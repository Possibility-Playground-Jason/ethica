// ABOUTME: Check engine for running compliance checks against a GitHub repo snapshot
// ABOUTME: Ports the Python check logic to TypeScript using the GitHub API instead of filesystem

import { type RepoSnapshot, fetchFileContent, fetchFiles } from "./github";
import {
  type CheckSpec,
  type FrameworkSpec,
  type ProviderInfo,
  PROVIDERS,
} from "./frameworks";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CheckResult {
  id: string;
  name: string;
  status: "passed" | "failed" | "skipped";
  message: string;
  severity: "error" | "warning" | "info";
  suggestion: string | null;
}

export interface PrincipleResult {
  id: string;
  checks: CheckResult[];
  passed: number;
  failed: number;
  skipped: number;
  status: "passed" | "failed" | "skipped";
}

export interface CheckResults {
  framework_id: string;
  framework_version: string;
  principles: PrincipleResult[];
  total_checks: number;
  checks_passed: number;
  checks_failed: number;
  checks_skipped: number;
  pass_rate: number;
  overall_status: string;
  overall_status_color: string;
  project_types: string[];
  request: {
    repo_url: string;
    ref: string | null;
    framework: string;
    compliance_level: string;
  };
  compliance?: {
    level: string;
    required_pass_rate: number;
    actual_pass_rate: number;
    meets_level: boolean;
  };
}

// ---------------------------------------------------------------------------
// Project type detection (mirrors ethica/utils/detect.py)
// ---------------------------------------------------------------------------

const PROJECT_MARKERS: Record<string, string> = {
  "package.json": "nodejs",
  "requirements.txt": "python",
  "pyproject.toml": "python",
  "setup.py": "python",
  "setup.cfg": "python",
  "go.mod": "go",
  "Cargo.toml": "rust",
  "Gemfile": "ruby",
  "pom.xml": "java",
  "build.gradle": "java",
  "build.gradle.kts": "kotlin",
  "composer.json": "php",
  "mix.exs": "elixir",
  "Package.swift": "swift",
};

function detectProjectTypes(snapshot: RepoSnapshot): string[] {
  const types = new Set<string>();
  for (const [marker, projectType] of Object.entries(PROJECT_MARKERS)) {
    if (snapshot.files.has(marker)) {
      types.add(projectType);
    }
  }
  return [...types].sort();
}

// ---------------------------------------------------------------------------
// Individual check runners
// ---------------------------------------------------------------------------

function runFileExistsCheck(
  spec: CheckSpec,
  snapshot: RepoSnapshot
): CheckResult {
  const paths = (spec.config.paths as string[]) || [];

  if (paths.length === 0) {
    return {
      id: spec.id,
      name: spec.name,
      status: "skipped",
      message: "No paths configured for check",
      severity: spec.severity,
      suggestion: null,
    };
  }

  for (const p of paths) {
    // Check both files and dirs (e.g. .git is a directory)
    if (snapshot.files.has(p) || snapshot.dirs.has(p)) {
      return {
        id: spec.id,
        name: spec.name,
        status: "passed",
        message: `Found required file/directory at ${p}`,
        severity: spec.severity,
        suggestion: null,
      };
    }
  }

  const pathsFormatted = paths.join(", ");
  let suggestion = `Create one of: ${pathsFormatted}`;
  if (spec.help_url) {
    suggestion += `\nSee: ${spec.help_url}`;
  }

  return {
    id: spec.id,
    name: spec.name,
    status: "failed",
    message: `Required file/directory not found. Expected one of: ${pathsFormatted}`,
    severity: spec.severity,
    suggestion,
  };
}

// ---------------------------------------------------------------------------
// Dependency parsing (mirrors ethica/checks/dependency_checks.py)
// ---------------------------------------------------------------------------

function parseRequirementsTxt(content: string): Set<string> {
  const deps = new Set<string>();
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([a-zA-Z0-9_-]+)/);
    if (match) deps.add(match[1]!.toLowerCase());
  }
  return deps;
}

function parsePyprojectToml(content: string): Set<string> {
  const deps = new Set<string>();
  let inSection = false;
  let inArray = false;

  for (const line of content.split("\n")) {
    const stripped = line.trim();

    if (stripped.startsWith("[")) {
      inArray = false;
      inSection = stripped.toLowerCase().includes("dependencies");
      continue;
    }

    if (/(?:dev-)?dependencies\s*=\s*\[/.test(stripped)) {
      inArray = true;
    }

    if (inArray) {
      const matches = stripped.matchAll(/"([a-zA-Z0-9@/_-]+)[>=<["]?/g);
      for (const m of matches) {
        deps.add(m[1]!.toLowerCase());
      }
      if (stripped.includes("]")) inArray = false;
    }

    if (inSection && stripped.includes("=")) {
      const match = stripped.match(/^"?([a-zA-Z0-9_-]+)"?\s*=/);
      if (match) deps.add(match[1]!.toLowerCase());
    }
  }
  return deps;
}

function parseSetupPy(content: string): Set<string> {
  const deps = new Set<string>();
  const matches = content.matchAll(
    /install_requires\s*=\s*\[([\s\S]*?)\]/g
  );
  for (const m of matches) {
    const packages = m[1]!.matchAll(/"([a-zA-Z0-9_-]+)[>=<]?/g);
    for (const pkg of packages) {
      deps.add(pkg[1]!.toLowerCase());
    }
  }
  return deps;
}

function parsePackageJson(content: string): Set<string> {
  const deps = new Set<string>();
  try {
    const data = JSON.parse(content) as Record<string, unknown>;
    for (const key of ["dependencies", "devDependencies", "peerDependencies"]) {
      const section = data[key];
      if (section && typeof section === "object") {
        for (const name of Object.keys(section as Record<string, unknown>)) {
          deps.add(name.toLowerCase());
        }
      }
    }
  } catch {
    // ignore parse errors
  }
  return deps;
}

async function getProjectDependencies(
  snapshot: RepoSnapshot,
  token?: string
): Promise<Set<string>> {
  const deps = new Set<string>();

  // Determine which dep files exist
  const depFiles = [
    "requirements.txt",
    "requirements-dev.txt",
    "requirements/base.txt",
    "requirements/dev.txt",
    "pyproject.toml",
    "setup.py",
    "package.json",
  ].filter((f) => snapshot.files.has(f));

  const contents = await fetchFiles(snapshot, depFiles, token);

  for (const [path, content] of contents) {
    let parsed: Set<string>;
    if (path.endsWith("requirements.txt") || path.includes("requirements/")) {
      parsed = parseRequirementsTxt(content);
    } else if (path === "pyproject.toml") {
      parsed = parsePyprojectToml(content);
    } else if (path === "setup.py") {
      parsed = parseSetupPy(content);
    } else if (path === "package.json") {
      parsed = parsePackageJson(content);
    } else {
      continue;
    }
    for (const d of parsed) deps.add(d);
  }

  return deps;
}

async function runDependencyCheck(
  spec: CheckSpec,
  snapshot: RepoSnapshot,
  token?: string
): Promise<CheckResult> {
  const packages = (spec.config.packages as string[]) || [];
  const requireAny = (spec.config.require_any as boolean) ?? true;
  const requireAll = (spec.config.require_all as boolean) ?? false;

  if (packages.length === 0) {
    return {
      id: spec.id,
      name: spec.name,
      status: "skipped",
      message: "No packages configured for check",
      severity: spec.severity,
      suggestion: null,
    };
  }

  const declaredDeps = await getProjectDependencies(snapshot, token);
  const found = packages.filter((pkg) => declaredDeps.has(pkg.toLowerCase()));

  if (requireAll) {
    if (found.length === packages.length) {
      return {
        id: spec.id,
        name: spec.name,
        status: "passed",
        message: `All required packages found: ${found.join(", ")}`,
        severity: spec.severity,
        suggestion: null,
      };
    }
    const missing = packages.filter(
      (pkg) => !declaredDeps.has(pkg.toLowerCase())
    );
    return {
      id: spec.id,
      name: spec.name,
      status: "failed",
      message: `Missing required packages: ${missing.join(", ")}`,
      severity: spec.severity,
      suggestion: `Install: ${missing.join(", ")}`,
    };
  }

  // require_any (default)
  if (found.length > 0) {
    return {
      id: spec.id,
      name: spec.name,
      status: "passed",
      message: `Found package(s): ${found.join(", ")}`,
      severity: spec.severity,
      suggestion: null,
    };
  }

  const packagesFormatted = packages.join(", ");
  return {
    id: spec.id,
    name: spec.name,
    status: "failed",
    message: `No required packages found. Expected at least one of: ${packagesFormatted}`,
    severity: spec.severity,
    suggestion: `Install one of: ${packagesFormatted}`,
  };
}

// ---------------------------------------------------------------------------
// Provider check (mirrors ethica/checks/provider_checks.py)
// ---------------------------------------------------------------------------

const CODE_EXTENSIONS = [
  ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs",
  ".go", ".rs", ".java", ".kt", ".rb",
];

const SKIP_DIRS = [
  "node_modules", "venv", ".venv", "__pycache__",
  ".git", "dist", "build",
];

async function runProviderCheck(
  spec: CheckSpec,
  snapshot: RepoSnapshot,
  token?: string
): Promise<CheckResult> {
  // Collect source files to scan (limit to keep within Worker CPU limits)
  const sourceFiles: string[] = [];
  for (const filePath of snapshot.files) {
    if (SKIP_DIRS.some((skip) => filePath.includes(skip))) continue;
    if (CODE_EXTENSIONS.some((ext) => filePath.endsWith(ext))) {
      sourceFiles.push(filePath);
    }
  }

  // Also include dependency manifests as fallback
  const depFiles = ["requirements.txt", "pyproject.toml", "package.json", "go.mod"];
  for (const f of depFiles) {
    if (snapshot.files.has(f) && !sourceFiles.includes(f)) {
      sourceFiles.push(f);
    }
  }

  if (sourceFiles.length === 0) {
    return {
      id: spec.id,
      name: spec.name,
      status: "skipped",
      message: "No source files found to scan",
      severity: spec.severity,
      suggestion: null,
    };
  }

  // Fetch contents (cap at 30 files to stay within limits)
  const filesToFetch = sourceFiles.slice(0, 30);
  const contents = await fetchFiles(snapshot, filesToFetch, token);

  // Concatenate all content (lowercase) for matching
  let allContent = "";
  for (const content of contents.values()) {
    allContent += content.slice(0, 50_000).toLowerCase() + "\n";
  }

  if (!allContent.trim()) {
    return {
      id: spec.id,
      name: spec.name,
      status: "skipped",
      message: "No AI model providers detected in source code",
      severity: spec.severity,
      suggestion: null,
    };
  }

  // Detect providers
  const detected = new Map<string, ProviderInfo>();

  for (const [providerId, provider] of Object.entries(PROVIDERS)) {
    for (const marker of provider.import_markers) {
      if (allContent.includes(marker.toLowerCase())) {
        detected.set(providerId, provider);
        break;
      }
    }
    if (!detected.has(providerId)) {
      for (const pattern of provider.model_id_patterns) {
        if (allContent.includes(pattern.toLowerCase())) {
          detected.set(providerId, provider);
          break;
        }
      }
    }
  }

  if (detected.size === 0) {
    return {
      id: spec.id,
      name: spec.name,
      status: "skipped",
      message: "No AI model providers detected in source code",
      severity: spec.severity,
      suggestion: null,
    };
  }

  const transparent: string[] = [];
  const opaque: string[] = [];

  for (const [, provider] of detected) {
    if (provider.publishes_system_cards) {
      transparent.push(
        `${provider.name} (system cards: ${provider.system_cards_url || "available"})`
      );
    } else {
      opaque.push(
        `${provider.name}: ${provider.notes || "No published system cards"}`
      );
    }
  }

  if (opaque.length > 0) {
    const parts = [`Found ${detected.size} AI provider(s).`];
    if (transparent.length > 0) {
      parts.push(`Providers with system cards: ${transparent.join(", ")}`);
    }
    parts.push(`Providers WITHOUT system cards: ${opaque.join("; ")}`);

    return {
      id: spec.id,
      name: spec.name,
      status: "failed",
      message: parts.join(" "),
      severity: spec.severity,
      suggestion:
        "Consider providers that publish system cards and safety evaluations. See https://www.anthropic.com/system-cards for an example.",
    };
  }

  const names = [...detected.values()].map((p) => p.name);
  return {
    id: spec.id,
    name: spec.name,
    status: "passed",
    message: `All detected AI providers publish system cards: ${names.join(", ")}`,
    severity: spec.severity,
    suggestion: null,
  };
}

// ---------------------------------------------------------------------------
// Check engine (mirrors ethica/core/checker.py)
// ---------------------------------------------------------------------------

export async function runChecks(
  framework: FrameworkSpec,
  snapshot: RepoSnapshot,
  repoUrl: string,
  ref: string | null,
  complianceLevel: string,
  token?: string
): Promise<CheckResults> {
  const principleMap = new Map<string, PrincipleResult>();

  for (const spec of framework.checks) {
    let result: CheckResult;

    switch (spec.type) {
      case "file-exists":
        result = runFileExistsCheck(spec, snapshot);
        break;
      case "dependency-check":
        result = await runDependencyCheck(spec, snapshot, token);
        break;
      case "provider-check":
        result = await runProviderCheck(spec, snapshot, token);
        break;
      default:
        continue;
    }

    if (!principleMap.has(spec.principle)) {
      principleMap.set(spec.principle, {
        id: spec.principle,
        checks: [],
        passed: 0,
        failed: 0,
        skipped: 0,
        status: "skipped",
      });
    }

    const principle = principleMap.get(spec.principle)!;
    principle.checks.push(result);

    if (result.status === "passed") principle.passed++;
    else if (result.status === "failed") principle.failed++;
    else principle.skipped++;
  }

  // Compute principle-level status
  for (const principle of principleMap.values()) {
    if (principle.failed > 0) principle.status = "failed";
    else if (principle.passed > 0) principle.status = "passed";
    else principle.status = "skipped";
  }

  const principles = [...principleMap.values()];
  const totalChecks = framework.checks.length;
  const totalPassed = principles.reduce((s, p) => s + p.passed, 0);
  const totalFailed = principles.reduce((s, p) => s + p.failed, 0);
  const totalSkipped = principles.reduce((s, p) => s + p.skipped, 0);
  const passRate = totalChecks > 0 ? totalPassed / totalChecks : 0;

  // Determine overall status
  let errorFailures = 0;
  for (const p of principles) {
    for (const c of p.checks) {
      if (c.status === "failed" && c.severity === "error") errorFailures++;
    }
  }

  let overallStatus: string;
  let overallStatusColor: string;
  if (errorFailures > 0) {
    overallStatus = "failed";
    overallStatusColor = "red";
  } else if (totalFailed > 0) {
    overallStatus = "passed with warnings";
    overallStatusColor = "yellow";
  } else {
    overallStatus = "passed";
    overallStatusColor = "green";
  }

  const projectTypes = detectProjectTypes(snapshot);

  const results: CheckResults = {
    framework_id: framework.metadata.id,
    framework_version: framework.metadata.version,
    principles,
    total_checks: totalChecks,
    checks_passed: totalPassed,
    checks_failed: totalFailed,
    checks_skipped: totalSkipped,
    pass_rate: passRate,
    overall_status: overallStatus,
    overall_status_color: overallStatusColor,
    project_types: projectTypes,
    request: {
      repo_url: repoUrl,
      ref,
      framework: framework.metadata.id,
      compliance_level: complianceLevel,
    },
  };

  // Evaluate compliance level
  const levelSpec = framework.compliance_levels[complianceLevel];
  if (levelSpec) {
    results.compliance = {
      level: complianceLevel,
      required_pass_rate: levelSpec.minimum_check_pass_rate,
      actual_pass_rate: passRate,
      meets_level: passRate >= levelSpec.minimum_check_pass_rate,
    };
  }

  return results;
}
