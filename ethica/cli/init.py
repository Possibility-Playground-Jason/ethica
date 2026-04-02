# ABOUTME: Implementation of 'ethica init' command
# ABOUTME: Initializes AI ethics compliance in a project

"""
Initialize ethics compliance configuration in a project.
"""

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from ethica import __version__
from ethica.utils.detect import detect_project_types

console = Console()


def init_command(
    framework: str = typer.Option(
        "unesco-2021",
        "--framework",
        "-f",
        help="Framework to initialize with",
    ),
    level: str = typer.Option(
        "standard",
        "--level",
        "-l",
        help="Compliance level (basic, standard, verified)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing configuration",
    ),
) -> None:
    """Initialize ethics compliance in your project"""

    config_path = Path(".ai-ethics.yaml")

    # Check if config already exists
    if config_path.exists() and not force:
        console.print(
            "[yellow]Configuration file .ai-ethics.yaml already exists.[/yellow]"
        )
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    # Detect project type
    project_types = detect_project_types(Path.cwd())
    if project_types:
        console.print(
            f"[dim]Detected project type(s): {', '.join(sorted(project_types))}[/dim]"
        )

    # Create configuration
    config = {
        "version": "1.0",
        "frameworks": [
            {
                "id": framework,
                "enabled": True,
                "compliance_level": level,
            }
        ],
        "exclude_checks": [],
        "custom_checks": [],
        "metadata": {
            "project_name": Path.cwd().name,
            "project_types": sorted(project_types) if project_types else [],
            "last_assessed": None,
            "assessment_tool_version": __version__,
        },
        "reporting": {
            "formats": ["text"],
            "output_dir": "./ethics-reports",
        },
    }

    # Write configuration
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]\u2713[/green] Created .ai-ethics.yaml with {framework} framework")

    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Create template files based on framework
    if framework == "unesco-2021":
        _create_unesco_templates(docs_dir)

    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Review and customize .ai-ethics.yaml")
    console.print("2. Fill out template files in docs/")
    console.print("3. Run [cyan]ethica check[/cyan] to verify compliance")


def _create_unesco_templates(docs_dir: Path) -> None:
    """Create UNESCO framework template files"""

    # Model / system card template
    model_card_path = docs_dir / "MODEL_CARD.md"
    if not model_card_path.exists():
        model_card_content = """# Model / System Card

## Overview

- **System Name**: [Your System Name]
- **Version**: [Version Number]
- **Date**: [Date]
- **Type**: [e.g., ML model, AI-powered API, recommendation system, LLM application]

## Intended Use

- **Primary Use Cases**: [Describe intended applications]
- **Out-of-Scope Uses**: [Describe inappropriate uses]
- **Target Users**: [Who will interact with this system]

## Architecture

- **System Components**: [Key technical components]
- **AI/ML Models Used**: [If applicable -- model type, provider, version]
- **Data Sources**: [What data does the system use]

## Performance and Limitations

- **Key Metrics**: [Accuracy, latency, throughput, etc.]
- **Known Limitations**: [Where the system may fail or underperform]
- **Edge Cases**: [Scenarios that may produce unexpected results]

## Ethical Considerations

- **Potential Harms**: [Who could be harmed and how]
- **Bias Considerations**: [Known or potential biases]
- **Mitigation Steps**: [What has been done to reduce risks]

## Monitoring

- **How is performance tracked?**: [Logging, dashboards, alerts]
- **Feedback mechanisms**: [How users can report issues]
"""
        model_card_path.write_text(model_card_content)
        console.print(f"[green]\u2713[/green] Created template: {model_card_path}")

    # Privacy impact assessment template
    privacy_path = docs_dir / "PRIVACY_IMPACT_ASSESSMENT.md"
    if not privacy_path.exists():
        privacy_content = """# Privacy Impact Assessment

## Data Collection

- **What data is collected?**: [Description]
- **How is data collected?**: [User input, APIs, tracking, etc.]
- **Purpose of collection**: [Justification]

## Data Usage

- **How is data used?**: [Training, inference, analytics, personalization]
- **Who has access?**: [Teams, third-party services]
- **Retention period**: [How long data is kept]

## Data Protection

- **Security measures**: [Encryption, access controls, network isolation]
- **Where is data stored?**: [Cloud provider, region, on-premise]
- **Third-party processors**: [Any external services that handle data]

## User Rights

- **Right to access**: [How users can access their data]
- **Right to deletion**: [How users can request deletion]
- **Right to opt out**: [How users can opt out of AI processing]

## Compliance

- **Applicable regulations**: [GDPR, CCPA, HIPAA, SOC2, etc.]
- **Data Protection Officer**: [Contact information]
- **Last Review**: [Date]
"""
        privacy_path.write_text(privacy_content)
        console.print(f"[green]\u2713[/green] Created template: {privacy_path}")
