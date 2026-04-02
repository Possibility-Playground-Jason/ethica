// ABOUTME: SVG badge generator for ethica compliance status
// ABOUTME: Produces shields.io-style badges (port of ethica/api/badge.py)

import type { CheckResults } from "./checks";

function textWidth(text: string): number {
  return Math.round(text.length * 6.5) + 10;
}

function generateBadgeSvg(
  label: string,
  message: string,
  color: string
): string {
  const labelW = textWidth(label);
  const messageW = textWidth(message);
  const totalW = labelW + messageW;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${totalW}" height="20" role="img" aria-label="${label}: ${message}">
  <title>${label}: ${message}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="${totalW}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="${labelW}" height="20" fill="#555"/>
    <rect x="${labelW}" width="${messageW}" height="20" fill="${color}"/>
    <rect width="${totalW}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="${labelW / 2}" y="15" fill="#010101" fill-opacity=".3">${label}</text>
    <text x="${labelW / 2}" y="14">${label}</text>
    <text aria-hidden="true" x="${labelW + messageW / 2}" y="15" fill="#010101" fill-opacity=".3">${message}</text>
    <text x="${labelW + messageW / 2}" y="14">${message}</text>
  </g>
</svg>`;
}

function pct(n: number): string {
  return `${Math.round(n * 100)}%`;
}

export function badgeFromResults(results: CheckResults): string {
  const passRate = results.pass_rate;
  const compliance = results.compliance;

  if (compliance) {
    if (compliance.meets_level) {
      return generateBadgeSvg("ethica", `${compliance.level} \u2713 ${pct(passRate)}`, "#4c1");
    }
    return generateBadgeSvg("ethica", `${compliance.level} \u2717 ${pct(passRate)}`, "#e05d44");
  }

  if (results.overall_status === "passed") {
    return generateBadgeSvg("ethica", `passing ${pct(passRate)}`, "#4c1");
  } else if (results.overall_status === "passed with warnings") {
    return generateBadgeSvg("ethica", `warnings ${pct(passRate)}`, "#dfb317");
  }
  return generateBadgeSvg("ethica", `failing ${pct(passRate)}`, "#e05d44");
}
