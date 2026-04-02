# ABOUTME: Implementation of 'ethica generate' command
# ABOUTME: Generates pre-filled model/system card from project introspection

"""
Generate a model card or system card for the current project.
"""

from pathlib import Path

import typer
from rich.console import Console

from ethica.utils.generate import generate_card
from ethica.utils.introspect import introspect_project

console = Console()


def generate_command(
    output: str = typer.Option(
        "docs/MODEL_CARD.md",
        "--output",
        "-o",
        help="Output file path",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing file",
    ),
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Print to stdout instead of writing a file",
    ),
) -> None:
    """Generate a pre-filled model/system card from project metadata"""

    project_path = Path.cwd()

    console.print("[dim]Scanning project...[/dim]")
    profile = introspect_project(project_path)

    # Report what was found
    if profile["ai_libraries"]:
        console.print(
            f"[dim]Found AI libraries: {', '.join(profile['ai_libraries'])}[/dim]"
        )
    if profile["project_types"]:
        console.print(
            f"[dim]Detected: {', '.join(profile['project_types'])}[/dim]"
        )

    card = generate_card(profile)

    if stdout:
        console.print(card)
        return

    out_path = Path(output)
    if out_path.exists() and not force:
        console.print(
            f"[yellow]{out_path} already exists.[/yellow] Use --force to overwrite."
        )
        raise typer.Exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(card)
    console.print(f"[green]\u2713[/green] Generated {out_path}")
    console.print(
        "\n[bold]Next:[/bold] Review the file and fill in [cyan][TODO][/cyan] sections."
    )
