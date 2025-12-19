"""
Example showing AGUI with state management - as simple as pydantic-ai's to_web()!
"""
from fasthtml.common import *
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps
from ag_ui.core.events import StateSnapshotEvent, EventType
from ft_agui import setup_agui
from typing import List
import uuid

class Term(BaseModel):
    term: str
    definition: str

    def __ft__(self):
        return Span(B(self.term), ":", self.definition)
    
class TermList(BaseModel):
    terms: List[Term]

    def __ft__(self):
        return Ul(*[Li(term) for term in self.terms])

# Define your state model
class Note(BaseModel):
    id: str
    title: str
    content: str|TermList

    def __ft__(self):
        # Add 'marked' class for markdown rendering when content is a string
        if isinstance(self.content, str):
            content_div = Div(self.content, cls="marked prose prose-sm")
        else:
            content_div = Div(self.content, cls="prose prose-sm")

        return Li(
            Card(
                content_div,
                header=H4(self.title)
            )
        )
class ChatState(BaseModel):
    notes: Dict[str, List[Note]] = Field(default_factory=dict, description="A dictionary of notes, grouped by category.")
    current_topic: str = "General Chat"

    def __ft__(self):
        """Custom rendering for the state"""
        return Card(
            Card(
                *[Div(H4(cat), Ul(*[Li(note) for note in notes])) for cat, notes in self.notes.items()],
                header=H3("Notes")
            ),
            header=H2(self.current_topic),
            id="agui-state"
        )


# Create agent with state dependencies
agent = Agent[StateDeps[ChatState]](
    'openai:gpt-4o-mini',
    instructions='You are a helpful assistant that can take notes. Use tools to manage notes. Keep an on topic name of th chat always',
    deps_type=StateDeps[ChatState]
)

@agent.tool
def list_categories(ctx: RunContext[StateDeps[ChatState]]) -> List[str]:
    """Get the categories of the notes so far."""
    return list(ctx.deps.state.notes.keys())

@agent.tool
def list_notes(ctx: RunContext[StateDeps[ChatState]], category: str) -> ToolReturn:
    """List all notes"""
    notes = ctx.deps.state.notes
    if not notes:
        return ToolReturn(return_value="No notes found")

    notes_text = "\n".join([f"- {n.content}" for n in notes[category]]) if category in notes else "No notes found in this category"
    return ToolReturn(
        return_value=f"Current notes:\n{notes_text}"
    )


@agent.tool
def add_note(ctx: RunContext[StateDeps[ChatState]], category: str, note: Note) -> ToolReturn:
    """Add a note to the chat state"""

    ctx.deps.state.notes.setdefault(category, []).append(note)
    return ToolReturn(
        return_value=f"Added note: {note.title}",
        metadata=[
            StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                snapshot=ctx.deps.state
            )
        ]
    )


@agent.tool
def set_topic(ctx: RunContext[StateDeps[ChatState]], topic: str) -> ToolReturn:
    """Set the current chat topic"""
    ctx.deps.state.current_topic = topic
    return ToolReturn(
        return_value=f"Topic set to: {topic}",
        metadata=[
            StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                snapshot=ctx.deps.state
            )
        ]
    )



# Create FastHTML app with WebSocket and MarkdownJS support
app, rt = fast_app(exts='ws', hdrs=[MarkdownJS()])

# Setup AGUI with state - just as easy!
agui = setup_agui(app, agent, ChatState(), ChatState)




@rt('/')
def index():
    """Chat interface with state display - clean and simple!"""
    thread_id = "1234"
    return Titled(
        "AGUI APP",
        Container(
            Grid(
                Div(
                    agui.state(thread_id)
                ),
                Div(
                    agui.chat(thread_id)
                )
            )
        )
    )


if __name__ == "__main__":
    serve()