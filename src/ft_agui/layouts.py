"""Pre-built layout components for common chat UI patterns"""

from fasthtml.common import *
from .styles import get_chat_styles, get_custom_theme


def chat_with_sidebar(chat_component, sidebar_component, **kwargs):
    """
    Standard chat layout with sidebar (like pydantic-ai)

    Args:
        chat_component: The chat component (typically agui.chat())
        sidebar_component: The sidebar component (typically agui.state())
        **kwargs: Additional attributes for the container
    """
    return Div(
        get_chat_styles(),
        Div(
            # Sidebar
            Div(
                sidebar_component,
                cls="chat-layout-sidebar"
            ),
            # Main chat area
            Div(
                chat_component,
                cls="chat-layout-main"
            ),
            cls="chat-layout"
        ),
        **kwargs
    )


def simple_chat(chat_component, **kwargs):
    """Simple full-width chat layout"""
    return Div(
        get_chat_styles(),
        Div(
            chat_component,
            style="height: 100vh; padding: 1rem;"
        ),
        **kwargs
    )


def mobile_friendly_chat(chat_component, sidebar_component, **kwargs):
    """Mobile-responsive layout that stacks on small screens"""
    return Div(
        get_chat_styles(),
        Style("""
        @media (max-width: 768px) {
            .chat-layout {
                grid-template-columns: 1fr !important;
                grid-template-rows: auto 1fr !important;
            }
        }
        """),
        Div(
            Div(sidebar_component, cls="chat-layout-sidebar"),
            Div(chat_component, cls="chat-layout-main"),
            cls="chat-layout"
        ),
        **kwargs
    )


def custom_themed_chat(chat_component, sidebar_component=None, theme=None, **kwargs):
    """
    Chat layout with custom theme

    Args:
        theme: Dict of theme variables, e.g.:
            {
                "chat_primary": "#10b981",
                "chat_user_bg": "#10b981",
                "chat_assistant_bg": "#f3f4f6"
            }
    """
    components = [get_chat_styles()]

    if theme:
        components.append(get_custom_theme(**theme))

    if sidebar_component:
        layout = Div(
            Div(sidebar_component, cls="chat-layout-sidebar"),
            Div(chat_component, cls="chat-layout-main"),
            cls="chat-layout"
        )
    else:
        layout = Div(
            chat_component,
            style="height: 100vh; padding: 1rem;"
        )

    components.append(layout)

    return Div(*components, **kwargs)


def discord_style_layout(chat_component, sidebar_component, **kwargs):
    """Discord-style dark layout"""
    discord_theme = {
        "chat_bg": "#36393f",
        "chat_surface": "#40444b",
        "chat_border": "#202225",
        "chat_text": "#dcddde",
        "chat_text_muted": "#72767d",
        "chat_primary": "#5865f2",
        "chat_user_bg": "#5865f2",
        "chat_assistant_bg": "#2f3136"
    }

    return custom_themed_chat(
        chat_component,
        sidebar_component,
        theme=discord_theme,
        **kwargs
    )


def slack_style_layout(chat_component, sidebar_component, **kwargs):
    """Slack-style layout"""
    slack_theme = {
        "chat_bg": "#f8f8f8",
        "chat_surface": "#ffffff",
        "chat_border": "#e8e8e8",
        "chat_primary": "#1264a3",
        "chat_user_bg": "#1264a3",
        "chat_assistant_bg": "#f8f8f8"
    }

    return custom_themed_chat(
        chat_component,
        sidebar_component,
        theme=slack_theme,
        **kwargs
    )