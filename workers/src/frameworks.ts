// ABOUTME: Embedded framework specifications and provider registry
// ABOUTME: Converted from YAML to TypeScript objects for Workers bundling

export interface CheckSpec {
  id: string;
  name: string;
  principle: string;
  severity: "error" | "warning" | "info";
  type: "file-exists" | "dependency-check" | "provider-check";
  description: string;
  config: Record<string, unknown>;
  help_url?: string;
}

export interface FrameworkSpec {
  metadata: {
    id: string;
    name: string;
    version: string;
    description: string;
  };
  checks: CheckSpec[];
  compliance_levels: Record<
    string,
    {
      name: string;
      description: string;
      minimum_check_pass_rate: number;
      badge_color: string;
    }
  >;
}

export interface ProviderInfo {
  name: string;
  publishes_system_cards: boolean;
  system_cards_url?: string;
  notes?: string;
  import_markers: string[];
  model_id_patterns: string[];
}

// ---------------------------------------------------------------------------
// UNESCO 2021 framework (from frameworks/unesco-2021/framework.yaml)
// ---------------------------------------------------------------------------

export const UNESCO_2021: FrameworkSpec = {
  metadata: {
    id: "unesco-2021",
    name: "UNESCO Recommendation on the Ethics of AI",
    version: "1.1.0",
    description:
      "First global normative instrument on AI ethics, adopted unanimously by 193 UNESCO Member States on 23 November 2021.",
  },
  checks: [
    {
      id: "transparency-001",
      name: "Model / System Card",
      principle: "transparency",
      severity: "error",
      type: "file-exists",
      description:
        "Project must include model card or system documentation describing what the system does, its limitations, and intended use",
      config: {
        paths: [
          "MODEL_CARD.md",
          "docs/MODEL_CARD.md",
          "docs/model_card.md",
          "model_card.md",
          "SYSTEM_CARD.md",
          "docs/SYSTEM_CARD.md",
        ],
      },
      help_url: "https://modelcards.withgoogle.com/",
    },
    {
      id: "transparency-002",
      name: "Explainability Implementation",
      principle: "transparency",
      severity: "warning",
      type: "dependency-check",
      description:
        "Project should implement explainability or interpretability methods",
      config: {
        packages: [
          "shap",
          "lime",
          "captum",
          "interpret",
          "alibi",
          "dalex",
          "@tensorflow/tfjs-vis",
          "ml-explain",
        ],
        require_any: true,
      },
    },
    {
      id: "transparency-003",
      name: "AI Provider Transparency",
      principle: "transparency",
      severity: "warning",
      type: "provider-check",
      description:
        "AI model providers used in the project should publish system cards and safety evaluations",
      config: {},
      help_url: "https://www.anthropic.com/system-cards",
    },
    {
      id: "fairness-001",
      name: "Fairness Metrics Library",
      principle: "fairness",
      severity: "warning",
      type: "dependency-check",
      description: "Project should use fairness evaluation tools",
      config: {
        packages: ["fairlearn", "aif360", "responsibleai", "ai-fairness"],
        require_any: true,
      },
    },
    {
      id: "privacy-001",
      name: "Privacy Impact Assessment",
      principle: "privacy",
      severity: "error",
      type: "file-exists",
      description:
        "Project must document privacy impact and data governance practices",
      config: {
        paths: [
          "PRIVACY_IMPACT_ASSESSMENT.md",
          "docs/PRIVACY_IMPACT_ASSESSMENT.md",
          "docs/privacy_impact_assessment.md",
          "PRIVACY.md",
          "docs/PRIVACY.md",
        ],
      },
    },
    {
      id: "accountability-001",
      name: "Version Control",
      principle: "accountability",
      severity: "error",
      type: "file-exists",
      description:
        "Project must use version control for auditability and traceability",
      config: { paths: [".git"] },
    },
    {
      id: "accountability-002",
      name: "Project Documentation",
      principle: "accountability",
      severity: "error",
      type: "file-exists",
      description:
        "Project must have a README describing its purpose, usage, and responsible parties",
      config: {
        paths: ["README.md", "README.rst", "README.txt", "README"],
      },
    },
    {
      id: "safety-001",
      name: "Dependency Manifest",
      principle: "safety",
      severity: "warning",
      type: "file-exists",
      description:
        "Project must declare its dependencies for supply-chain security",
      config: {
        paths: [
          "package.json",
          "requirements.txt",
          "pyproject.toml",
          "setup.py",
          "go.mod",
          "Cargo.toml",
          "Gemfile",
          "pom.xml",
          "build.gradle",
        ],
      },
    },
    {
      id: "safety-002",
      name: "License Declaration",
      principle: "safety",
      severity: "warning",
      type: "file-exists",
      description:
        "Project should include a license to clarify rights and obligations",
      config: {
        paths: ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"],
      },
    },
    {
      id: "sustainability-001",
      name: "Ethical Impact Documentation",
      principle: "sustainability",
      severity: "warning",
      type: "file-exists",
      description:
        "Project should document its ethical and environmental impact (aligned with UNESCO EIA methodology)",
      config: {
        paths: [
          "ETHICS.md",
          "docs/ETHICS.md",
          "ETHICAL_IMPACT_ASSESSMENT.md",
          "docs/ETHICAL_IMPACT_ASSESSMENT.md",
          "IMPACT.md",
          "docs/IMPACT.md",
        ],
      },
      help_url: "https://www.unesco.org/ethics-ai/en/eia",
    },
  ],
  compliance_levels: {
    basic: {
      name: "Basic Compliance",
      description: "Minimum ethics requirements for AI projects",
      minimum_check_pass_rate: 0.5,
      badge_color: "yellow",
    },
    standard: {
      name: "Standard Compliance",
      description: "Comprehensive ethics implementation",
      minimum_check_pass_rate: 0.7,
      badge_color: "green",
    },
    verified: {
      name: "Verified Compliance",
      description: "Full ethics compliance with verification",
      minimum_check_pass_rate: 0.95,
      badge_color: "blue",
    },
  },
};

// ---------------------------------------------------------------------------
// Provider registry (from frameworks/providers.yaml)
// ---------------------------------------------------------------------------

export const PROVIDERS: Record<string, ProviderInfo> = {
  anthropic: {
    name: "Anthropic",
    publishes_system_cards: true,
    system_cards_url: "https://www.anthropic.com/system-cards",
    import_markers: ["anthropic"],
    model_id_patterns: ["claude-"],
  },
  openai: {
    name: "OpenAI",
    publishes_system_cards: true,
    system_cards_url: "https://openai.com/index/gpt-4o-system-card/",
    import_markers: ["openai"],
    model_id_patterns: ["gpt-", "o1-", "o3-"],
  },
  google: {
    name: "Google DeepMind",
    publishes_system_cards: true,
    notes: "Has been criticized for delayed publication of model cards relative to model launches",
    import_markers: ["google.generativeai", "google-generativeai", "@google/generative-ai"],
    model_id_patterns: ["gemini-"],
  },
  meta: {
    name: "Meta",
    publishes_system_cards: true,
    notes: "Model cards for Llama 4 were criticized as insufficient by safety experts",
    import_markers: ["llama"],
    model_id_patterns: ["llama-", "meta-llama"],
  },
  mistral: {
    name: "Mistral AI",
    publishes_system_cards: false,
    notes: "Limited transparency documentation compared to peers",
    import_markers: ["mistralai"],
    model_id_patterns: ["mistral-", "mixtral-"],
  },
  cohere: {
    name: "Cohere",
    publishes_system_cards: false,
    import_markers: ["cohere"],
    model_id_patterns: ["command-"],
  },
};

// ---------------------------------------------------------------------------
// Framework registry
// ---------------------------------------------------------------------------

const FRAMEWORKS: Record<string, FrameworkSpec> = {
  "unesco-2021": UNESCO_2021,
};

export function getFramework(id: string): FrameworkSpec | undefined {
  return FRAMEWORKS[id];
}

export function listFrameworks(): Array<{
  id: string;
  name: string;
  version: string;
  description: string;
  status: string;
  category: string;
}> {
  return [
    {
      id: "unesco-2021",
      name: "UNESCO AI Ethics Recommendation 2021",
      version: "1.1.0",
      description:
        "First global standard on AI ethics adopted by 193 member states",
      status: "available",
      category: "international",
    },
  ];
}
