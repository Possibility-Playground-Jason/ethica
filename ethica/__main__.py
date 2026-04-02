# ABOUTME: CLI entry point for ethica command
# ABOUTME: Sets up typer app and registers all command groups

"""
Main CLI entry point for ethica.
"""

import typer
from rich.console import Console

from ethica.cli import init, check, frameworks, generate, serve

app = typer.Typer(
    name="ethica",
    help="Framework-agnostic platform for AI ethics compliance checking",
    no_args_is_help=True,
)

console = Console()

# Register command groups
app.command(name="init")(init.init_command)
app.command(name="check")(check.check_command)
app.command(name="generate")(generate.generate_command)
app.command(name="serve")(serve.serve_command)
app.add_typer(frameworks.app, name="frameworks")


@app.command()
def version() -> None:
    """Show version information"""
    from ethica import __version__

    console.print(f"ethica version {__version__}")


def main() -> None:
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
