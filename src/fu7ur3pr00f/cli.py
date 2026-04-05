"""fu7ur3pr00f CLI - Career Intelligence System."""

import inspect
import logging

import click
import typer

from . import __version__  # noqa: E402
from .config import settings  # noqa: E402
from .utils.console import console  # noqa: E402

logger = logging.getLogger(__name__)


def _patch_click_make_metavar() -> None:
    """Patch Click < 8.2 to accept Typer's ``ctx=`` argument.

    Typer 0.24 calls ``make_metavar(ctx=...)`` while Click 8.1 exposes
    ``make_metavar(self)``. This shim keeps ``--help`` working until the
    dependency floor is raised.
    """
    for cls in (click.Parameter, click.Option, click.Argument):
        make_metavar = getattr(cls, "make_metavar", None)
        if make_metavar is None:
            continue
        if "ctx" in inspect.signature(make_metavar).parameters:
            continue

        def _compat_make_metavar(
            self, ctx=None, _orig=make_metavar
        ):  # type: ignore[no-untyped-def]
            return _orig(self)

        cls.make_metavar = _compat_make_metavar  # type: ignore[assignment]


_patch_click_make_metavar()

app = typer.Typer(
    name="fu7ur3pr00f",
    help="Career Intelligence System - chat with your career agent",
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]fu7ur3pr00f[/bold blue] v{__version__}")
        raise typer.Exit()


_VERSION_OPTION = typer.Option(
    False,
    "--version",
    "-v",
    callback=version_callback,
    is_eager=True,
    help="Show the application version and exit.",
)
_THREAD_OPTION = typer.Option(
    "main",
    "--thread",
    "-t",
    help="Conversation thread ID",
)
_DEBUG_OPTION = typer.Option(
    False,
    "--debug",
    help="Show debug-level logs in terminal",
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = _VERSION_OPTION,
    thread: str = _THREAD_OPTION,
    debug: bool = _DEBUG_OPTION,
) -> None:
    """fu7ur3pr00f - Know thyself through your data."""
    settings.ensure_directories()

    # Initialize logging — file handler always active, console only shows warnings
    from .utils.logging import setup_logging

    setup_logging(
        level="DEBUG",
        log_file=settings.data_dir / "fu7ur3pr00f.log",
        console_level="WARNING",
    )

    # If a subcommand was invoked, let it handle things
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand → launch chat
    if debug:
        fp_logger = logging.getLogger("fu7ur3pr00f")
        for handler in fp_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setLevel(logging.DEBUG)

    from .chat.client import run_chat

    try:
        run_chat(thread_id=thread)
    except KeyboardInterrupt:
        console.print("\n[dim]Chat ended.[/dim]")
    except Exception as e:
        console.print(f"[red]Chat error: {e}[/red]")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
