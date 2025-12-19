"""
ft-agui: Easy AGUI integration for FastHTML applications
"""
from .core import setup_agui, AGUISetup, AGUIThread
from .styles import get_chat_styles, get_custom_theme
from .layouts import (
    chat_with_sidebar,
    simple_chat,
    mobile_friendly_chat,
    custom_themed_chat,
    discord_style_layout,
    slack_style_layout,
)

__version__ = "0.1.0"

__all__ = [
    "setup_agui",
    "AGUISetup",
    "AGUIThread",
    "get_chat_styles",
    "get_custom_theme",
    "chat_with_sidebar",
    "simple_chat",
    "mobile_friendly_chat",
    "custom_themed_chat",
    "discord_style_layout",
    "slack_style_layout",
]