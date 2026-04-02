// ABOUTME: HTML report card generator for ethica compliance results
// ABOUTME: Produces a self-contained HTML page (port of ethica/api/report.py)

import type { CheckResults } from "./checks";

const STATUS_ICONS: Record<string, string> = {
  passed: "\u2705",
  failed: "\u274c",
  skipped: "\u23ed\ufe0f",
  "passed with warnings": "\u26a0\ufe0f",
};

const SEVERITY_BADGES: Record<string, string> = {
  error: '<span class="badge badge-error">required</span>',
  warning: '<span class="badge badge-warning">recommended</span>',
  info: '<span class="badge badge-info">info</span>',
};

export function generateReportHtml(results: CheckResults): string {
  const frameworkId = results.framework_id;
  const frameworkVersion = results.framework_version;
  const overallStatus = results.overall_status;
  const passRate = results.pass_rate;
  const total = results.total_checks;
  const passed = results.checks_passed;
  const compliance = results.compliance;
  const repoUrl = results.request.repo_url;
  const projectTypes = results.project_types;

  let statusColor: string;
  let statusBg: string;
  if (overallStatus === "passed") {
    statusColor = "#16a34a";
    statusBg = "#f0fdf4";
  } else if (overallStatus === "passed with warnings") {
    statusColor = "#ca8a04";
    statusBg = "#fefce8";
  } else {
    statusColor = "#dc2626";
    statusBg = "#fef2f2";
  }

  let complianceHtml = "";
  if (compliance) {
    const meets = compliance.meets_level;
    const cColor = meets ? "#16a34a" : "#dc2626";
    const cLabel = meets ? "MEETS" : "DOES NOT MEET";
    complianceHtml = `
        <div class="compliance-box" style="border-color: ${cColor}">
            <span class="compliance-label" style="color: ${cColor}">${cLabel}</span>
            <span class="compliance-level">${compliance.level.toUpperCase()} compliance</span>
            <span class="compliance-detail">
                Required: ${Math.round(compliance.required_pass_rate * 100)}%
                &middot; Actual: ${Math.round(compliance.actual_pass_rate * 100)}%
            </span>
        </div>`;
  }

  let principlesHtml = "";
  for (const principle of results.principles) {
    const pid = principle.id;
    const pPassed = principle.passed;
    const pTotal = pPassed + principle.failed + principle.skipped;
    const pStatus = principle.status;
    const pIcon = STATUS_ICONS[pStatus] || "";

    let checksHtml = "";
    for (const check of principle.checks) {
      const cStatus = check.status;
      const cIcon = STATUS_ICONS[cStatus] || "";
      const severityBadge = SEVERITY_BADGES[check.severity] || "";
      let suggestionHtml = "";
      if (check.suggestion && cStatus === "failed") {
        suggestionHtml = `<div class="suggestion">${check.suggestion}</div>`;
      }

      const checkClass =
        cStatus === "passed"
          ? "check-pass"
          : cStatus === "failed"
            ? "check-fail"
            : "check-skip";

      checksHtml += `
                <div class="check ${checkClass}">
                    <div class="check-header">
                        <span class="check-icon">${cIcon}</span>
                        <span class="check-name">${check.name}</span>
                        ${severityBadge}
                    </div>
                    <div class="check-message">${check.message}</div>
                    ${suggestionHtml}
                </div>`;
    }

    const titleCase = pid
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

    principlesHtml += `
            <div class="principle">
                <div class="principle-header">
                    <span>${pIcon} ${titleCase}</span>
                    <span class="principle-score">${pPassed}/${pTotal}</span>
                </div>
                <div class="checks">${checksHtml}</div>
            </div>`;
  }

  let projectInfo = "";
  if (repoUrl) {
    projectInfo += `<div class="meta-item"><strong>Repository:</strong> ${repoUrl}</div>`;
  }
  if (projectTypes.length > 0) {
    projectInfo += `<div class="meta-item"><strong>Detected:</strong> ${projectTypes.join(", ")}</div>`;
  }

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethica Report &mdash; ${frameworkId}</title>
<style>
  :root { --radius: 8px; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f8fafc; color: #1e293b; line-height: 1.5; padding: 2rem; }
  .container { max-width: 720px; margin: 0 auto; }
  .header { text-align: center; margin-bottom: 2rem; }
  .header h1 { font-size: 1.5rem; font-weight: 600; }
  .header .subtitle { color: #64748b; font-size: 0.9rem; }
  .score-card {
    background: ${statusBg}; border: 2px solid ${statusColor};
    border-radius: var(--radius); padding: 1.5rem; text-align: center; margin-bottom: 1.5rem;
  }
  .score-card .status { font-size: 1.75rem; font-weight: 700; color: ${statusColor}; }
  .score-card .rate { font-size: 1rem; color: #475569; margin-top: 0.25rem; }
  .compliance-box {
    border: 2px solid; border-radius: var(--radius); padding: 1rem;
    text-align: center; margin-bottom: 1.5rem;
  }
  .compliance-label { font-weight: 700; font-size: 1.1rem; }
  .compliance-level { display: block; font-size: 0.9rem; color: #475569; }
  .compliance-detail { display: block; font-size: 0.8rem; color: #94a3b8; }
  .meta { background: #fff; border: 1px solid #e2e8f0; border-radius: var(--radius);
           padding: 1rem; margin-bottom: 1.5rem; font-size: 0.85rem; }
  .meta-item { margin-bottom: 0.25rem; }
  .principle {
    background: #fff; border: 1px solid #e2e8f0; border-radius: var(--radius);
    margin-bottom: 1rem; overflow: hidden;
  }
  .principle-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.75rem 1rem; background: #f1f5f9; font-weight: 600; font-size: 0.95rem;
    text-transform: capitalize;
  }
  .principle-score { color: #64748b; font-weight: 400; font-size: 0.85rem; }
  .checks { padding: 0.5rem 1rem; }
  .check { padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9; }
  .check:last-child { border-bottom: none; }
  .check-header { display: flex; align-items: center; gap: 0.5rem; }
  .check-icon { font-size: 1rem; }
  .check-name { font-weight: 500; font-size: 0.9rem; }
  .check-message { font-size: 0.8rem; color: #64748b; margin-left: 1.5rem; }
  .suggestion {
    font-size: 0.8rem; color: #0369a1; background: #f0f9ff;
    padding: 0.35rem 0.5rem; border-radius: 4px; margin: 0.25rem 0 0 1.5rem;
  }
  .badge {
    font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
    padding: 0.1rem 0.4rem; border-radius: 3px;
  }
  .badge-error { background: #fef2f2; color: #dc2626; }
  .badge-warning { background: #fffbeb; color: #d97706; }
  .badge-info { background: #f0f9ff; color: #0284c7; }
  .footer { text-align: center; color: #94a3b8; font-size: 0.75rem; margin-top: 2rem; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Ethica Report Card</h1>
    <div class="subtitle">${frameworkId} v${frameworkVersion}</div>
  </div>

  <div class="score-card">
    <div class="status">${STATUS_ICONS[overallStatus] || ""} ${overallStatus.toUpperCase()}</div>
    <div class="rate">${passed}/${total} checks passed (${Math.round(passRate * 100)}%)</div>
  </div>

  ${complianceHtml}

  <div class="meta">${projectInfo}</div>

  ${principlesHtml}

  <div class="footer">
    Generated by Ethica &middot; AI Ethics Compliance Checking
  </div>
</div>
</body>
</html>`;
}
