# Ethica

**AI ethics compliance checking as a service and CLI**

Automated compliance checking against the [UNESCO Recommendation on the Ethics of AI](https://www.unesco.org/en/artificial-intelligence/recommendation-ethics) -- the first global standard on AI ethics, adopted unanimously by 193 Member States in November 2021.

Works with Python, JavaScript/TypeScript, Go, Rust, Java, and any project with a git repo.

## Quick Start

### As a CLI

```bash
pip install -e "."

cd your-project
ethica init       # creates .ai-ethics.yaml + doc templates
ethica check      # run compliance checks
```

### As a Service

```bash
pip install -e ".[server]"
ethica serve      # starts API on port 8000

# Check any public repo
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo.git"}'
```

### Badge for Your README

Once deployed, add a compliance badge to any project:

```markdown
![Ethica](https://your-ethica-service.run.app/badge/owner/repo)
```

Query params: `?level=basic|standard|verified` `?ref=branch` `?framework=unesco-2021`

## What It Checks

Ethica implements 9 automated checks across 6 of the [10 UNESCO principles](https://unesdoc.unesco.org/ark:/48223/pf0000380455). The remaining 4 principles (Proportionality, Human Oversight, Awareness, Governance) require organizational processes -- see UNESCO's [RAM](https://www.unesco.org/ethics-ai/en/ram) and [EIA](https://www.unesco.org/ethics-ai/en/eia) tools for those.

| Principle | Check | What it looks for | Severity |
|-----------|-------|-------------------|----------|
| **Transparency** | Model / System Card | `MODEL_CARD.md`, `SYSTEM_CARD.md` in root or `docs/` | required |
| **Transparency** | Explainability | `shap`, `captum`, `lime`, `alibi`, `@tensorflow/tfjs-vis`, etc. in deps | recommended |
| **Fairness** | Fairness Metrics | `fairlearn`, `aif360`, `responsibleai`, etc. in deps | recommended |
| **Privacy** | Privacy Assessment | `PRIVACY_IMPACT_ASSESSMENT.md` or `PRIVACY.md` | required |
| **Accountability** | Version Control | `.git/` directory | required |
| **Accountability** | README | `README.md` (or `.rst`, `.txt`) | required |
| **Safety** | Dependency Manifest | `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc. | recommended |
| **Safety** | License | `LICENSE`, `COPYING`, etc. | recommended |
| **Sustainability** | Ethical Impact Doc | `ETHICS.md` or `ETHICAL_IMPACT_ASSESSMENT.md` ([aligned with UNESCO EIA](https://www.unesco.org/ethics-ai/en/eia)) | recommended |

Dependency checks read `requirements.txt`, `pyproject.toml`, `setup.py`, and `package.json`.

## API Endpoints

| Method | Path | Returns |
|--------|------|---------|
| `GET` | `/health` | Readiness probe |
| `GET` | `/frameworks` | Available frameworks |
| `POST` | `/check` | JSON compliance results |
| `POST` | `/check/report` | HTML report card |
| `POST` | `/check/badge` | SVG badge |
| `GET` | `/badge/{owner}/{repo}` | SVG badge (for README embedding) |
| `GET` | `/docs` | Interactive API docs (Swagger) |

## Compliance Levels

| Level | Pass Rate | Scope |
|-------|-----------|-------|
| **basic** | 50% | Transparency + Accountability only |
| **standard** | 70% | + Fairness, Privacy, Safety (default) |
| **verified** | 95% | All principles |

```bash
ethica check --level basic
ethica check --level verified
```

## Configuration

`ethica init` creates `.ai-ethics.yaml`:

```yaml
version: "1.0"
frameworks:
  - id: "unesco-2021"
    enabled: true
    compliance_level: "standard"
exclude_checks: []
  # - "unesco-2021/transparency-002"  # optionally skip checks
```

## Deploying

### Cloudflare Pages (recommended)

No Docker required. Connect your GitHub repo and it auto-deploys on every push to Cloudflare's edge (300+ locations, no cold starts).

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. Select your repo, set root directory to `workers`, build command to `npm install`, output to `public`
3. Deploy

See [docs/deploy-cloudflare.md](docs/deploy-cloudflare.md) for full instructions, GitHub token setup, and custom domains.

### Google Cloud Run (Docker)

See [docs/deploy-cloud-run.md](docs/deploy-cloud-run.md) for full instructions. The short version:

```bash
IMAGE=us-central1-docker.pkg.dev/$PROJECT_ID/ethica/ethica-api
gcloud builds submit --tag $IMAGE .
gcloud run deploy ethica-api --image $IMAGE --region us-central1 \
  --allow-unauthenticated --port 8080 --min-instances 0
```

Scales to zero when idle. ~$0-5/mo at low traffic.

## Development

```bash
git clone https://github.com/shellen/ethica
cd ethica
pip install -e ".[dev,server]"
pytest
```

## UNESCO Source Material

This project implements automated checks inspired by the UNESCO Recommendation on the Ethics of Artificial Intelligence. Key references:

- [Full text of the Recommendation](https://unesdoc.unesco.org/ark:/48223/pf0000380455) (adopted 23 Nov 2021)
- [UNESCO Ethics of AI overview](https://www.unesco.org/en/artificial-intelligence/recommendation-ethics)
- [Readiness Assessment Methodology (RAM)](https://www.unesco.org/ethics-ai/en/ram) -- country-level diagnostic deployed in 60+ countries
- [Ethical Impact Assessment (EIA)](https://www.unesco.org/ethics-ai/en/eia) -- system-level impact assessment tool (published 2023)
- [Global AI Ethics and Governance Observatory](https://www.unesco.org/ethics-ai/en) -- launched 2024
- [Key facts summary](https://unesdoc.unesco.org/ark:/48223/pf0000385082)

Ethica automates project-level checks. It does not replace the RAM (national governance) or EIA (system impact) processes. This project is not officially endorsed by or affiliated with UNESCO.

## License

Apache 2.0 -- See [LICENSE](LICENSE) for details.
