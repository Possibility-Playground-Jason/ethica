# ABOUTME: SVG badge generator for ethica compliance status
# ABOUTME: Produces shields.io-style badges showing pass/fail and score

"""
Generate SVG compliance badges.
"""

from typing import Any


def _text_width(text: str) -> int:
    """Rough pixel width for Verdana 11px (shields.io convention)."""
    return int(len(text) * 6.5) + 10


def generate_badge_svg(
    label: str,
    message: str,
    color: str,
) -> str:
    """Generate a shields.io-style flat SVG badge."""
    label_w = _text_width(label)
    message_w = _text_width(message)
    total_w = label_w + message_w

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{label}: {message}">
  <title>{label}: {message}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total_w}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="20" fill="#555"/>
    <rect x="{label_w}" width="{message_w}" height="20" fill="{color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="{label_w / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_w / 2}" y="14">{label}</text>
    <text aria-hidden="true" x="{label_w + message_w / 2}" y="15" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{label_w + message_w / 2}" y="14">{message}</text>
  </g>
</svg>"""


def badge_from_results(results: dict[str, Any], level: str = "") -> str:
    """Generate an SVG badge from check results."""
    overall = results.get("overall_status", "unknown")
    pass_rate = results.get("pass_rate", 0.0)
    compliance = results.get("compliance", {})

    if compliance:
        meets = compliance.get("meets_level", False)
        lvl = compliance.get("level", "standard")
        if meets:
            return generate_badge_svg("ethica", f"{lvl} ✓ {pass_rate:.0%}", "#4c1")
        else:
            return generate_badge_svg("ethica", f"{lvl} ✗ {pass_rate:.0%}", "#e05d44")

    if overall == "passed":
        return generate_badge_svg("ethica", f"passing {pass_rate:.0%}", "#4c1")
    elif overall == "passed with warnings":
        return generate_badge_svg("ethica", f"warnings {pass_rate:.0%}", "#dfb317")
    else:
        return generate_badge_svg("ethica", f"failing {pass_rate:.0%}", "#e05d44")
