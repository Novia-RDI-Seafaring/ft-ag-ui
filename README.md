# ft-agui

Easy AGUI (Agent GUI) integration for FastHTML applications. Build real-time chat interfaces with AI agents as simple as `pydantic-ai`'s `to_web()` but with full control and flexibility for FastHTML.

## Features

- **Simple Setup** - One line to integrate: `agui = setup_agui(app, agent, state)`
- **Real-time Chat** - WebSocket-based communication with streaming responses
- **Customizable UI** - FastHTML components with beautiful default styles
- **State Management** - Thread-safe state with automatic UI updates
- **AGUI Protocol** - Full compatibility with pydantic-ai's AGUI protocol
- **Multi-threading** - Support for multiple conversation threads

## Installation

```bash
pip install ft-agui
```

## Quick Start

```python
from fasthtml.common import *
from pydantic_ai import Agent
from ft_agui import setup_agui

# Create FastHTML app with WebSocket support
app, rt = fast_app(exts='ws')

# Create your agent
agent = Agent('openai:gpt-4o-mini', instructions='Be helpful and friendly')

# Setup AGUI with one line!
agui = setup_agui(app, agent)

@rt('/')
def index():
    return Titled(
        "My AI Chat",
        Container(
            agui.chat("my-thread")
        )
    )

serve()
```

## Advanced Usage with State Management

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps
from ft_agui import setup_agui
from typing import List

# Define your state model
class Note(BaseModel):
    title: str
    content: str

class ChatState(BaseModel):
    notes: List[Note] = Field(default_factory=list)
    topic: str = "General"

    def __ft__(self):
        """Custom FastHTML rendering"""
        return Card(
            H3(f"Topic: {self.topic}"),
            Ul(*[Li(f"{n.title}: {n.content}") for n in self.notes]),
            header="Session State"
        )

# Create agent with state
agent = Agent[StateDeps[ChatState]](
    'openai:gpt-4o-mini',
    instructions='You can take notes and manage topics.',
    deps_type=StateDeps[ChatState]
)

# Add tools for state management
@agent.tool
def add_note(ctx: RunContext[StateDeps[ChatState]], title: str, content: str) -> ToolReturn:
    ctx.deps.state.notes.append(Note(title=title, content=content))
    return ToolReturn(return_value=f"Added note: {title}")

# Setup AGUI with state
app, rt = fast_app(exts='ws')
agui = setup_agui(app, agent, ChatState(), ChatState)

@rt('/')
def index():
    thread_id = "main-thread"
    return Container(
        Grid(
            Div(agui.state(thread_id)),      # State display
            Div(agui.chat(thread_id, autoscroll=True))  # Chat interface
        )
    )
```

## Thread Management

ft-agui provides flexible thread management for handling multiple conversations:

### Option 1: Explicit Thread IDs
```python
# Pass thread_id directly
agui.state(thread_id="user-123")
agui.chat(thread_id="user-123", autoscroll=True)
```

### Option 2: Thread Instances (Recommended)
```python
# Create a thread instance
thread = agui.thread("user-123")
return Container(
    Grid(
        Div(thread.state()),
        Div(thread.chat(autoscroll=True))
    )
)
```

### Option 3: Multiple Threads
```python
# Manage multiple conversations
thread1 = agui.thread("support-chat")
thread2 = agui.thread("sales-chat")

return Container(
    Div(thread1.chat()),
    Div(thread2.chat())
)
```

## Custom State Rendering

Define custom `__ft__()` methods on your Pydantic models for rich UI rendering:

```python
class TodoItem(BaseModel):
    task: str
    done: bool = False

    def __ft__(self):
        return Li(
            Input(type="checkbox", checked=self.done),
            Span(self.task, style="text-decoration: line-through;" if self.done else "")
        )

class TodoList(BaseModel):
    items: List[TodoItem] = []

    def __ft__(self):
        return Card(
            Ul(*[item.__ft__() for item in self.items]),
            header="My Todos"
        )
```

## API Reference

### `setup_agui(app, agent, initial_state=None, state_type=None)`

Initialize AGUI for your FastHTML application.

**Parameters:**
- `app`: FastHTML application (must have `exts='ws'` enabled)
- `agent`: pydantic-ai Agent instance
- `initial_state`: Initial state instance (optional)
- `state_type`: State type class for validation (optional)

**Returns:** `AGUISetup` instance

### `AGUISetup.chat(thread_id, autoscroll=False, **kwargs)`

Create a chat interface component.

**Parameters:**
- `thread_id`: Thread identifier
- `autoscroll`: Auto-scroll to bottom on new messages
- `**kwargs`: Additional HTML attributes

### `AGUISetup.state(thread_id, **kwargs)`

Create a state display component.

**Parameters:**
- `thread_id`: Thread identifier
- `**kwargs`: Additional HTML attributes

### `AGUISetup.thread(thread_id)`

Create a thread instance for cleaner component management.

**Parameters:**
- `thread_id`: Thread identifier (auto-generated if None)

**Returns:** `AGUIThread` instance with `chat()` and `state()` methods

## Requirements

- Python 3.11+
- FastHTML with WebSocket support
- pydantic-ai
- ag-ui (AGUI protocol)

## Examples

Check out the `/example` directory for complete examples:

- `simple_agui.py` - Basic chat interface
- `agui_with_state.py` - State management with tools
- `thread_management.py` - Multi-thread handling

## License

MIT

## Credits

Built using [FastHTML](https://fasthtml.dev) and currently supporting [pydantic-ai](https://ai.pydantic.dev)
