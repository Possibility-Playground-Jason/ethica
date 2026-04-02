// ABOUTME: Cloudflare Worker entry point for ethica API
// ABOUTME: Hono-based HTTP API that mirrors the FastAPI endpoints using GitHub API instead of git clone

import { Hono } from "hono";
import { cors } from "hono/cors";

import { fetchRepoSnapshot, parseRepoUrl } from "./github";
import { runChecks } from "./checks";
import { getFramework, listFrameworks } from "./frameworks";
import { badgeFromResults } from "./badge";
import { generateReportHtml } from "./report";

type Bindings = {
  GITHUB_TOKEN?: string;
};

const app = new Hono<{ Bindings: Bindings }>();

app.use("*", cors());

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

app.get("/health", (c) => {
  return c.json({ status: "ok", version: "0.1.0", runtime: "cloudflare-workers" });
});

// ---------------------------------------------------------------------------
// Frameworks
// ---------------------------------------------------------------------------

app.get("/frameworks", (c) => {
  return c.json(listFrameworks());
});

// ---------------------------------------------------------------------------
// Check (JSON)
// ---------------------------------------------------------------------------

interface CheckBody {
  repo_url: string;
  ref?: string;
  framework?: string;
  compliance_level?: string;
}

async function performCheck(body: CheckBody, token?: string) {
  const frameworkId = body.framework || "unesco-2021";
  const complianceLevel = body.compliance_level || "standard";

  const framework = getFramework(frameworkId);
  if (!framework) {
    return { error: `Framework '${frameworkId}' not found`, status: 404 };
  }

  const ref = parseRepoUrl(body.repo_url);
  if (body.ref) ref.ref = body.ref;

  const snapshot = await fetchRepoSnapshot(ref, token);
  const results = await runChecks(
    framework,
    snapshot,
    body.repo_url,
    body.ref || null,
    complianceLevel,
    token
  );

  return results;
}

app.post("/check", async (c) => {
  try {
    const body = await c.req.json<CheckBody>();
    if (!body.repo_url) {
      return c.json({ error: "repo_url is required" }, 400);
    }

    const results = await performCheck(body, c.env.GITHUB_TOKEN);
    if ("error" in results) {
      return c.json(
        { detail: (results as { error: string }).error },
        (results as { status: number }).status as 404
      );
    }
    return c.json(results);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return c.json({ detail: message }, 500);
  }
});

// ---------------------------------------------------------------------------
// Check (HTML report)
// ---------------------------------------------------------------------------

app.post("/check/report", async (c) => {
  try {
    const body = await c.req.json<CheckBody>();
    if (!body.repo_url) {
      return c.json({ error: "repo_url is required" }, 400);
    }

    const results = await performCheck(body, c.env.GITHUB_TOKEN);
    if ("error" in results) {
      return c.json(
        { detail: (results as { error: string }).error },
        (results as { status: number }).status as 404
      );
    }
    const html = generateReportHtml(results);
    return c.html(html);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return c.json({ detail: message }, 500);
  }
});

// ---------------------------------------------------------------------------
// Check (SVG badge)
// ---------------------------------------------------------------------------

app.post("/check/badge", async (c) => {
  try {
    const body = await c.req.json<CheckBody>();
    if (!body.repo_url) {
      return c.json({ error: "repo_url is required" }, 400);
    }

    const results = await performCheck(body, c.env.GITHUB_TOKEN);
    if ("error" in results) {
      return c.json(
        { detail: (results as { error: string }).error },
        (results as { status: number }).status as 404
      );
    }
    const svg = badgeFromResults(results);
    return new Response(svg, {
      headers: {
        "Content-Type": "image/svg+xml",
        "Cache-Control": "no-cache, max-age=0",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return c.json({ detail: message }, 500);
  }
});

// ---------------------------------------------------------------------------
// GET badge shorthand — works as a plain image URL in READMEs
// ---------------------------------------------------------------------------

const GITHUB_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

app.get("/badge/:owner/:repo", async (c) => {
  const owner = c.req.param("owner");
  const repo = c.req.param("repo");
  const slug = `${owner}/${repo}`;

  if (!GITHUB_RE.test(slug)) {
    return c.json({ detail: "Invalid owner/repo format" }, 400);
  }

  const ref = c.req.query("ref");
  const framework = c.req.query("framework") || "unesco-2021";
  const level = c.req.query("level") || "standard";

  try {
    const results = await performCheck(
      {
        repo_url: `https://github.com/${slug}.git`,
        ref: ref || undefined,
        framework,
        compliance_level: level,
      },
      c.env.GITHUB_TOKEN
    );

    if ("error" in results) {
      return c.json(
        { detail: (results as { error: string }).error },
        (results as { status: number }).status as 404
      );
    }

    const svg = badgeFromResults(results);
    return new Response(svg, {
      headers: {
        "Content-Type": "image/svg+xml",
        "Cache-Control": "public, max-age=300, s-maxage=300",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return c.json({ detail: message }, 500);
  }
});

export default app;
