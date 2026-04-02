# Deploying Ethica to Cloudflare Workers

Run the ethica API on Cloudflare's edge network — no Docker, no containers,
no cold starts. Auto-deploys from GitHub on every push.

## How it works

The Workers deployment replaces `git clone` with the **GitHub API**:

| Python (Cloud Run)               | Workers (Cloudflare)                     |
| -------------------------------- | ---------------------------------------- |
| `git clone` via subprocess       | GitHub Trees API (single request)        |
| Read files from filesystem       | GitHub Contents API (on-demand fetch)    |
| Requires Docker + git binary     | Pure TypeScript, no runtime dependencies |
| Single region                    | 300+ edge locations                      |

The check logic is identical — same frameworks, same checks, same API surface.

## Prerequisites

- A [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier works)
- Node.js 18+
- (Optional) A GitHub personal access token for higher rate limits

## Local development

```bash
cd workers
npm install
npm run dev          # local dev server at http://localhost:8787
```

## Deploy from GitHub (recommended)

Connect your repo to Cloudflare Workers for automatic deployments on every push:

1. Go to the [Cloudflare dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create**
2. Select **Create Worker** → **Connect to Git**
3. Authorize Cloudflare and select your `ethica` repository
4. Configure the build:

   | Setting              | Value              |
   | -------------------- | ------------------ |
   | **Production branch** | `main`            |
   | **Root directory**    | `workers`         |
   | **Build command**     | `npm install`     |

5. Click **Save and Deploy**

The `wrangler.toml` controls the entry point (`main`) and static assets
(`[assets]`), so no additional dashboard configuration is needed.

Your API will be live at `https://ethica.<your-subdomain>.workers.dev`.

Every push to `main` triggers a new deployment automatically.

## Deploy manually (CLI)

```bash
cd workers
npm install
npx wrangler login              # first time only
npx wrangler deploy
```

## GitHub token (recommended)

Without a token, the GitHub API allows 60 requests/hour. With a token,
you get 5,000/hour. Each ethica check uses 2-30 API calls depending on
repo size.

**Via the Cloudflare dashboard** (recommended):

1. Go to **Workers & Pages** → your ethica project → **Settings** → **Environment variables**
2. Add variable: Name = `GITHUB_TOKEN`, Value = your token
3. Check **Encrypt** to keep it secret

**Via the CLI:**

```bash
npx wrangler secret put GITHUB_TOKEN
# Paste your token when prompted
```

Generate a token at https://github.com/settings/tokens with no special
scopes needed (public repo access only).

## API endpoints

All endpoints match the Python API:

| Method | Path                    | Description                     |
| ------ | ----------------------- | ------------------------------- |
| GET    | `/health`               | Health check                    |
| GET    | `/frameworks`           | List available frameworks       |
| POST   | `/check`                | JSON compliance results         |
| POST   | `/check/report`         | HTML report card                |
| POST   | `/check/badge`          | SVG badge                       |
| GET    | `/badge/:owner/:repo`   | README-embeddable badge         |

### Example: check a repo

```bash
curl -X POST https://ethica.<your-subdomain>.workers.dev/check \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/my-ai-app.git"}'
```

### Example: embed a badge

```markdown
![Ethica](https://ethica.<your-subdomain>.workers.dev/badge/owner/repo)
```

## Custom domain

1. Go to your Workers project → **Settings** → **Domains & Routes**
2. Add your domain (e.g. `ethica.example.com`)
3. Cloudflare handles DNS and TLS automatically

## Limits

| Resource        | Free tier        | Paid ($5/mo)      |
| --------------- | ---------------- | ----------------- |
| Requests/day    | 100,000          | Unlimited         |
| CPU time/req    | 10 ms            | 30 ms             |
| Subrequests     | 50/request       | 1,000/request     |

Ethica checks typically use 2-30 subrequests (GitHub API calls) and
complete well within CPU limits.

## Comparison with Cloud Run

| Aspect              | Cloud Run (Docker)     | Workers (Cloudflare)        |
| ------------------- | ---------------------- | --------------------------- |
| **Cold start**      | 2-10 seconds           | None (runs at edge)         |
| **Deployment**      | Build image + deploy   | Push to GitHub (automatic)  |
| **Runtime**         | Docker container       | V8 isolate                  |
| **Scaling**         | 0-N containers         | Automatic, per-request      |
| **Free tier**       | ~2M requests/mo        | 100K requests/day           |
| **Global latency**  | Single region          | 300+ locations              |
| **Git access**      | git clone (subprocess) | GitHub API (fetch)          |

## Limitations

- **GitHub repos only**: The Workers version uses the GitHub API, so it
  currently only supports GitHub-hosted repositories. The Python version
  supports any git URL.
- **Large repos**: GitHub's Trees API may truncate results for repos with
  100,000+ files. This is unlikely for most AI projects.
- **Private repos**: Requires a GitHub token with `repo` scope.
