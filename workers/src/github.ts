// ABOUTME: GitHub API client for fetching repository contents without git clone
// ABOUTME: Uses Trees API for file listings and Contents API for file content

export interface RepoRef {
  owner: string;
  repo: string;
  ref?: string;
}

export interface TreeEntry {
  path: string;
  type: "blob" | "tree";
  sha: string;
  size?: number;
}

export interface RepoSnapshot {
  /** All file paths in the repo (relative to root) */
  files: Set<string>;
  /** All directory paths */
  dirs: Set<string>;
  /** Fetched file contents (populated on demand) */
  contents: Map<string, string>;
  /** Repo metadata */
  ref: RepoRef;
  /** Default branch (resolved from the API) */
  defaultBranch: string;
}

const GITHUB_API = "https://api.github.com";

/**
 * Parse a GitHub clone URL into owner/repo.
 * Handles https://github.com/owner/repo.git and owner/repo shorthand.
 */
export function parseRepoUrl(url: string): RepoRef {
  // Try full URL first
  const urlMatch = url.match(
    /github\.com[/:]([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+?)(?:\.git)?$/
  );
  if (urlMatch) {
    return { owner: urlMatch[1]!, repo: urlMatch[2]! };
  }

  // Try owner/repo shorthand
  const shortMatch = url.match(/^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);
  if (shortMatch) {
    return { owner: shortMatch[1]!, repo: shortMatch[2]! };
  }

  throw new Error(`Cannot parse GitHub URL: ${url}`);
}

function headers(token?: string): Record<string, string> {
  const h: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "User-Agent": "ethica-worker/0.1",
  };
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  }
  return h;
}

async function ghFetch(
  path: string,
  token?: string
): Promise<Response> {
  const resp = await fetch(`${GITHUB_API}${path}`, {
    headers: headers(token),
  });
  if (!resp.ok) {
    const body = await resp.text();
    if (resp.status === 403 && body.includes("rate limit")) {
      throw new Error(
        "GitHub API rate limit exceeded. This service is currently using unauthenticated requests (60/hr). Please try again later."
      );
    }
    if (resp.status === 404) {
      throw new Error(
        `Repository not found: ${path.replace(/^\/repos\//, "").split("/git/")[0]}. Make sure the repository exists and is public.`
      );
    }
    throw new Error(
      `GitHub API ${resp.status}: ${path} — ${body.slice(0, 200)}`
    );
  }
  return resp;
}

/**
 * Get the default branch for a repository.
 */
async function getDefaultBranch(
  ref: RepoRef,
  token?: string
): Promise<string> {
  const resp = await ghFetch(
    `/repos/${ref.owner}/${ref.repo}`,
    token
  );
  const data = (await resp.json()) as { default_branch: string };
  return data.default_branch;
}

/**
 * Fetch the full file tree for a repo at a given ref.
 * Uses the Git Trees API with recursive=1 for a single API call.
 */
export async function fetchRepoSnapshot(
  ref: RepoRef,
  token?: string
): Promise<RepoSnapshot> {
  const branch = ref.ref || (await getDefaultBranch(ref, token));

  const resp = await ghFetch(
    `/repos/${ref.owner}/${ref.repo}/git/trees/${branch}?recursive=1`,
    token
  );
  const data = (await resp.json()) as {
    tree: TreeEntry[];
    truncated: boolean;
  };

  const files = new Set<string>();
  const dirs = new Set<string>();

  for (const entry of data.tree) {
    if (entry.type === "blob") {
      files.add(entry.path);
    } else if (entry.type === "tree") {
      dirs.add(entry.path);
    }
  }

  // Always add root-level implied dirs
  dirs.add(".");

  return {
    files,
    dirs,
    contents: new Map(),
    ref,
    defaultBranch: branch,
  };
}

/**
 * Fetch a single file's text content from the repo.
 * Caches in the snapshot for reuse.
 */
export async function fetchFileContent(
  snapshot: RepoSnapshot,
  path: string,
  token?: string
): Promise<string | null> {
  if (snapshot.contents.has(path)) {
    return snapshot.contents.get(path)!;
  }

  if (!snapshot.files.has(path)) {
    return null;
  }

  try {
    const resp = await fetch(
      `${GITHUB_API}/repos/${snapshot.ref.owner}/${snapshot.ref.repo}/contents/${path}?ref=${snapshot.defaultBranch}`,
      {
        headers: {
          ...headers(token),
          Accept: "application/vnd.github.raw+json",
        },
      }
    );
    if (!resp.ok) return null;

    const text = await resp.text();
    snapshot.contents.set(path, text);
    return text;
  } catch {
    return null;
  }
}

/**
 * Fetch multiple files in parallel. Returns a map of path -> content.
 */
export async function fetchFiles(
  snapshot: RepoSnapshot,
  paths: string[],
  token?: string
): Promise<Map<string, string>> {
  const results = new Map<string, string>();
  const toFetch = paths.filter(
    (p) => snapshot.files.has(p) && !snapshot.contents.has(p)
  );

  await Promise.all(
    toFetch.map(async (path) => {
      const content = await fetchFileContent(snapshot, path, token);
      if (content !== null) {
        results.set(path, content);
      }
    })
  );

  // Include already-cached
  for (const p of paths) {
    if (snapshot.contents.has(p)) {
      results.set(p, snapshot.contents.get(p)!);
    }
  }

  return results;
}
