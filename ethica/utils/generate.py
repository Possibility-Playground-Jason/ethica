# ABOUTME: Generates pre-filled model/system card from project introspection
# ABOUTME: Produces Markdown documentation ready for human review and editing

"""
Generate a pre-filled Model Card or System Card from project metadata.
"""

from typing import Any


def generate_card(profile: dict[str, Any]) -> str:
    """
    Generate a Markdown model/system card pre-filled from the project profile.

    Sections that can't be inferred are left with [TODO] placeholders
    so the developer knows exactly what to fill in.
    """
    name = profile.get("project_name", "My Project")
    desc = profile.get("description", "")
    date_str = profile.get("date", "")
    project_types = profile.get("project_types", [])
    ai_libs = profile.get("ai_libraries", [])
    explain_libs = profile.get("explainability_libraries", [])
    fairness_libs = profile.get("fairness_libraries", [])
    deps = profile.get("dependencies", [])
    has_tests = profile.get("has_tests", False)
    has_ci = profile.get("has_ci", False)
    license_str = profile.get("license", "")
    contributors = profile.get("contributors", [])
    repo_url = profile.get("repo_url", "")

    # Decide card type based on what we find
    has_ml = bool(ai_libs)
    card_title = "Model Card" if has_ml else "System Card"

    sections: list[str] = []

    # --- Header ---
    sections.append(f"# {card_title}: {name}\n")

    # --- Overview ---
    overview_lines = ["## Overview\n"]
    overview_lines.append(f"- **Name**: {name}")
    if desc:
        overview_lines.append(f"- **Description**: {desc}")
    else:
        overview_lines.append("- **Description**: [TODO: One-sentence description of what this system does]")
    overview_lines.append(f"- **Date**: {date_str}")
    if project_types:
        overview_lines.append(f"- **Tech Stack**: {', '.join(project_types)}")
    if ai_libs:
        overview_lines.append(f"- **AI/ML Frameworks**: {', '.join(ai_libs)}")
    if license_str:
        overview_lines.append(f"- **License**: {license_str}")
    if repo_url:
        overview_lines.append(f"- **Repository**: {repo_url}")
    sections.append("\n".join(overview_lines))

    # --- Intended Use ---
    sections.append("""## Intended Use

- **Primary Use Cases**: [TODO: What is this system designed to do?]
- **Target Users**: [TODO: Who will use this system?]
- **Out-of-Scope Uses**: [TODO: What should this system NOT be used for?]""")

    # --- Architecture (if AI libs detected) ---
    if has_ml:
        arch_lines = ["## Architecture\n"]
        arch_lines.append(f"- **AI/ML Libraries**: {', '.join(ai_libs)}")
        arch_lines.append("- **Model Type**: [TODO: e.g., transformer, CNN, gradient boosting, LLM API wrapper]")
        arch_lines.append("- **Training Data**: [TODO: Describe training data sources, or note if using a pre-trained model/API]")
        arch_lines.append("- **Input Format**: [TODO: What data does the system accept?]")
        arch_lines.append("- **Output Format**: [TODO: What does the system return?]")
        sections.append("\n".join(arch_lines))
    else:
        sections.append("""## Architecture

- **System Components**: [TODO: Key technical components]
- **Data Sources**: [TODO: What data does the system use?]
- **External Services**: [TODO: Any third-party APIs or AI services used?]""")

    # --- Performance ---
    sections.append("""## Performance and Limitations

- **Key Metrics**: [TODO: Accuracy, latency, throughput, or other relevant metrics]
- **Known Limitations**: [TODO: Where does the system underperform or fail?]
- **Edge Cases**: [TODO: Scenarios that may produce unexpected results]""")

    # --- Ethical Considerations ---
    ethical_lines = ["## Ethical Considerations\n"]
    ethical_lines.append("- **Potential Harms**: [TODO: Who could be harmed by this system and how?]")
    ethical_lines.append("- **Bias Considerations**: [TODO: Known or potential biases in data or outputs]")
    ethical_lines.append("- **Mitigation Steps**: [TODO: What has been done to reduce risks?]")

    if explain_libs:
        ethical_lines.append(f"\n### Explainability\n")
        ethical_lines.append(f"This project uses **{', '.join(explain_libs)}** for model interpretability.")
        ethical_lines.append("- **How explanations are surfaced**: [TODO: Are explanations available to end users?]")
    else:
        ethical_lines.append(f"\n### Explainability\n")
        ethical_lines.append("- **Explainability approach**: [TODO: How can users understand the system's decisions?]")

    if fairness_libs:
        ethical_lines.append(f"\n### Fairness\n")
        ethical_lines.append(f"This project uses **{', '.join(fairness_libs)}** for fairness evaluation.")
        ethical_lines.append("- **Protected attributes tested**: [TODO: e.g., gender, race, age]")
        ethical_lines.append("- **Fairness metrics used**: [TODO: e.g., demographic parity, equalized odds]")
    else:
        ethical_lines.append(f"\n### Fairness\n")
        ethical_lines.append("- **Fairness evaluation**: [TODO: How is fairness measured? Consider adding fairlearn, aif360, or similar]")

    sections.append("\n".join(ethical_lines))

    # --- Data & Privacy ---
    sections.append("""## Data and Privacy

- **Data Collected**: [TODO: What user or system data is processed?]
- **Data Retention**: [TODO: How long is data kept?]
- **Privacy Protections**: [TODO: Encryption, anonymization, access controls]
- **Applicable Regulations**: [TODO: GDPR, CCPA, HIPAA, etc.]""")

    # --- Monitoring ---
    monitoring_lines = ["## Monitoring and Maintenance\n"]
    if has_ci:
        monitoring_lines.append("- **CI/CD**: Automated pipeline detected in this project")
    else:
        monitoring_lines.append("- **CI/CD**: [TODO: Set up continuous integration for automated testing]")
    if has_tests:
        monitoring_lines.append("- **Testing**: Test suite detected in this project")
    else:
        monitoring_lines.append("- **Testing**: [TODO: Add tests for model/system behavior]")
    monitoring_lines.append("- **Drift Monitoring**: [TODO: How is model or system performance tracked over time?]")
    monitoring_lines.append("- **Incident Response**: [TODO: What happens when the system fails or produces harmful output?]")
    monitoring_lines.append("- **Update Cadence**: [TODO: How often is the system re-evaluated?]")
    sections.append("\n".join(monitoring_lines))

    # --- Contributors ---
    if contributors:
        contrib_lines = ["## Contributors\n"]
        for name in contributors[:10]:
            contrib_lines.append(f"- {name}")
        if len(contributors) > 10:
            contrib_lines.append(f"- ... and {len(contributors) - 10} more")
        sections.append("\n".join(contrib_lines))

    # --- Footer ---
    sections.append("""---

*This card was auto-generated by [Ethica](https://github.com/shellen/ethica) and should be reviewed and completed by the project team. Sections marked [TODO] need human input.*""")

    return "\n\n".join(sections) + "\n"
