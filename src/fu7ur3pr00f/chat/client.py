"""Chat client for FutureProof conversational interface.

Combines prompt-toolkit for input handling with Rich for output display.
Provides both sync and async chat loops for different use cases.
"""

import warnings

# Suppress noisy Pydantic serialization warnings from structured output
# Must be set before third-party imports that trigger model validation.
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import logging  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
from collections.abc import Callable  # noqa: E402
from pathlib import Path  # noqa: E402

from prompt_toolkit import PromptSession  # noqa: E402
from prompt_toolkit.formatted_text import HTML  # noqa: E402
from prompt_toolkit.history import FileHistory  # noqa: E402
from prompt_toolkit.styles import Style as PTStyle  # noqa: E402
from rich.markdown import Markdown  # noqa: E402

from fu7ur3pr00f.agents.blackboard import get_conversation_engine  # noqa: E402
from fu7ur3pr00f.agents.specialists.blackboard_factory import (  # noqa: E402
    get_agent_config,
)
from fu7ur3pr00f.agents.specialists.orchestrator import (  # noqa: E402
    get_orchestrator,
    reset_orchestrator,
)
from fu7ur3pr00f.chat.ui import (  # noqa: E402
    console,
    display_blackboard_result,
    display_error,
    display_goals,
    display_help,
    display_interrupt_confirmation,
    display_model_info,
    display_profile_summary,
    display_specialist_progress,
    display_tool_result,
    display_tool_start,
    display_welcome,
)
from fu7ur3pr00f.config import settings  # noqa: E402
from fu7ur3pr00f.constants import (  # noqa: E402
    COLOR_ACCENT,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_SUCCESS,
    COLOR_WARNING,
)
from fu7ur3pr00f.memory.checkpointer import get_data_dir, list_threads  # noqa: E402
from fu7ur3pr00f.memory.profile import load_profile  # noqa: E402
from fu7ur3pr00f.utils.security import sanitize_error  # noqa: E402

logger = logging.getLogger(__name__)

# ── Prompt styling ────────────────────────────────────────────────────────

_PROMPT_STYLE = PTStyle.from_dict({"prompt": f"{COLOR_WARNING} bold"})
_PROMPT_MSG = HTML("<prompt>\u25b6 </prompt>")

# Thread ID validation (alphanumeric, dash, underscore only, max 64 chars)
_VALID_THREAD_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def get_history_path() -> Path:
    """Get the path for command history file."""
    return get_data_dir() / "chat_history"


# ── Command Handlers ────────────────────────────────────────────────────────

def _cmd_quit(chat_state: dict, arg: str) -> bool:
    console.print(f"[{COLOR_INFO}]Goodbye! Your conversation is saved.[/{COLOR_INFO}]")
    return True


def _cmd_help(chat_state: dict, arg: str) -> bool:
    display_help()
    return False


def _cmd_profile(chat_state: dict, arg: str) -> bool:
    display_profile_summary(load_profile())
    return False


def _cmd_goals(chat_state: dict, arg: str) -> bool:
    display_goals(load_profile())
    return False


def _cmd_clear(chat_state: dict, arg: str) -> bool:
    from fu7ur3pr00f.memory.checkpointer import clear_thread_history

    clear_thread_history(chat_state["thread_id"])
    console.print(f"[{COLOR_INFO}]Conversation history cleared.[/{COLOR_INFO}]")
    return False


def _cmd_thread(chat_state: dict, arg: str) -> bool:
    if not arg:
        console.print(
            f"[{COLOR_INFO}]Current thread: [bold]{chat_state['thread_id']}[/bold][/{COLOR_INFO}]"
        )
    else:
        if not _VALID_THREAD_ID_RE.match(arg):
            console.print(
                f"[{COLOR_ERROR}]Invalid thread ID: use alphanumeric characters, "
                f"dashes, and underscores only (max 64 chars).[/{COLOR_ERROR}]"
            )
            return False
        chat_state["thread_id"] = arg
        chat_state["config"] = get_agent_config(thread_id=arg)
        console.print(
            f"[{COLOR_SUCCESS}]Switched to thread: [bold]{arg}[/bold][/{COLOR_SUCCESS}]"
        )
    return False


def _cmd_threads(chat_state: dict, arg: str) -> bool:
    thread_list = list_threads()
    if thread_list:
        console.print(f"[bold {COLOR_ACCENT}]Conversation threads:[/bold {COLOR_ACCENT}]")
        for t in thread_list:
            marker = " (active)" if t == chat_state["thread_id"] else ""
            console.print(f"  - {t}[bold {COLOR_WARNING}]{marker}[/bold {COLOR_WARNING}]")
    else:
        console.print(f"[{COLOR_INFO}]No conversation threads found.[/{COLOR_INFO}]")
    return False


def _cmd_memory(chat_state: dict, arg: str) -> bool:
    data_dir = get_data_dir()
    profile = load_profile()
    thread_list = list_threads()

    console.print("[bold #5bc0be]Memory Status[/bold #5bc0be]\n")
    console.print(f"  Data directory: {data_dir}")
    console.print(f"  Conversation threads: {len(thread_list)}")
    console.print(f"  Profile configured: {'Yes' if profile.name else 'No'}")
    if profile.goals:
        console.print(f"  Career goals: {len(profile.goals)}")
    console.print()
    return False


def _cmd_gather(chat_state: dict, arg: str) -> bool:
    """Gather career data from all sources using GathererService."""
    console.print("[bold #5bc0be]Gathering career data...[/bold #5bc0be]\n")

    # Enable verbose logging during gather
    logging.getLogger("fu7ur3pr00f.gatherers").setLevel(logging.INFO)

    try:
        from fu7ur3pr00f.services.gatherer_service import GathererService

        service = GathererService()
        results = service.gather_all(verbose=True)

        successful = sum(1 for s in results.values() if s)
        console.print(
            f"\n[{COLOR_SUCCESS}]✓ Gathered {successful}/{len(results)} sources[/{COLOR_SUCCESS}]"
        )
        console.print(
            f"[{COLOR_SUCCESS}]✓ Data indexed to knowledge base[/{COLOR_SUCCESS}]\n"
        )
    except Exception as e:
        logger.exception("Gather failed")
        display_error(sanitize_error(f"Gather failed: {e}"))
    return False


def _cmd_agents(chat_state: dict, arg: str) -> bool:
    orchestrator = get_orchestrator()
    agents = orchestrator.list_agents()
    console.print("[bold #5bc0be]Specialist Agents[/bold #5bc0be]\n")
    for a in agents:
        console.print(
            f"  [bold {COLOR_WARNING}]{a['name']}[/bold {COLOR_WARNING}]: {a['description']}"
        )
    console.print()
    return False


def _cmd_debug(chat_state: dict, arg: str) -> bool:
    current_level = logging.getLogger().level
    if current_level <= logging.DEBUG:
        logging.getLogger().setLevel(logging.WARNING)
        console.print(f"[{COLOR_ERROR}]Debug mode OFF[/{COLOR_ERROR}]\n")
    else:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("fu7ur3pr00f").setLevel(logging.DEBUG)
        console.print(f"[{COLOR_SUCCESS}]Debug mode ON[/{COLOR_SUCCESS}]\n")
        console.print("[dim]You will now see:[/dim]")
        console.print("  - LLM API calls and responses")
        console.print("  - Tool execution details")
        console.print("  - Agent routing decisions")
        console.print("  - ChromaDB operations\n")
    return False


def _cmd_verbose(chat_state: dict, arg: str) -> bool:
    model_name = get_orchestrator().get_model_name() or "unknown"
    console.print("[bold #5bc0be]System Information[/bold #5bc0be]\n")
    console.print(f"Data directory: {get_data_dir()}")
    console.print(f"LLM Provider: {settings.llm_provider or 'auto-detect'}")
    console.print(f"Model: {model_name}")
    console.print(f"Portfolio URL: {settings.portfolio_url or 'Not configured'}")
    console.print(f"GitHub MCP: {'Enabled' if settings.has_github_mcp else 'Disabled'}")
    console.print(f"Tavily MCP: {'Enabled' if settings.has_tavily_mcp else 'Disabled'}")
    console.print(f"Debug level: {logging.getLevelName(logging.getLogger().level)}\n")
    return False


def _cmd_reset(chat_state: dict, arg: str) -> bool:
    console.print(f"[bold {COLOR_ERROR}]Factory Reset[/bold {COLOR_ERROR}]\n")
    console.print("This will delete all conversation history, your user profile,")
    console.print("and the knowledge base. It will preserve raw data in data/raw/.\n")

    try:
        confirm = chat_state["session"].prompt("Proceed? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = ""

    if confirm not in ("y", "yes"):
        console.print(f"[{COLOR_INFO}]Reset cancelled.[/{COLOR_INFO}]")
        return False

    deleted = settings.factory_reset()

    console.print(
        f"\n[{COLOR_SUCCESS}]Factory reset complete.[/{COLOR_SUCCESS}] Cleared {deleted} items."
    )
    console.print(f"[{COLOR_INFO}]Restart FutureProof to start fresh.[/{COLOR_INFO}]")
    return True


_COMMAND_MAP: dict[str, Callable[[dict, str], bool]] = {
    "/quit": _cmd_quit,
    "/q": _cmd_quit,
    "/exit": _cmd_quit,
    "/help": _cmd_help,
    "/h": _cmd_help,
    "/profile": _cmd_profile,
    "/goals": _cmd_goals,
    "/clear": _cmd_clear,
    "/thread": _cmd_thread,
    "/threads": _cmd_threads,
    "/memory": _cmd_memory,
    "/gather": _cmd_gather,
    "/agents": _cmd_agents,
    "/debug": _cmd_debug,
    "/verbose": _cmd_verbose,
    "/reset": _cmd_reset,
}


def handle_command(command: str, *, chat_state: dict) -> bool:
    """Handle slash commands using a command dispatcher map.

    Args:
        command: The command string (including leading /)
        chat_state: Mutable dict with session state

    Returns:
        True if the chat should exit, False otherwise
    """
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    handler = _COMMAND_MAP.get(cmd)
    if handler:
        return handler(chat_state, arg)

    console.print(
        f"[{COLOR_WARNING}]Unknown command: {cmd}. "
        f"Type /help for available commands.[/{COLOR_WARNING}]"
    )
    return False


def _ensure_orchestrator(thread_id: str, first_run: bool = False) -> tuple:
    """Ensure orchestrator is initialized, running setup if needed."""
    from fu7ur3pr00f.chat.setup import run_setup

    if not settings.active_provider:
        run_setup(console, first_run=True)

    try:
        orchestrator = get_orchestrator()
        config = get_agent_config(thread_id=thread_id)
        model_name = orchestrator.get_model_name()
        if model_name:
            display_model_info(model_name)
        return orchestrator, config
    except Exception as e:
        from pydantic import ValidationError

        is_val_err = isinstance(e, ValidationError) or isinstance(
            e.__cause__, ValidationError
        )
        if is_val_err:
            display_error(
                f"Configuration error — check your settings.\n{e}\n\nRun /setup..."
            )
            run_setup(console, first_run=True)
            try:
                orchestrator = get_orchestrator()
                config = get_agent_config(thread_id=thread_id)
                model_name = orchestrator.get_model_name()
                if model_name:
                    display_model_info(model_name)
                return orchestrator, config
            except Exception as retry_err:
                display_error(sanitize_error(f"Still failing: {retry_err}"))
                raise
        else:
            display_error(sanitize_error(f"Failed to initialize agent: {e}"))
            raise


def run_chat(
    thread_id: str = "main",
) -> None:  # noqa: C901 - Main chat loop with command/tool handling
    """Run the synchronous chat loop.

    Args:
        thread_id: Conversation thread identifier for persistence
    """
    # Set up prompt session with history
    history_path = get_history_path()
    history = FileHistory(str(history_path))
    session = PromptSession(history=history)
    if history_path.exists():
        history_path.chmod(0o600)

    # Display welcome message
    display_welcome()

    # Initialise orchestrator and display model info
    try:
        orchestrator, config = _ensure_orchestrator(thread_id)
    except Exception:
        return

    # Mutable state shared with handle_command for /thread switching
    chat_state: dict = {
        "thread_id": thread_id,
        "config": config,
        "session": session,
    }

    # Turn-level timing state for tool execution tracking
    tool_start_times: dict[str, float] = {}

    def _on_specialist_start(name: str) -> None:
        display_specialist_progress(name, "working")

    def _on_specialist_complete(name: str, finding: dict) -> None:
        display_specialist_progress(name, "done")
        reasoning = finding.get("reasoning", "")
        if reasoning:
            console.print(Markdown(reasoning))
            console.print()

    def _on_tool_start(specialist: str, tool_name: str, args: dict) -> None:
        tool_start_times[f"{specialist}:{tool_name}"] = time.monotonic()
        display_tool_start(tool_name, args)

    def _on_tool_result(specialist: str, tool_name: str, result: str) -> None:
        key = f"{specialist}:{tool_name}"
        elapsed_t = time.monotonic() - tool_start_times.pop(key, time.monotonic())
        display_tool_result(tool_name, result, elapsed_t)

    def _confirm(question: str, details: str) -> bool:
        display_interrupt_confirmation(question, details)
        try:
            resp = session.prompt("Approve? [y/N] ").strip().lower()
            return resp in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    while True:
        try:
            # Get user input
            user_input = session.prompt(
                _PROMPT_MSG,
                style=_PROMPT_STYLE,
                is_password=False,
            ).strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                if user_input.strip().lower() == "/setup":
                    from fu7ur3pr00f.chat.setup import run_setup

                    changed = run_setup(console)
                    if changed:
                        reset_orchestrator()
                        try:
                            orchestrator, config = _ensure_orchestrator(
                                chat_state["thread_id"]
                            )
                            chat_state["config"] = config
                        except Exception:
                            pass
                    continue
                if handle_command(user_input, chat_state=chat_state):
                    break
                # Pick up thread changes from /thread command
                config = chat_state["config"]
                continue

            # All queries go through conversation engine (outer graph)
            console.print()  # Blank line before response

            engine = get_conversation_engine()
            tool_start_times.clear()  # Reset for this turn

            try:
                result = engine.invoke_turn(
                    query=user_input,
                    thread_id=chat_state["thread_id"],
                    on_specialist_start=_on_specialist_start,
                    on_specialist_complete=_on_specialist_complete,
                    on_tool_start=_on_tool_start,
                    on_tool_result=_on_tool_result,
                    confirm_fn=_confirm,
                )
                # Display synthesis result
                display_blackboard_result(
                    synthesis=result.synthesis,
                    specialists_contributed=result.specialists,
                    elapsed=result.elapsed,
                )
                # Display suggestions if any
                if result.suggested_next:
                    console.print()
                    console.print("[dim]Suggested next:[/dim]")
                    for i, suggestion in enumerate(result.suggested_next, 1):
                        console.print(f"  {i}. {suggestion}")
            except Exception as e:
                logger.exception("Conversation execution failed")
                display_error(sanitize_error(f"Analysis failed: {e}"))

        except KeyboardInterrupt:
            console.print(f"\n[{COLOR_INFO}]Use /quit to exit[/{COLOR_INFO}]")
            continue
        except EOFError:
            console.print(f"\n[{COLOR_INFO}]Goodbye![/{COLOR_INFO}]")
            break
        except Exception as e:
            # Catch unhandled exceptions from event loop / nest_asyncio
            # to prevent the chat from crashing
            logger.exception("Unhandled error in chat loop")
            if str(e):
                display_error(sanitize_error(f"Unexpected error: {e}"))
            else:
                # Bare Exception() with no message — typically from
                # nest_asyncio/prompt_toolkit event loop conflicts
                console.print(
                    f"\n[{COLOR_INFO}]Press ENTER to continue...[/{COLOR_INFO}]"
                )
            continue
