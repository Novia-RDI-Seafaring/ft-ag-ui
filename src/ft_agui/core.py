from typing import Dict, List, Optional, Any, TypeVar
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter
from pydantic_ai.ui import StateDeps
from ag_ui.core.types import (
    RunAgentInput,
    Tool,
    BaseMessage,
    UserMessage,
    AssistantMessage,
    Context,
)
from ag_ui.core.events import (
    BaseEvent,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    TextMessageStartEvent,
    TextMessageChunkEvent,
    StateSnapshotEvent,
)
from fasthtml.common import *
from fasthtml.core import *
import uuid
import asyncio
from .patches import setup_ft_patches
from typing import Generic, Callable
from collections import defaultdict

T = TypeVar('T', bound=BaseModel)

class UI(Generic[T]):
    def __init__(self, thread_id: str, autoscroll: bool = False):
        self.thread_id = thread_id
        self.autoscroll = autoscroll
        
    def _trigger_run(self, run_id: str):
        print("sending trigger run", self.thread_id, run_id)
        """Create element to trigger agent run"""
        return Div(
            Div("...running...", id=f"run-{run_id}",
                hx_get=f'/agui/run/{self.thread_id}/{run_id}',
                hx_trigger='load',
            ),
            id="agui-run",
            hx_swap_oob="beforeend"
        )

    def _clear_input(self):
        """Clear the input field after sending"""
        return Script("document.getElementById('agui-input').value = '';")

    def _render_messages(self, messages: List[BaseMessage]):
        """Render chat messages"""
        return Ul(
            *[m.__ft__() if hasattr(m, '__ft__') else self._render_message(m) for m in messages],
            id="agui-messages",
            cls="agui-message-list"
        )

    def _render_message(self, message: BaseMessage):
        """Render a single message (fallback if no __ft__ method)"""
        return Li(
            Div(f"{message.role.title()}: ", cls="agui-message-role"),
            Div(message.content, cls="agui-message-content"),
            cls=f"agui-message agui-{message.role}",
            id=message.id
        )

    def _render_input_form(self):
        """Render the input form"""
        return Form(
            Hidden(name='thread_id', value=self.thread_id),
            Input(
                id='agui-input',
                name='msg',
                placeholder="Type a message...",
                autofocus=True,
                autocomplete="off"
            ),
            Button("Send", type="submit"),
            id='agui-form',
            ws_send=True,
            cls="agui-input-form"
        )


    def state_loader(self):
        return Div(hx_get=f'/agui/ui/{self.thread_id}/state', hx_trigger='load', hx_swap_oob="innerHTML")

    def chat_loader(self):
        return Div(hx_get=f'/agui/ui/{self.thread_id}/chat', hx_trigger='load', hx_swap_oob="innerHTML")



    def chat(self, **kwargs):

        components = []

        components.extend([
            Div(id="agui-messages", cls="agui-message-list"),
            Div(id="agui-stream"),
            Div(id="agui-run"),
            self._render_input_form(),
        ])

        if self.autoscroll:
            components.append(Script("""
                // Auto-scroll to bottom on new messages
                (function() {
                    const observer = new MutationObserver(() => {
                        const messages = document.getElementById('agui-messages');
                        if (messages) {
                            messages.scrollTop = messages.scrollHeight;
                        }
                    });
                    const target = document.getElementById('agui-messages');
                    if (target) {
                        observer.observe(target, {childList: true, subtree: true});
                    }
                })();
            """))

        return Div(
            *components,
            hx_ext='ws',
            ws_connect=f'/agui/ws/{self.thread_id}',
            cls="agui-chat-container",
            **kwargs
        )

class AGUIThread(Generic[T]):
    """Represents a single AGUI thread/conversation"""

    def __init__(self, thread_id: str, state: T, agent: Agent):
        self.thread_id = thread_id
        self._state = state
        self._runs = {}
        self._agent = agent
        self._messages: List[BaseMessage] = []
        self._connections = {}
        self.ui = UI[T](self.thread_id)

    def subscribe(self, connection_id,  send):
        print("subscribing", connection_id)
        self._connections[connection_id] = send

    def unsubscribe(self, connection_id: str):
        print("unsubscribing", connection_id)
        self._connections.pop(connection_id, None)

    async def send(self, element:FT):
        """Broadcast element to all connected clients in a thread"""
        for connection_id, send in self._connections.items():
            await send(element)

    async def _handle_message(self, msg: str, session):
        """Handle incoming WebSocket message"""
        run_id = str(uuid.uuid4())
        message = UserMessage(
            id=str(uuid.uuid4()),
            role='user',
            content=msg,
            name=session.get("username", "User")
        )

        self._messages.append(message)

        run_input = RunAgentInput(
            thread_id=self.thread_id,
            run_id=run_id,
            messages=self._messages,
            state=self._state,
            tools=[],
            forwarded_props=[],
            context=[],

        )

        self._runs[run_id] = run_input

        # Trigger the run
        await self.send(self.ui._render_messages(self._messages))
        await self.send(self.ui._trigger_run(run_id))
        await self.send(self.ui._clear_input())

    async def _handle_run(self, run_id: str):
        """Handle agent run execution"""
        if run_id not in self._runs: return Div("Run not found")

        run_input = self._runs[run_id]
        state = self._state

        adapter = AGUIAdapter(self._agent, run_input=run_input)
        response = AssistantMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content="",
            name=self._agent.name or "Assistant"
        )

        deps = StateDeps[T](state=state)

        async for event in adapter.run_stream(
            message_history=self._messages or [],
            deps=deps
        ):
            # Use the __ft__ method from patches if available
            if hasattr(event, '__ft__'):
                await self.send(event.__ft__())

            if event.type == EventType.TEXT_MESSAGE_START:
                response.id = event.message_id
            elif event.type == EventType.TEXT_MESSAGE_CHUNK:
                response.content += event.delta
            elif event.type == EventType.RUN_FINISHED:
                self._messages.append(response)
            elif event.type == EventType.STATE_SNAPSHOT:
                self._state = event.snapshot

        return Div()




class AGUISetup(Generic[T]):
    """Main class for setting up AGUI in a FastHTML application"""

    def __init__(self, 
            app,
            agent: Agent,
            state: T,
            tools: Optional[List[Tool]] = [],
            forwarded_props: Any = {},
            context: List[Context] = []):
        self.app = app
        self.agent = agent
        self._state: T = state
        self.tools = tools
        self.forwarded_props = forwarded_props
        self.context = context
        # Setup FT patches for ag_ui types
        self._threads: Dict[str, AGUIThread[T]] = {}
        setup_ft_patches()

        # Setup WebSocket routes
        self._setup_routes()

    def add_context(self, context: Context):
        self.context.append(context)

    def _setup_routes(self):
        """Setup the necessary routes for AGUI"""

        @self.app.get('/agui/ui/{thread_id}/chat')
        async def ui_handler(thread_id: str, session):
            session["thread_id"] = thread_id
            return self.thread(thread_id).ui.chat()

        @self.app.get('/agui/ui/{thread_id}/state')
        async def ui_handler(thread_id: str, session):
            return self.thread(thread_id)._state.__ft__()        

        @self.app.ws('/agui/ws/{thread_id}', conn=self._on_conn, disconn=self._on_disconn)
        async def ws_handler(thread_id: str, msg: str, session):
            await self._threads[thread_id]._handle_message(msg, session)

        @self.app.route('/agui/run/{thread_id}/{run_id}')
        async def run_handler(thread_id: str, run_id: str):
            return await self._threads[thread_id]._handle_run(run_id)

    def thread(self, thread_id: str) -> AGUIThread[T]:
        self._threads.setdefault(thread_id, AGUIThread[T](thread_id=thread_id, state=self._state, agent=self.agent))
        return self._threads[thread_id]

    def _on_conn(self, ws, send, session):  self.thread(session["thread_id"]).subscribe(str(id(ws)), send)
    def _on_disconn(self, ws, session): self.thread(session["thread_id"]).unsubscribe(str(id(ws)))


    def state(self, thread_id):
        return self.thread(thread_id).ui.state_loader()

    def chat(self, thread_id):
        return self.thread(thread_id).ui.chat_loader()



def setup_agui(app, agent: Agent, initial_state: T, state_type: type[T]) -> AGUISetup[T]:
    """
    Setup AGUI for a FastHTML application

    Args:
        app: FastHTML application instance (must have 'ws' extension enabled)
        agent: pydantic-ai Agent instance
        initial_state: Initial state of the AGUI
        state_type: Pydantic model for managing state

    Returns:
        AGUISetup instance with chat() and state() methods

    Usage:
        from pydantic_ai import Agent
        from ft_event_sender import setup_agui

        app, rt = fast_app(exts='ws')  # Important: Enable WebSocket extension
        agent = Agent('openai:gpt-4')
        agui = setup_agui(app, agent)

        # In your route:
        return agui.chat()
    """
    json = initial_state.model_dump_json()
    state = state_type.model_validate_json(json)
    return AGUISetup[T](app, agent, state)