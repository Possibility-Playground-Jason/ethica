# ABOUTME: Implementation of 'ethica serve' command
# ABOUTME: Starts the FastAPI server for remote compliance checking

"""
Start the ethica API server.
"""

import typer
from rich.console import Console

console = Console()


def serve_command(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Bind address",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Bind port",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development",
    ),
) -> None:
    """Start the ethica API server"""
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[red]Server dependencies not installed.[/red]\n"
            "Install them with: [cyan]pip install ethica\\[server][/cyan]"
        )
        raise typer.Exit(1)

    console.print(f"[green]Starting ethica server on {host}:{port}[/green]")
    console.print("API docs available at [cyan]http://{}:{}/docs[/cyan]".format(host, port))

    uvicorn.run(
        "ethica.api.server:app",
        host=host,
        port=port,
        reload=reload,
    )
