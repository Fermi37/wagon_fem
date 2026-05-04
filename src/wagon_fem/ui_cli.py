"""Typer CLI wrapper to launch the Wagon FEM Gradio UI.

This provides a small, ergonomic CLI to start the Gradio app with
flags for host/port/share and simple logging configuration.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import typer

app = typer.Typer(help="Wagon FEM UI CLI")


def _env_bool(names: list[str], default: bool = False) -> bool:
    for n in names:
        v = os.environ.get(n)
        if v is not None:
            return str(v).lower() in ("1", "true", "yes", "y")
    return default


@app.command("serve")
def serve(
    host: Optional[str] = typer.Option(
        None, help="Host to bind (env: WAGON_FEM_HOST)"),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Port to bind (env: WAGON_FEM_PORT)", min=1, max=65535),
    share: Optional[bool] = typer.Option(
        None, "--share/--no-share", help="Enable Gradio share link (env: WAGON_FEM_SHARE)"),
    no_queue: bool = typer.Option(
        False, help="Disable Gradio queue() before launching"),
    log_level: str = typer.Option(
        "info", "--log-level", "-l", help="Logging level"),
):
    """Launch the Wagon FEM Gradio UI.

    Examples:
      python -m wagon_fem.ui_cli serve --port 7860 --share
    """

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level)
    logger = logging.getLogger(__name__)

    host = host or os.environ.get(
        "WAGON_FEM_HOST", os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"))
    port = port or int(os.environ.get(
        "WAGON_FEM_PORT", os.environ.get("PORT", 7860)))

    if share is None:
        share = _env_bool(["WAGON_FEM_SHARE", "GRADIO_SHARE"], default=False)

    logger.info("Launching Wagon FEM UI on %s:%s (share=%s, queue=%s)",
                host, port, share, not no_queue)

    try:
        # import the demo Blocks instance from the UI module (this defines the layout)
        from .ui import demo
    except Exception as e:  # pragma: no cover - runtime import failure
        logger.exception("Failed to import UI module: %s", e)
        raise typer.Exit(code=1)

    if not no_queue:
        try:
            demo.queue()
        except Exception:
            logger.debug(
                "demo.queue() not available; continuing without global queue")

    try:
        demo.launch(server_name=host, server_port=int(port), share=bool(share))
    except Exception as e:  # pragma: no cover - runtime launch failure
        logger.exception("Failed to launch Gradio demo: %s", e)
        raise typer.Exit(code=1)


def main() -> None:
    """Entry point for packaging tools (console_scripts)."""
    app()


if __name__ == "__main__":
    main()
