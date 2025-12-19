"""
Patches to add FastHTML rendering (__ft__) methods to ag_ui protocol types
"""
from fasthtml.common import *
from ag_ui.core.types import BaseMessage
from ag_ui.core.events import (
        TextMessageStartEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        TextMessageChunkEvent,
        ToolCallStartEvent,
        ToolCallArgsEvent,
        ToolCallEndEvent,
        ToolCallChunkEvent,
        ToolCallResultEvent,
        StateSnapshotEvent,
        StateDeltaEvent,
        MessagesSnapshotEvent,
        ActivitySnapshotEvent,
        ActivityDeltaEvent,
        RawEvent,
        CustomEvent,
        RunStartedEvent,
        RunFinishedEvent,
        RunErrorEvent,
        StepStartedEvent,
        StepFinishedEvent,
)


def setup_ft_patches():
    """Setup FastHTML rendering patches for ag_ui types"""

    # Patch BaseMessage
    @patch
    def __ft__(self: BaseMessage):
        message_class = "chat-user" if self.role == "user" else "chat-assistant"
        return Div(
            Div(self.content, cls="chat-message-content marked"),
            cls=f"chat-message {message_class}",
            id=self.id
        )

    # Patch RunStartedEvent
    @patch
    def __ft__(self: RunStartedEvent):
        return Div(
            Div(id=f"run-{self.run_id}"),
            id="agui-messages",
            hx_swap_oob="beforeend"
        )

    # Patch TextMessageStartEvent
    @patch
    def __ft__(self: TextMessageStartEvent):
        return Div(
            Div(
                Div(Span("", id=f"message-content-{self.message_id}", cls="marked"),Span("",cls="chat-streaming", id=f"streaming-{self.message_id}"), cls="chat-message-content"),
                cls="chat-message chat-assistant",
                id=f"message-{self.message_id}"
            ),
            id="chat-messages",
            hx_swap_oob="beforeend"
        )

    # Patch TextMessageChunkEvent
    @patch
    def __ft__(self: TextMessageChunkEvent):
        return Span(
            self.delta,
            id=f"message-content-{self.message_id}",
            hx_swap_oob="beforeend"
        )

    # Patch TextMessageContentEvent
    @patch
    def __ft__(self: TextMessageContentEvent):
        return Span(
            self.delta,
            id=f"message-content-{self.message_id}",
            hx_swap_oob="beforeend"
        )
    
    @patch
    def __ft__(self:TextMessageEndEvent):
        return Span("", id=f"streaming-{self.message_id}")

    # Patch StateSnapshotEvent
    @patch
    def __ft__(self: StateSnapshotEvent):
        if hasattr(self.snapshot, '__ft__'):
            return self.snapshot.__ft__()
        return Div(
            Pre(str(self.snapshot)),
            id="agui-state",
            hx_swap_oob="innerHTML"
        )

    # Patch ToolCallStartEvent
    @patch
    def __ft__(self: ToolCallStartEvent):
        return Div(
            Div(
                Div(f"🔧 {self.tool_call_name}...", cls="chat-message-content"),
                cls="chat-message chat-tool",
                id=f"tool-{self.tool_call_id}"
            ),
            id="chat-messages",
            hx_swap_oob="beforeend"
        )

    # Patch ToolCallEndEvent
    @patch
    def __ft__(self: ToolCallEndEvent):
        return Span(
            f"✅",
            id=f"tool-call-status-{self.tool_call_id}",
            hx_swap_oob="outerHTML",
            cls="agui-tool-result"
        )

    # Patch ErrorEvent
    @patch
    def __ft__(self: RunErrorEvent):
        return Div(
            Div("⚠️ Error:", cls="agui-error-title"),
            Div(self.type, cls="agui-error-message"),
            Div(self.message, cls="agui-error-details") if getattr(self, 'details', None) else "",
            cls="agui-error",
            role="alert",
            id="agui-messages",
            hx_swap_oob="beforeend"
        )