# ABOUTME: HTML report card generator for ethica compliance results
# ABOUTME: Produces a self-contained HTML page showing pass/fail status

"""
Generate a visual HTML report card from check results.
"""

from typing import Any

_STATUS_ICONS = {
    "passed": "\u2705",
    "failed": "\u274c",
    "skipped": "\u23ed\ufe0f",
    "passed with warnings": "\u26a0\ufe0f",
}

_SEVERITY_BADGES = {
    "error": '<span class="badge badge-error">required</span>',
    "warning": '<span class="badge badge-warning">recommended</span>',
    "info": '<span class="badge badge-info">info</span>',
}


def generate_report_html(results: dict[str, Any]) -> str:
    """Generate a self-contained HTML report card from check results."""

    framework_id = results.get("framework_id", "unknown")
    framework_version = results.get("framework_version", "")
    overall_status = results.get("overall_status", "unknown")
    pass_rate = results.get("pass_rate", 0.0)
    total = results.get("total_checks", 0)
    passed = results.get("checks_passed", 0)
    failed = results.get("checks_failed", 0)
    compliance = results.get("compliance", {})
    request = results.get("request", {})
    repo_url = request.get("repo_url", "")
    project_types = results.get("project_types", [])

    # Determine overall color
    if overall_status == "passed":
        status_color = "#16a34a"
        status_bg = "#f0fdf4"
    elif overall_status == "passed with warnings":
        status_color = "#ca8a04"
        status_bg = "#fefce8"
    else:
        status_color = "#dc2626"
        status_bg = "#fef2f2"

    compliance_html = ""
    if compliance:
        meets = compliance.get("meets_level", False)
        level = compliance.get("level", "")
        c_color = "#16a34a" if meets else "#dc2626"
        c_label = "MEETS" if meets else "DOES NOT MEET"
        compliance_html = f"""
        <div class="compliance-box" style="border-color: {c_color}">
            <span class="compliance-label" style="color: {c_color}">{c_label}</span>
            <span class="compliance-level">{level.upper()} compliance</span>
            <span class="compliance-detail">
                Required: {compliance.get('required_pass_rate', 0):.0%}
                &middot; Actual: {compliance.get('actual_pass_rate', 0):.0%}
            </span>
        </div>"""

    # Build principle sections
    principles_html = ""
    for principle in results.get("principles", []):
        pid = principle["id"]
        p_passed = principle.get("passed", 0)
        p_failed = principle.get("failed", 0)
        p_total = p_passed + p_failed + principle.get("skipped", 0)
        p_status = principle.get("status", "unknown")
        p_icon = _STATUS_ICONS.get(p_status, "")

        checks_html = ""
        for check in principle.get("checks", []):
            c_status = check.get("status", "unknown")
            c_icon = _STATUS_ICONS.get(c_status, "")
            c_name = check.get("name", "")
            c_message = check.get("message", "")
            c_severity = check.get("severity", "info")
            severity_badge = _SEVERITY_BADGES.get(c_severity, "")
            suggestion_html = ""
            if check.get("suggestion") and c_status == "failed":
                suggestion_html = (
                    f'<div class="suggestion">{check["suggestion"]}</div>'
                )

            checks_html += f"""
                <div class="check {'check-pass' if c_status == 'passed' else 'check-fail' if c_status == 'failed' else 'check-skip'}">
                    <div class="check-header">
                        <span class="check-icon">{c_icon}</span>
                        <span class="check-name">{c_name}</span>
                        {severity_badge}
                    </div>
                    <div class="check-message">{c_message}</div>
                    {suggestion_html}
                </div>"""

        principles_html += f"""
            <div class="principle">
                <div class="principle-header">
                    <span>{p_icon} {pid.replace('-', ' ').title()}</span>
                    <span class="principle-score">{p_passed}/{p_total}</span>
                </div>
                <div class="checks">{checks_html}</div>
            </div>"""

    project_info = ""
    if repo_url:
        project_info += f'<div class="meta-item"><strong>Repository:</strong> {repo_url}</div>'
    if project_types:
        project_info += f'<div class="meta-item"><strong>Detected:</strong> {", ".join(project_types)}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethica Report &mdash; {framework_id}</title>
<style>
  :root {{ --radius: 8px; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f8fafc; color: #1e293b; line-height: 1.5; padding: 2rem; }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  .header {{ text-align: center; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 1.5rem; font-weight: 600; }}
  .header .subtitle {{ color: #64748b; font-size: 0.9rem; }}
  .score-card {{
    background: {status_bg}; border: 2px solid {status_color};
    border-radius: var(--radius); padding: 1.5rem; text-align: center; margin-bottom: 1.5rem;
  }}
  .score-card .status {{ font-size: 1.75rem; font-weight: 700; color: {status_color}; }}
  .score-card .rate {{ font-size: 1rem; color: #475569; margin-top: 0.25rem; }}
  .compliance-box {{
    border: 2px solid; border-radius: var(--radius); padding: 1rem;
    text-align: center; margin-bottom: 1.5rem;
  }}
  .compliance-label {{ font-weight: 700; font-size: 1.1rem; }}
  .compliance-level {{ display: block; font-size: 0.9rem; color: #475569; }}
  .compliance-detail {{ display: block; font-size: 0.8rem; color: #94a3b8; }}
  .meta {{ background: #fff; border: 1px solid #e2e8f0; border-radius: var(--radius);
           padding: 1rem; margin-bottom: 1.5rem; font-size: 0.85rem; }}
  .meta-item {{ margin-bottom: 0.25rem; }}
  .principle {{
    background: #fff; border: 1px solid #e2e8f0; border-radius: var(--radius);
    margin-bottom: 1rem; overflow: hidden;
  }}
  .principle-header {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.75rem 1rem; background: #f1f5f9; font-weight: 600; font-size: 0.95rem;
    text-transform: capitalize;
  }}
  .principle-score {{ color: #64748b; font-weight: 400; font-size: 0.85rem; }}
  .checks {{ padding: 0.5rem 1rem; }}
  .check {{ padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9; }}
  .check:last-child {{ border-bottom: none; }}
  .check-header {{ display: flex; align-items: center; gap: 0.5rem; }}
  .check-icon {{ font-size: 1rem; }}
  .check-name {{ font-weight: 500; font-size: 0.9rem; }}
  .check-message {{ font-size: 0.8rem; color: #64748b; margin-left: 1.5rem; }}
  .suggestion {{
    font-size: 0.8rem; color: #0369a1; background: #f0f9ff;
    padding: 0.35rem 0.5rem; border-radius: 4px; margin: 0.25rem 0 0 1.5rem;
  }}
  .badge {{
    font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
    padding: 0.1rem 0.4rem; border-radius: 3px;
  }}
  .badge-error {{ background: #fef2f2; color: #dc2626; }}
  .badge-warning {{ background: #fffbeb; color: #d97706; }}
  .badge-info {{ background: #f0f9ff; color: #0284c7; }}
  .footer {{ text-align: center; color: #94a3b8; font-size: 0.75rem; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Ethica Report Card</h1>
    <div class="subtitle">{framework_id} v{framework_version}</div>
  </div>

  <div class="score-card">
    <div class="status">{_STATUS_ICONS.get(overall_status, '')} {overall_status.upper()}</div>
    <div class="rate">{passed}/{total} checks passed ({pass_rate:.0%})</div>
  </div>

  {compliance_html}

  <div class="meta">{project_info}</div>

  {principles_html}

  <div class="footer">
    Generated by Ethica &middot; AI Ethics Compliance Checking
  </div>
</div>
</body>
</html>"""
