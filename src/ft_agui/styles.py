"""Modern chat UI styles using CSS custom properties for easy theming"""

# Standard chat UI CSS using custom properties - follows common patterns from
# Discord, Slack, ChatGPT, etc. Most chat UIs use these same semantic patterns:
# .chat-container, .chat-message, .chat-user/.chat-assistant, .chat-input

CHAT_UI_STYLES = """
/* === Chat UI CSS Custom Properties (Variables) === */
:root {
  /* Color Palette */
  --chat-bg: #f8fafc;
  --chat-surface: #ffffff;
  --chat-border: #e2e8f0;
  --chat-text: #1e293b;
  --chat-text-muted: #64748b;
  --chat-primary: #3b82f6;
  --chat-primary-hover: #2563eb;
  --chat-user-bg: #3b82f6;
  --chat-user-text: #ffffff;
  --chat-assistant-bg: #f1f5f9;
  --chat-assistant-text: #1e293b;

  /* Spacing */
  --chat-padding: 1rem;
  --chat-gap: 0.75rem;
  --chat-message-padding: 0.75rem 1rem;
  --chat-border-radius: 0.75rem;
  --chat-message-radius: 1.125rem;

  /* Typography */
  --chat-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --chat-font-size: 0.875rem;
  --chat-line-height: 1.5;

  /* Transitions */
  --chat-transition: all 0.2s ease;

  /* Shadows */
  --chat-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  --chat-shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Dark theme support */
@media (prefers-color-scheme: dark) {
  :root {
    --chat-bg: #0f172a;
    --chat-surface: #1e293b;
    --chat-border: #334155;
    --chat-text: #f1f5f9;
    --chat-text-muted: #94a3b8;
    --chat-assistant-bg: #334155;
    --chat-assistant-text: #f1f5f9;
  }
}

/* === Chat Layout === */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 400px;
  background: var(--chat-bg);
  font-family: var(--chat-font-family);
  border-radius: var(--chat-border-radius);
  overflow: hidden;
  border: 1px solid var(--chat-border);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--chat-padding);
  background: var(--chat-surface);
  display: flex;
  flex-direction: column;
  gap: var(--chat-gap);
}

.chat-messages:empty::before {
  content: "Start a conversation...";
  color: var(--chat-text-muted);
  text-align: center;
  padding: 2rem;
  font-style: italic;
}

/* === Message Styles === */
.chat-message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  animation: chat-message-in 0.3s ease-out;
}

/* Markdown styles for chat messages */
.chat-message-content p {
  margin: 0 0 0.5rem 0;
}

.chat-message-content p:last-child {
  margin-bottom: 0;
}

.chat-message-content ul,
.chat-message-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.chat-message-content li {
  margin: 0.25rem 0;
}

.chat-message-content code {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: 'Courier New', Courier, monospace;
}

.chat-assistant .chat-message-content code {
  background: rgba(0, 0, 0, 0.05);
}

.chat-message-content pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.75rem 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.chat-message-content pre code {
  background: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
}

/* Dark theme code blocks */
@media (prefers-color-scheme: dark) {
  .chat-message-content pre {
    background: #0f172a;
    border: 1px solid var(--chat-border);
  }
}

.chat-message-content blockquote {
  border-left: 3px solid var(--chat-border);
  padding-left: 1rem;
  margin: 0.5rem 0;
  color: var(--chat-text-muted);
}

.chat-message-content h1,
.chat-message-content h2,
.chat-message-content h3,
.chat-message-content h4 {
  margin: 0.75rem 0 0.5rem 0;
  font-weight: 600;
}

.chat-message-content h1 { font-size: 1.25rem; }
.chat-message-content h2 { font-size: 1.125rem; }
.chat-message-content h3 { font-size: 1rem; }
.chat-message-content h4 { font-size: 0.875rem; }

.chat-message-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5rem 0;
}

.chat-message-content th,
.chat-message-content td {
  border: 1px solid var(--chat-border);
  padding: 0.5rem;
  text-align: left;
}

.chat-message-content th {
  background: rgba(0, 0, 0, 0.05);
  font-weight: 600;
}

@keyframes chat-message-in {
  from {
    opacity: 0;
    transform: translateY(0.5rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-user {
  align-self: flex-end;
}

.chat-assistant {
  align-self: flex-start;
}

.chat-message-content {
  padding: var(--chat-message-padding);
  border-radius: var(--chat-message-radius);
  font-size: var(--chat-font-size);
  line-height: var(--chat-line-height);
  word-wrap: break-word;
  position: relative;
}

.chat-user .chat-message-content {
  background: var(--chat-user-bg);
  color: var(--chat-user-text);
  border-bottom-right-radius: 0.375rem;
}

.chat-assistant .chat-message-content {
  background: var(--chat-assistant-bg);
  color: var(--chat-assistant-text);
  border-bottom-left-radius: 0.375rem;
}

.chat-message-role {
  font-size: 0.75rem;
  color: var(--chat-text-muted);
  margin-bottom: 0.25rem;
  padding: 0 0.5rem;
}

/* Streaming indicator */
.chat-streaming::after {
  content: '▊';
  animation: chat-blink 1s infinite;
  opacity: 0.7;
}

@keyframes chat-blink {
  0%, 50% { opacity: 0.7; }
  51%, 100% { opacity: 0; }
}

/* === Input Form === */
.chat-input {
  padding: var(--chat-padding);
  background: var(--chat-surface);
  border-top: 1px solid var(--chat-border);
}

.chat-status {
  min-height: 1.5rem;
  padding: 0.5rem 0;
  color: var(--chat-text-muted);
  font-size: 0.875rem;
  text-align: center;
}

/* === Suggestion Buttons === */
#suggestion-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
}

.suggestion-btn {
  padding: 0.5rem 1rem;
  background: var(--chat-surface);
  border: 1px solid var(--chat-border);
  border-radius: 1rem;
  color: var(--chat-primary);
  font-size: 0.875rem;
  font-family: var(--chat-font-family);
  cursor: pointer;
  transition: var(--chat-transition);
  white-space: nowrap;
}

.suggestion-btn:hover {
  background: var(--chat-primary);
  color: white;
  transform: translateY(-1px);
  box-shadow: var(--chat-shadow-lg);
}

.chat-input-form {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  align-items: end;
  width: 100%;
}

.chat-input-field {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 1px solid var(--chat-border);
  border-radius: var(--chat-border-radius);
  background: var(--chat-bg);
  color: var(--chat-text);
  font-family: var(--chat-font-family);
  font-size: 1rem;
  line-height: 1.5;
  resize: none;
  min-height: 3.5rem;
  max-height: 12rem;
  transition: var(--chat-transition);
  overflow-y: hidden;
  box-sizing: border-box;
}

.chat-input-field:focus {
  outline: none;
  border-color: var(--chat-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.chat-input-button {
  padding: 0.75rem 1.5rem;
  background: var(--chat-primary);
  color: white;
  border: none;
  border-radius: var(--chat-border-radius);
  font-family: var(--chat-font-family);
  font-size: var(--chat-font-size);
  font-weight: 500;
  cursor: pointer;
  transition: var(--chat-transition);
  min-height: 3.5rem;
  justify-self: end;
}

.chat-input-button:hover {
  background: var(--chat-primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--chat-shadow-lg);
}

.chat-input-button:active {
  transform: translateY(0);
}

/* === State Sidebar === */
.chat-state-container {
  background: var(--chat-surface);
  border: 1px solid var(--chat-border);
  border-radius: var(--chat-border-radius);
  padding: var(--chat-padding);
  height: fit-content;
}

.chat-state-title {
  font-weight: 600;
  color: var(--chat-text);
  margin-bottom: var(--chat-gap);
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--chat-border);
}

/* === Tool/System Messages === */
.chat-tool {
  align-self: center;
  max-width: 60%;
}

.chat-tool .chat-message-content {
  background: var(--chat-border);
  color: var(--chat-text-muted);
  font-size: 0.8rem;
  text-align: center;
  border-radius: var(--chat-border-radius);
}

/* === Layout Utilities === */
.chat-layout {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--chat-padding);
  height: 100vh;
  padding: var(--chat-padding);
  background: var(--chat-bg);
}

.chat-layout-sidebar {
  overflow-y: auto;
}

.chat-layout-main {
  display: flex;
  flex-direction: column;
}

/* === Responsive === */
@media (max-width: 768px) {
  .chat-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .chat-message {
    max-width: 90%;
  }
}

/* === Error States === */
.chat-error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.chat-error .chat-message-content {
  background: #fef2f2;
  color: #dc2626;
}
"""


def get_chat_styles():
    """Get modern chat UI styles as a Style component"""
    from fasthtml.common import Style
    return Style(CHAT_UI_STYLES)


def get_custom_theme(**theme_vars):
    """Generate custom theme CSS variables

    Example:
        get_custom_theme(
            chat_primary="#10b981",
            chat_user_bg="#10b981",
            chat_assistant_bg="#f3f4f6"
        )
    """
    from fasthtml.common import Style

    css_vars = []
    for key, value in theme_vars.items():
        css_var = f"--{key.replace('_', '-')}: {value};"
        css_vars.append(css_var)

    theme_css = f"""
    :root {{
        {' '.join(css_vars)}
    }}
    """

    return Style(theme_css)