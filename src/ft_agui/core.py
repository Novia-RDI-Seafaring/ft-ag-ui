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
from .styles import get_chat_styles
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
            "...running...",
            Div(
                id=f"run-trigger-{run_id}",
                hx_get=f'/agui/run/{self.thread_id}/{run_id}',
                hx_trigger='load',
                style="display: none;"
            ),
            id="chat-status",
            hx_swap_oob="innerHTML"
        )

    def _clear_input(self):
        """Replace the form with a cleared version"""
        return self._render_input_form(oob_swap=True)

    def _render_messages(self, messages: List[BaseMessage]):
        """Render chat messages"""
        return Div(
            *[m.__ft__() if hasattr(m, '__ft__') else self._render_message(m) for m in messages],
            id="chat-messages",
            cls="chat-messages"
        )

    def _render_message(self, message: BaseMessage):
        """Render a single message (fallback if no __ft__ method)"""
        message_class = "chat-user" if message.role == "user" else "chat-assistant"
        return Div(
            Div(message.content, cls="chat-message-content"),
            cls=f"chat-message {message_class}",
            id=message.id
        )

    def _render_input_form(self, oob_swap=False):
        """Render the input form"""
        form_attrs = {
            'id': 'chat-form',
            'ws_send': True,
        }

        container_attrs = {
            'cls': 'chat-input',
            'id': 'chat-input-container'
        }

        # Only add OOB swap when clearing after message send
        if oob_swap:
            container_attrs['hx_swap_oob'] = 'outerHTML'

        return Div(
            Div(id="suggestion-buttons"),  # Empty placeholder for suggestions
            Div(id="chat-status", cls="chat-status"),
            Form(
                Hidden(name='thread_id', value=self.thread_id),
                Textarea(
                    id='chat-input',
                    name='msg',
                    placeholder="Type a message...",
                    autofocus=True,
                    autocomplete="off",
                    cls="chat-input-field",
                    rows="1",
                    onkeydown="handleKeyDown(this, event)",
                    oninput="autoResize(this)"
                ),
                Button("Send", type="submit", cls="chat-input-button"),
                cls="chat-input-form",
                **form_attrs
            ),
            **container_attrs
        )


    def state_loader(self):
        return Div(hx_get=f'/agui/ui/{self.thread_id}/state', hx_trigger='load', hx_swap_oob="innerHTML")

    def chat_loader(self):
        return Div(hx_get=f'/agui/ui/{self.thread_id}/chat', hx_trigger='load', hx_swap_oob="innerHTML")



    def chat(self, **kwargs):

        components = []

        components.extend([
            get_chat_styles(),  # Include CSS
            MarkdownJS(), # Add markdown support
            Div(
                id="chat-messages",
                cls="chat-messages",
                hx_get=f'/agui/messages/{self.thread_id}',
                hx_trigger='load',
                hx_swap='outerHTML'
            ),
            self._render_input_form(),
        ])

        # Add auto-resize and enter submit script for textarea
        components.append(Script("""
            function autoResize(textarea) {
                textarea.style.height = 'auto';
                const maxHeight = 12 * 16; // 12rem in pixels (assuming 16px = 1rem)
                const newHeight = Math.min(textarea.scrollHeight, maxHeight);
                textarea.style.height = newHeight + 'px';

                // Show scrollbar if content exceeds max height
                if (textarea.scrollHeight > maxHeight) {
                    textarea.style.overflowY = 'auto';
                } else {
                    textarea.style.overflowY = 'hidden';
                }
            }

            function handleKeyDown(textarea, event) {
                autoResize(textarea);

                // Submit on Enter, but allow Shift+Enter for new lines
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    const form = textarea.closest('form');
                    if (form && textarea.value.trim()) {
                        form.requestSubmit();
                    }
                }
            }

            // Re-render markdown when content changes
            function renderMarkdown(elementId) {
                setTimeout(() => {
                    const element = document.getElementById(elementId);
                    if (element && window.marked && element.classList.contains('marked')) {
                        const content = element.textContent || element.innerText;
                        if (content) {
                            element.innerHTML = marked.parse(content);
                        }
                    }
                }, 10);
            }
        """))

        if self.autoscroll:
            components.append(Script("""
                // Auto-scroll to bottom on new messages
                (function() {
                    const observer = new MutationObserver(() => {
                        const messages = document.getElementById('chat-messages');
                        if (messages) {
                            messages.scrollTop = messages.scrollHeight;
                        }
                    });
                    const target = document.getElementById('chat-messages');
                    if (target) {
                        observer.observe(target, {childList: true, subtree: true});
                    }
                })();
            """))

        return Div(
            *components,
            hx_ext='ws',
            ws_connect=f'/agui/ws/{self.thread_id}',
            cls="chat-container",
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
        self.ui = UI[T](self.thread_id, autoscroll=False)
        self._suggestions: List[str] = []

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

    async def set_suggestions(self, suggestions: List[str]):
        """Set suggestion buttons and broadcast to all connected clients"""
        self._suggestions = suggestions[:4]  # Limit to 4 suggestions

        # Create suggestion buttons element
        if self._suggestions:
            suggestions_element = Div(
                *[
                    Button(
                        suggestion,
                        onclick=f"""
                            const textarea = document.getElementById('chat-input');
                            const form = document.getElementById('chat-form');
                            if (textarea && form) {{
                                textarea.value = {repr(suggestion)};
                                form.requestSubmit();
                            }}
                        """,
                        cls="suggestion-btn"
                    ) for suggestion in self._suggestions
                ],
                id="suggestion-buttons",
                hx_swap_oob="outerHTML"
            )
        else:
            # Empty suggestions
            suggestions_element = Div(id="suggestion-buttons", hx_swap_oob="outerHTML")

        await self.send(suggestions_element)

    def get_suggestions(self) -> List[str]:
        """Get current suggestions"""
        return self._suggestions.copy()

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
        await self.send(
            Div(
                Div(Span(cls="loading"), id="run-start"),
                id="agui-messages", hx_swap_oob="beforeend"))
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
            elif event.type == EventType.TEXT_MESSAGE_CONTENT:
                response.content += event.delta
            elif event.type == EventType.RUN_FINISHED:
                self._messages.append(response)
                # Replace the entire message div with properly rendered markdown
                content_id = f"content-{response.id}"
                await self.send(
                    Div(
                        Div(response.content, cls="chat-message-content marked", id=content_id),
                        cls="chat-message chat-assistant",
                        id=f"message-{response.id}",
                        hx_swap_oob="outerHTML"
                    )
                )
                # Trigger markdown rendering
                await self.send(Script(f"renderMarkdown('{content_id}');"))
                # Clear the status when run completes
                await self.send(Div(id="chat-status", hx_swap_oob="innerHTML"))
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

        @self.app.route('/agui/messages/{thread_id}')
        def get_messages(thread_id: str):
            """Load existing messages for a thread"""
            thread = self.thread(thread_id)
            if thread._messages:
                return thread.ui._render_messages(thread._messages)
            return Div(id="chat-messages", cls="chat-messages")

    def thread(self, thread_id: str) -> AGUIThread[T]:
        self._threads.setdefault(thread_id, AGUIThread[T](thread_id=thread_id, state=self._state, agent=self.agent))
        return self._threads[thread_id]

    def _on_conn(self, ws, send, session):  self.thread(session["thread_id"]).subscribe(str(id(ws)), send)
    def _on_disconn(self, ws, session): self.thread(session["thread_id"]).unsubscribe(str(id(ws)))


    def state(self, thread_id):
        return self.thread(thread_id).ui.state_loader()

    def chat(self, thread_id):
        return self.thread(thread_id).ui.chat_loader()

    async def set_suggestions(self, thread_id: str, suggestions: List[str]):
        """Set suggestions for a specific thread"""
        await self.thread(thread_id).set_suggestions(suggestions)

    def get_suggestions(self, thread_id: str) -> List[str]:
        """Get current suggestions for a thread"""
        return self.thread(thread_id).get_suggestions()



def setup_agui(app, agent: Agent, initial_state: T, state_type: type[T], tools: Optional[List[Tool]] = [],
            forwarded_props: Any = {},
            context: List[Context] = []) -> AGUISetup[T]:
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
    return AGUISetup[T](app, agent, state, tools, forwarded_props, context)