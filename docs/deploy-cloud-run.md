# Deploying Ethica to Google Cloud Run

This guide walks through deploying the Ethica API service to Google Cloud Run.
By the end you'll have a public URL anyone can POST a repo URL to and get an
ethics compliance report back.

## Prerequisites

1. A Google Cloud account with billing enabled
2. The `gcloud` CLI installed and authenticated:
   ```bash
   # Install: https://cloud.google.com/sdk/docs/install
   gcloud auth login
   ```
3. Docker installed (for local testing, optional)

## Step 1: Set up your GCP project

```bash
# Create a new project (or use an existing one)
gcloud projects create ethica-service --name="Ethica"
gcloud config set project ethica-service

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com
```

## Step 2: Create an Artifact Registry repository

Cloud Run pulls images from Artifact Registry (GCR is deprecated).

```bash
gcloud artifacts repositories create ethica \
  --repository-format=docker \
  --location=us-central1 \
  --description="Ethica container images"
```

## Step 3: Build and push the image

From the repo root:

```bash
# Set variables
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
IMAGE=us-central1-docker.pkg.dev/$PROJECT_ID/ethica/ethica-api

# Option A: Build with Cloud Build (no local Docker needed)
gcloud builds submit --tag $IMAGE .

# Option B: Build locally and push
docker build -t $IMAGE .
gcloud auth configure-docker us-central1-docker.pkg.dev
docker push $IMAGE
```

## Step 4: Deploy to Cloud Run

```bash
gcloud run deploy ethica-api \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 5
```

Key settings explained:
- `--allow-unauthenticated`: Makes the API publicly accessible. Remove this if
  you want to require IAM authentication.
- `--timeout 300`: Gives 5 minutes per request (git clone + checks can be slow
  on large repos).
- `--min-instances 0`: Scales to zero when idle (no cost).
- `--max-instances 5`: Caps concurrent instances to control costs.
- `--concurrency 10`: Each instance handles up to 10 requests in parallel.

## Step 5: Verify the deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe ethica-api \
  --region $REGION --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Health check
curl $SERVICE_URL/health

# List frameworks
curl $SERVICE_URL/frameworks

# Check a repo (JSON response)
curl -X POST $SERVICE_URL/check \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/my-project.git",
    "framework": "unesco-2021",
    "compliance_level": "standard"
  }'

# Get an HTML report card
curl -X POST $SERVICE_URL/check/report \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/my-project.git",
    "framework": "unesco-2021",
    "compliance_level": "standard"
  }' -o report.html

open report.html  # or xdg-open on Linux
```

## Step 6: Set up a custom domain (optional)

```bash
# Map your domain
gcloud run domain-mappings create \
  --service ethica-api \
  --domain ethica.yourdomain.com \
  --region $REGION

# Follow the DNS instructions printed by the command above
# (add CNAME or A records to your DNS provider)
```

## Cost estimate

Cloud Run pricing at scale-to-zero:

| Traffic | Estimated monthly cost |
|---------|----------------------|
| 0 requests (idle) | $0 |
| 100 checks/day | ~$1-3 |
| 1,000 checks/day | ~$10-20 |
| 10,000 checks/day | ~$50-100 |

Main cost drivers: CPU time during git clone + checks, and network egress.
The `--min-instances 0` setting means you pay nothing when nobody is using it.

## Updating the deployment

After code changes, rebuild and redeploy:

```bash
# Rebuild
gcloud builds submit --tag $IMAGE .

# Redeploy (Cloud Run pulls the latest image with the same tag)
gcloud run deploy ethica-api \
  --image $IMAGE \
  --region $REGION
```

Or set up continuous deployment from GitHub:

```bash
# Connect your GitHub repo to Cloud Build
gcloud builds triggers create github \
  --repo-name=ethica \
  --repo-owner=shellen \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml
```

## Restricting access (optional)

If you don't want the API to be fully public:

```bash
# Remove public access
gcloud run services remove-iam-policy-binding ethica-api \
  --region $REGION \
  --member="allUsers" \
  --role="roles/run.invoker"

# Grant access to specific users/service accounts
gcloud run services add-iam-policy-binding ethica-api \
  --region $REGION \
  --member="user:developer@example.com" \
  --role="roles/run.invoker"
```

Callers then authenticate with:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $SERVICE_URL/check -X POST -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo.git"}'
```

## Troubleshooting

**"git clone failed"**: The Cloud Run instance needs outbound internet access
(default). Private repos require authentication -- pass a GitHub token via
environment variable and configure git credential helpers.

**Timeout errors**: Increase `--timeout` or use `--cpu-boost` for faster cold
starts. Very large repos may need deeper clone depth.

**Memory errors**: Increase `--memory` to `1Gi` for repos with many files.

**View logs**:
```bash
gcloud run services logs read ethica-api --region $REGION --limit 50
```
