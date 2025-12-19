"""
Example showing AGUI with suggestion buttons using the built-in suggestions feature!
"""
from fasthtml.common import *
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps
from ag_ui.core.events import StateSnapshotEvent, EventType, CustomEvent
from ft_agui import setup_agui
from typing import List
import uuid
import asyncio


class UserState(BaseModel):
    current_topic: str = "General Chat"

    def __ft__(self):
        return Div(
            "Current Topic: " + self.current_topic,
            cls="text-lg font-bold text-gray-900 mb-4 px-1"
        )
# Global reference to agui for the tool
agui_instance = None

# Create agent with state dependencies
agent = Agent[StateDeps[UserState]](
    'openai:gpt-4o-mini',
    instructions='You are a helpful assistant. Before returning the final answer, anticipate what the user might ask next using the anticipate_questions tool. Keep suggestions short as they will be rendered as buttons.',
    deps_type=StateDeps[UserState]
)

@agent.tool
async def anticipate_questions(ctx: RunContext[StateDeps[UserState]], questions: List[str]) -> ToolReturn:
    """Set suggestion buttons for the current chat"""
    global agui_instance
    if agui_instance:
        # Get thread_id from context - for simplicity using "1234"
        await agui_instance.set_suggestions("1234", questions[:4])

    return ToolReturn(
        return_value=f"Set {len(questions)} suggested questions"
    )



# Create FastHTML app with WebSocket and MarkdownJS support
app, rt = fast_app(exts='ws', hdrs=[MarkdownJS()])

# Setup AGUI with state - just as easy!
agui = setup_agui(app, agent, UserState(), UserState)
agui_instance = agui  # Set global reference




@rt('/')
async def index():
    """Chat interface with suggestion buttons"""
    thread_id = "1234"

    # Set initial suggestions
    await agui.set_suggestions(thread_id, [
        "What can you help me with?",
        "Tell me a joke",
        "Explain quantum computing",
        "What's the weather like?"
    ])

    return Titled(
        "AGUI with Smart Suggestions",
        Container(
            Grid(
                Div(
                    agui.state(thread_id),
                    cls="w-80 bg-gray-50 border-r border-gray-200 p-6"
                ),
                Div(
                    agui.chat(thread_id),
                    cls="flex-1"
                ),
                cls="grid-cols-[300px_1fr] h-screen"
            )
        )
    )


if __name__ == "__main__":
    serve()