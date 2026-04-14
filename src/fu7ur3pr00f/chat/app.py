"""FutureProofApp — main Textual application for fu7ur3pr00f chat."""

import asyncio
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import uvicorn
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input

from fu7ur3pr00f.agents.blackboard.engine import get_conversation_engine
from fu7ur3pr00f.agents.blackboard.streaming import synthesis_token_callback
from fu7ur3pr00f.chat.screens import (
    ConfirmDialog,
    HelpScreen,
    ProfileScreen,
    SetupScreen,
)
from fu7ur3pr00f.chat.widgets import (
    MessageBubble,
    ResponseBubble,
    SpecialistStatus,
    ToolLogPanel,
)
from fu7ur3pr00f.memory.checkpointer import list_threads
from fu7ur3pr00f.memory.profile import load_profile

logger = logging.getLogger(__name__)


class FutureProofApp(App):
    """Main Textual application for fu7ur3pr00f career intelligence chat."""

    CSS_PATH = Path(__file__).parent / "style.tcss"
    TITLE = "FUTUREPROOF"
    BINDINGS = [
        Binding("ctrl+t", "toggle_tool_log", "Toggle tool log"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, thread_id: str = "main", **kwargs) -> None:
        super().__init__(**kwargs)
        self._chat_thread_id: str = thread_id
        self._engine = get_conversation_engine()
        self._a2a_server_thread: threading.Thread | None = None

    def on_mount(self) -> None:
        # Start A2A Server in background
        self._start_a2a_server()

        profile = load_profile()
        if not profile.name:
            self.push_screen(SetupScreen())
        # Be defensive: during tests or alternate layouts the specialist-status
        # widget might not be present yet. Avoid raising NoMatches here so the
        # app can mount cleanly in test environments.
        try:
            self.query_one("#specialist-status", SpecialistStatus).display = False
        except Exception:  # textual.css.query.NoMatches or others
            logger.debug("specialist-status not present on mount; skipping hide")

        try:
            self.query_one(Input).focus()
        except Exception:
            logger.debug("Input widget not present to focus on mount")

    def compose(self) -> ComposeResult:
        """Compose the main application layout.

        Tests expect specific widget ids to exist (eg. #input-bar), so keep the
        layout minimal and stable here.
        """
        # Header / footer
        yield Header()
        # Main chat view
        yield VerticalScroll(id="chat-view")
        # Input bar docked at bottom (style hooks expect #input-bar)
        yield Input(id="input-bar", placeholder="Type a message...")
        # Specialist status and tool log
        yield SpecialistStatus(id="specialist-status")
        yield ToolLogPanel(id="tool-log-panel")
        yield Footer()

    def _start_a2a_server(self) -> None:
        """Launch the A2A FastAPI server in a separate thread."""
        # Only start A2A server when configured. Tests run with default
        # settings and should not attempt to start an HTTP server.
        from fu7ur3pr00f.container import container

        if not getattr(container.settings, "a2a_agent_key", ""):
            logger.debug("A2A agent key not configured; skipping A2A server start")
            return

        from fu7ur3pr00f.agents.blackboard.a2a_handler import A2AHandler

        def run_server():
            handler = A2AHandler()
            app = A2AFastAPIApplication(handler=handler)  # type: ignore[arg-type]
            # Mount at /api/a2a as per design
            # A2AFastAPIApplication does not type as a standard ASGI app in the
            # SDK typing; cast at call-site to Any to satisfy static type checks.
            uvicorn.run(app, host="0.0.0.0", port=8000)  # type: ignore[arg-type]

        self._a2a_server_thread = threading.Thread(target=run_server, daemon=True)
        self._a2a_server_thread.start()
        logger.info("A2A Server started on port 8000")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.clear()
        if not text:
            return
        if text.startswith("/"):
            self._handle_command(text)
        else:
            self._process_query(text)

    def _handle_command(self, text: str) -> None:  # noqa: C901
        """Dispatch slash commands."""
        # NOTE: This function is intentionally straightforward command dispatch
        # logic. Cyclomatic complexity is acceptable for an input command router.
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/quit", "/q"):
            self.exit()
        elif cmd in ("/help", "/h"):
            self.push_screen(HelpScreen())
        elif cmd in ("/profile",):
            self.push_screen(ProfileScreen())
        elif cmd in ("/goals",):
            self.push_screen(ProfileScreen())
        elif cmd in ("/setup",):
            self.push_screen(SetupScreen())
        elif cmd in ("/thread",):
            if arg:
                self._chat_thread_id = arg
                self.notify(f"Switched to thread: {arg}")
            else:
                self.notify(f"Current thread: {self._chat_thread_id}")
        elif cmd in ("/threads",):
            try:
                threads = list_threads()
                self.notify(
                    f"Threads: {', '.join(threads)}" if threads else "No threads found."
                )
            except Exception:
                self.notify("Could not list threads.", severity="warning")
        elif cmd in ("/clear",):
            self._clear_thread()
        elif cmd in ("/memory",):
            profile = load_profile()
            self.notify(
                f"Profile: {profile.name or 'empty'} | Thread: {self._chat_thread_id}"
            )
        elif cmd in ("/gather",):
            self.notify(
                "Use: fu7ur3pr00f gather — run from CLI for data gathering.",
                severity="information",
            )
        elif cmd in ("/debug",):
            self.notify("Debug mode: check fu7ur3pr00f.log for details.")
        elif cmd in ("/agents",):
            self.notify("Specialists: coach, jobs, learning, code, founder")
        elif cmd in ("/reset",):
            self.notify(
                "Factory reset: run fu7ur3pr00f reset from CLI.", severity="warning"
            )
        elif cmd in ("/verbose",):
            self.notify(f"Thread: {self._chat_thread_id} | Version: 0.2.0")
        else:
            self.notify(f"Unknown command: {cmd}", severity="warning")

    def _clear_thread(self) -> None:
        from fu7ur3pr00f.agents.blackboard.engine import reset_conversation_engine

        reset_conversation_engine()
        self._engine = get_conversation_engine()
        chat_view = self.query_one("#chat-view", VerticalScroll)
        chat_view.remove_children()
        self.notify("Thread cleared.")

    def _process_query(self, query: str) -> None:
        """Mount bubbles and dispatch query to worker thread."""
        chat_view = self.query_one("#chat-view", VerticalScroll)
        user_bubble = MessageBubble(query)
        chat_view.mount(user_bubble)
        response_bubble = ResponseBubble()
        chat_view.mount(response_bubble)
        chat_view.scroll_end(animate=False)

        specialist_status = self.query_one("#specialist-status", SpecialistStatus)
        specialist_status.reset()
        tool_log = self.query_one("#tool-log-panel", ToolLogPanel)

        self._run_query(query, response_bubble, specialist_status, tool_log)

    @work(thread=True, exclusive=True)
    def _run_query(
        self,
        query: str,
        response_bubble: ResponseBubble,
        specialist_status: SpecialistStatus,
        tool_log: ToolLogPanel,
    ) -> None:
        """Worker: run invoke_turn in OS thread, push updates via call_from_thread."""
        started_streaming = False

        def on_synthesis_token(token: str) -> None:
            nonlocal started_streaming
            if not started_streaming:
                started_streaming = True
                self.call_from_thread(response_bubble.start_streaming)
            self.call_from_thread(response_bubble.append_token, token)

        def on_specialist_start(name: str) -> None:
            self.call_from_thread(specialist_status.start_specialist, name)

        def on_specialist_complete(name: str, _: Any) -> None:
            self.call_from_thread(specialist_status.complete_specialist, name)

        def on_tool_start(specialist: str, tool: str, args: dict) -> None:
            self.call_from_thread(tool_log.write_tool_start, specialist, tool, args)

        def on_tool_result(specialist: str, tool: str, result: str) -> None:
            self.call_from_thread(tool_log.write_tool_result, specialist, tool, result)

        token_cv = synthesis_token_callback.set(on_synthesis_token)
        try:
            result = self._engine.invoke_turn(
                query=query,
                thread_id=self._chat_thread_id,
                on_specialist_start=on_specialist_start,
                on_specialist_complete=on_specialist_complete,
                on_tool_start=on_tool_start,
                on_tool_result=on_tool_result,
                confirm_fn=self._make_confirm_fn(),
            )
            self.call_from_thread(
                response_bubble.finalize,
                {
                    "synthesis": result.synthesis,
                    "specialists": result.specialists,
                    "elapsed": result.elapsed,
                },
            )
        except Exception as e:
            logger.exception("Query failed: %s", e)
            self.call_from_thread(response_bubble.finalize, None)
            self.call_from_thread(self.notify, f"Error: {e}", severity="error")
        finally:
            synthesis_token_callback.reset(token_cv)

    def _make_confirm_fn(self) -> Callable[[str, str], bool]:
        """Return a HITL confirmation function for use in worker thread."""
        result_holder: list[bool] = []
        event = threading.Event()

        async def _push_dialog(question: str, details: str) -> None:
            result = await self.push_screen_wait(ConfirmDialog(question, details))

            result_holder.append(bool(result))
            event.set()

        def confirm_fn(question: str, details: str = "") -> bool:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(_push_dialog(question, details), loop)
            event.wait(timeout=300)
            return result_holder[0] if result_holder else False

        return confirm_fn

    def action_toggle_tool_log(self) -> None:
        self.query_one("#tool-log-panel", ToolLogPanel).toggle_panel()


def run_chat(thread_id: str = "main") -> None:
    """Entry point: launch the Textual app."""
    FutureProofApp(thread_id=thread_id).run()
