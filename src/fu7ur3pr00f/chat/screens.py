"""Textual screens and modal dialogs for fu7ur3pr00f."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Input, Label, Markdown, Static

from fu7ur3pr00f.container import container


class ConfirmDialog(ModalScreen[bool]):
    """HITL confirmation dialog — returns True (YES) or False (NO)."""

    BINDINGS = [
        Binding("y", "confirm_yes", "Yes"),
        Binding("n", "confirm_no", "No"),
        Binding("escape", "confirm_no", "Cancel"),
    ]

    def __init__(self, question: str, details: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._question = question
        self._details = details

    def compose(self) -> ComposeResult:
        with Vertical(classes="confirm-dialog"):
            yield Label(self._question, classes="confirm-question")
            if self._details:
                yield Label(self._details, classes="confirm-details")
            with Horizontal(classes="confirm-buttons"):
                yield Button("Yes [Y]", id="btn-yes", variant="success")
                yield Button("No [N]", id="btn-no", variant="error")

    def on_mount(self) -> None:
        from fu7ur3pr00f.chat.widgets import _animations_enabled

        if _animations_enabled():
            self.styles.opacity = 0.0
            self.animate("opacity", 1.0, duration=0.2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")

    def action_confirm_yes(self) -> None:
        self.dismiss(True)

    def action_confirm_no(self) -> None:
        self.dismiss(False)


class HelpScreen(ModalScreen):
    """Help screen with command reference."""

    BINDINGS = [Binding("escape,q", "dismiss", "Close")]

    _HELP_TEXT = """
# Commands

| Command | Description |
|---------|-------------|
| `/help` or `/h` | Show this help |
| `/setup` | Configure LLM providers |
| `/gather` | Gather career data |
| `/profile` | View your profile |
| `/goals` | View career goals |
| `/thread [name]` | Show or switch thread |
| `/threads` | List all threads |
| `/memory` | Show memory stats |
| `/debug` | Toggle debug mode |
| `/verbose` | System information |
| `/agents` | List specialist agents |
| `/clear` | Clear current thread |
| `/reset` | Factory reset |
| `/quit` or `/q` | Exit |

## Tips

- Type naturally — I understand conversational requests
- Ask me to remember things like "remember I prefer remote work"
- Request specific actions like "analyze my skill gaps for ML Engineer"
"""

    def compose(self) -> ComposeResult:
        yield Markdown(self._HELP_TEXT)


class ProfileScreen(ModalScreen):
    """Profile and goals display screen."""

    BINDINGS = [Binding("escape,q", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        profile = container.profile
        parts = ["# Your Profile\n"]
        if profile.name:
            parts.append(f"**Name:** {profile.name}")
        if profile.current_role:
            parts.append(f"**Role:** {profile.current_role}")
        if profile.years_experience:
            parts.append(f"**Experience:** {profile.years_experience} years")
        if profile.technical_skills:
            parts.append(f"**Skills:** {', '.join(profile.technical_skills[:10])}")
        if profile.target_roles:
            parts.append(f"**Target Roles:** {', '.join(profile.target_roles)}")
        if profile.goals:
            parts.append("\n## Goals\n")
            for i, goal in enumerate(profile.goals, 1):
                parts.append(f"{i}. {goal.description}")
        if not profile.name:
            parts.append(
                "No profile configured yet. Tell me about yourself to get started!"
            )
        yield Markdown("\n".join(parts))


class ThreadSwitchDialog(ModalScreen[str | None]):
    """Thread name input dialog."""

    BINDINGS = [Binding("escape", "dismiss_cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Switch to thread:")
            yield Input(placeholder="thread name", id="thread-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else None)

    def action_dismiss_cancel(self) -> None:
        self.dismiss(None)


class SetupScreen(Screen):
    """Full provider setup wizard."""

    BINDINGS = [Binding("escape", "finish_setup", "Done")]

    _PROVIDERS = [
        ("fu7ur3pr00f", "FutureProof Proxy (recommended — free tokens)"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("google", "Google Gemini"),
        ("azure", "Azure OpenAI"),
        ("ollama", "Ollama (local)"),
    ]

    _PROVIDER_KEYS: dict[str, list[tuple[str, str, bool]]] = {
        "fu7ur3pr00f": [("FU7UR3PR00F_PROXY_KEY", "Proxy API key", True)],
        "openai": [("OPENAI_API_KEY", "OpenAI API key", True)],
        "anthropic": [("ANTHROPIC_API_KEY", "Anthropic API key", True)],
        "google": [("GOOGLE_API_KEY", "Google API key", True)],
        "azure": [
            ("AZURE_OPENAI_API_KEY", "Azure API key", True),
            ("AZURE_OPENAI_ENDPOINT", "Azure endpoint URL", False),
        ],
        "ollama": [
            (
                "OLLAMA_BASE_URL",
                "Ollama base URL (default: http://localhost:11434)",
                False,
            )
        ],
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected_provider: str = "fu7ur3pr00f"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("FUTUREPROOF SETUP", classes="setup-title")
            yield Label("Select LLM provider:", classes="setup-label")
            for provider_id, label in self._PROVIDERS:
                css_class = (
                    "setup-provider-option --selected"
                    if provider_id == self._selected_provider
                    else "setup-provider-option"
                )
                yield Button(label, id=f"provider-{provider_id}", classes=css_class)
            yield Static("", id="key-section")
            yield Button("Save & Continue", id="btn-save", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("provider-"):
            provider = btn_id[len("provider-") :]
            self._selected_provider = provider
            for p_id, _ in self._PROVIDERS:
                btn = self.query_one(f"#provider-{p_id}", Button)
                if p_id == provider:
                    btn.add_class("--selected")
                else:
                    btn.remove_class("--selected")
            self._render_key_section()
        elif btn_id == "btn-save":
            self._save_and_finish()

    def _render_key_section(self) -> None:
        section = self.query_one("#key-section", Static)
        section.remove_children()
        keys = self._PROVIDER_KEYS.get(self._selected_provider, [])
        for env_var, label, is_password in keys:
            section.mount(Label(f"{label}:", classes="setup-label"))
            section.mount(
                Input(
                    placeholder=env_var,
                    id=f"input-{env_var}",
                    password=is_password,
                )
            )

    def _save_and_finish(self) -> None:
        from fu7ur3pr00f.config import write_user_setting

        keys = self._PROVIDER_KEYS.get(self._selected_provider, [])
        for env_var, *_ in keys:
            inp = self.query_one(f"#input-{env_var}", Input)
            value = inp.value.strip()
            if value:
                write_user_setting(env_var, value)
        write_user_setting("ACTIVE_PROVIDER", self._selected_provider)
        self.app.notify("Setup saved! Restart fu7ur3pr00f to apply changes.")
        self.app.pop_screen()

    def action_finish_setup(self) -> None:
        self.app.pop_screen()
