"""Textual widgets for fu7ur3pr00f chat UI."""

import os

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, LoadingIndicator, Markdown, RichLog, Static


def _animations_enabled() -> bool:
    """Return False when NO_COLOR is set or TEXTUAL_ANIMATIONS=disabled."""
    if os.getenv("NO_COLOR") is not None:
        return False
    if os.getenv("TEXTUAL_ANIMATIONS", "").lower() == "disabled":
        return False
    return True


class SplashBanner(Static):
    """Animated splash banner using TerminalTextEffects Decrypt effect."""

    def on_mount(self) -> None:
        if _animations_enabled():
            self._run_tte()
        else:
            self.update("FUTUREPROOF")

    @work(thread=True)
    def _run_tte(self) -> None:
        try:
            from terminaltexteffects.effects.effect_decrypt import Decrypt

            effect = Decrypt("FUTUREPROOF")
            with effect.terminal_output(end_symbol=" "):
                for frame in effect:
                    self.app.call_from_thread(self.update, frame)
        except Exception:
            self.app.call_from_thread(self.update, "FUTUREPROOF")


class MessageBubble(Static):
    """User message bubble with fade+slide mount animation."""

    def __init__(self, content: str, **kwargs) -> None:
        super().__init__(content, **kwargs)

    def on_mount(self) -> None:
        if _animations_enabled():
            self.styles.opacity = 0.0
            self.animate("opacity", 1.0, duration=0.2)
        self.add_class("message-bubble-user")


class ResponseBubble(Widget):
    """AI response bubble with streaming support."""

    _accumulated: str = ""

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Markdown("")

    def on_mount(self) -> None:
        self.query_one(Markdown).display = False
        if _animations_enabled():
            self.styles.opacity = 0.0
            self.animate("opacity", 1.0, duration=0.15, easing="out_cubic")

    def start_streaming(self) -> None:
        """Switch from loading indicator to streaming markdown."""
        self.query_one(LoadingIndicator).display = False
        self.query_one(Markdown).display = True

    def append_token(self, token: str) -> None:
        """Accumulate a streaming token and update the Markdown widget."""
        self._accumulated += token
        self.query_one(Markdown).update(self._accumulated)

    def finalize(self, result: dict | None = None) -> None:
        """Finalize the response — hide loader, show full content."""
        self.query_one(LoadingIndicator).display = False
        md = self.query_one(Markdown)
        md.display = True
        if self._accumulated:
            md.update(self._accumulated)
        elif result:
            narrative = result.get("synthesis", {}).get(
                "narrative", "Analysis complete."
            )
            md.update(narrative)
        else:
            md.update("Analysis complete.")


class SpecialistBadge(Label):
    """Badge widget for a single specialist's working/done state."""

    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(f"◆ {name.upper()}", **kwargs)
        self._name = name


class SpecialistStatus(Widget):
    """Row of specialist badges with reactive state transitions."""

    _badges: dict[str, SpecialistBadge]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._badges = {}

    def compose(self) -> ComposeResult:
        yield Horizontal(id="badge-row")

    def start_specialist(self, name: str) -> None:
        """Mark specialist as working."""
        if name not in self._badges:
            badge = SpecialistBadge(name, classes="--working")
            self._badges[name] = badge
            self.query_one("#badge-row").mount(badge)
        else:
            badge = self._badges[name]
            badge.remove_class("--done")
            badge.add_class("--working")
        self.display = True

    def complete_specialist(self, name: str) -> None:
        """Mark specialist as done."""
        if name in self._badges:
            badge = self._badges[name]
            badge.remove_class("--working")
            badge.add_class("--done")

    def reset(self) -> None:
        """Clear all badges for next turn."""
        self._badges.clear()
        self.query_one("#badge-row").remove_children()
        self.display = False


class ToolLogPanel(Widget):
    """Collapsible tool log panel."""

    is_visible_panel: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield RichLog(id="tool-log", highlight=True, markup=True)

    def toggle_panel(self) -> None:
        self.is_visible_panel = not self.is_visible_panel

    def watch_is_visible_panel(self, visible: bool) -> None:
        if visible:
            self.add_class("--visible")
            if _animations_enabled():
                self.animate("styles.height", 8, duration=0.2, easing="out_cubic")
        else:
            self.remove_class("--visible")
            if _animations_enabled():
                self.animate("styles.height", 0, duration=0.2, easing="out_cubic")

    def write_tool_start(self, specialist: str, tool: str, args: dict) -> None:
        log = self.query_one(RichLog)
        args_str = ", ".join(f"{k}={v!r}" for k, v in list(args.items())[:3])
        log.write(f"[yellow]▶ {specialist}[/yellow].[cyan]{tool}[/cyan]({args_str})")

    def write_tool_result(self, _: str, tool: str, result: str) -> None:
        log = self.query_one(RichLog)
        preview = result[:200] + "…" if len(result) > 200 else result
        log.write(f"[green]✓ {tool}[/green]: {preview}")
