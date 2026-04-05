# 🤖 Gemini LLM Setup Guide (GCP)

LeadIQ uses **Google Gemini** as its AI engine for lead signal analysis, powered by `google-generativeai`.
Two authentication modes are supported — choose whichever fits your environment.

---

## Option 1 — Direct API Key (Fastest to get started)

Best for: local development, prototyping, small teams.

### Steps

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API key"**
3. Copy the key
4. Add to your backend `.env`:

```env
GEMINI_API_KEY=AIzaSy...your-key-here...
GEMINI_MODEL=gemini-2.0-flash
```

5. Leave `GCP_PROJECT_ID` empty — the SDK will use the API key automatically.

---

## Option 2 — Vertex AI / GCP (Recommended for Production)

Best for: production, enterprise, audit logging, higher quotas, VPC.

### Prerequisites

- A GCP project with billing enabled
- The **Vertex AI API** enabled:
  ```bash
  gcloud services enable aiplatform.googleapis.com
  ```

### Steps

#### A. Create a Service Account

```bash
# Create service account
gcloud iam service-accounts create leadiq-backend \
  --display-name="LeadIQ Backend Service Account"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:leadiq-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Download JSON key
gcloud iam service-accounts keys create ./service-account-key.json \
  --iam-account=leadiq-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

> ⚠️  **IMPORTANT**: Add `service-account-key.json` to `.gitignore` immediately!
> ```bash
> echo "service-account-key.json" >> .gitignore
> ```

#### B. Configure Environment

```env
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Leave GEMINI_API_KEY empty when using Vertex AI
GEMINI_API_KEY=
```

#### C. For Local Dev (without service account key)

```bash
# Install gcloud CLI and authenticate
gcloud auth application-default login
```

This sets up Application Default Credentials that the SDK picks up automatically.

---

## Available Models

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gemini-2.0-flash` | ⚡ Fastest | 💚 Lowest | Development, high volume |
| `gemini-1.5-flash` | ⚡ Fast | 💛 Low | Balanced production use |
| `gemini-1.5-pro` | 🐢 Slower | 🔴 Higher | Highest quality analysis |

Update `GEMINI_MODEL` in your `.env` to switch models.

---

## How It Works in LeadIQ

When the **AI Analyzer** worker runs (`POST /api/run-ai`):

1. A demand signal (raw text) is consumed from the `lead:collected` Redis stream
2. The Gemini model receives a structured prompt asking for JSON output:
   - `intent` (0–1): How strongly they intend to hire/buy
   - `urgency` (0–1): How urgently they need it
   - `budget` (0–1): Likelihood they have budget
   - `category`: saas / fintech / healthtech / edtech / logistics / general
   - `estimated_project_size`: small / medium / large
   - `outreach_angle`: Suggested personalization angle
3. The result is validated and published to `lead:analyzed`
4. The Scoring engine uses `intent`, `urgency`, `budget` to compute a 0–100 score
5. The Outreach generator uses `outreach_angle` for personalisation

### Fallback

If neither `GEMINI_API_KEY` nor `GCP_PROJECT_ID` is set, the analyzer falls back to
**deterministic heuristics** — no API calls, fully offline, suitable for demos.

---

## Vercel Deployment

When deploying to Vercel, add environment variables in the Vercel dashboard:

**Settings → Environment Variables:**
```
GEMINI_API_KEY = AIzaSy...
GEMINI_MODEL   = gemini-2.0-flash
```

Or for Vertex AI, use a service account key encoded as base64:
```bash
base64 -i service-account-key.json
```
Set as `GOOGLE_CREDENTIALS_BASE64`, then decode in your startup code.

---

## Testing Your Integration

Start the backend and trigger the AI worker:

```bash
# Start backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload

# In another terminal, trigger the full pipeline
curl -X POST http://localhost:8000/api/run-miner  # collect signals
curl -X POST http://localhost:8000/api/run-ai     # analyze with Gemini
```

Check backend logs — you should see:
```
INFO  Gemini client initialised with API key (model: gemini-2.0-flash)
INFO  Gemini analysis OK — category=fintech intent=0.87
```

If Gemini isn't configured:
```
WARNING  No Gemini credentials configured. Falling back to deterministic heuristics.
```
