# SIGNAL

> Snap products. Understand what brands are doing. Decide what to design next.

**Fashion Signal Agent** — a mobile-first field intelligence tool for fashion
designers. Upload one or many photos (model shots, store walks, moodboards,
assortment racks). SIGNAL infers the context, compares against a curated
brand universe via live web search, and returns a short editorial brief plus
three recommended design directions.

This is **not** a trend-forecasting dashboard, not a WGSN clone, not an
analytics tool. It is a creative scout for designers in the field.

---

## See it without installing anything

Two zero-setup options:

1. **Tappable web preview** — open `preview/web/index.html` in any browser.
   Click through Home → Upload → Analysis → Results → Export inside a
   phone-frame mockup. Same design tokens as the React Native app.
2. **Static screenshots** — see `preview/shots/*.png`.

## Deploy the backend in one click

The repo includes a Render blueprint. Click the button, sign in to Render
with GitHub, fill in `GEMINI_API_KEY` (free tier: ai.google.dev), optionally
`TAVILY_API_KEY` (free tier: app.tavily.com), and hit deploy.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/shubham2491/signal)

Once it's live you'll get a URL like `https://signal-backend-xxxx.onrender.com`.

- Test it: open `<url>/docs` in your browser, expand `POST /analyze`, click
  "Try it out", upload an image. You should see a JSON brief come back.
- Point the mobile app at it:

  ```bash
  cd mobile
  npm install
  EXPO_PUBLIC_API_URL="https://signal-backend-xxxx.onrender.com" npx expo start
  ```

  Then scan the QR with **Expo Go** on iOS or Android.

Free-tier Render sleeps after 15 minutes idle — first request after a sleep
takes ~30s to wake up. Subsequent requests are fast.

---

## Repo layout

```
signal/
├── backend/         FastAPI + agentic pipeline (Gemini vision, Tavily search,
│                    ReportLab PDF export)
├── mobile/          React Native + Expo client (iOS + Android, one codebase)
└── preview/         Tappable HTML mockup + static screenshots
```

## Privacy

SIGNAL never persists uploaded images. The flow is:

```
upload → in-memory processing → analysis → purge
```

Generated PDF reports are kept short-term in `backend/storage/reports/` so the
mobile client can download them; they are not tied to a user account and can
be aged out aggressively.

Analysis focuses on apparel and design attributes, not personal identity.

## Local quick start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY (and optionally TAVILY_API_KEY)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live on `http://localhost:8000`. See `GET /` for a health
check and `GET /docs` for the OpenAPI explorer.

If you skip the API keys entirely, set `ALLOW_MOCK_FALLBACK=1` in `.env`
(it's the default) and the pipeline returns editorial mock output — useful
for offline demos.

### Mobile

```bash
cd mobile
npm install
# Point the client at your backend (LAN IP, ngrok tunnel, or hosted URL)
export EXPO_PUBLIC_API_URL="http://<your-host>:8000"
npx expo start
```

Scan the QR with Expo Go on iOS / Android.

## Agent pipeline

```
Vision Agent  →  Mode Detector  →  Brand Selector
                                        ↓
                                   Search Agent
                                        ↓
                                Commentary Agent
                                        ↓
                              Recommendation Agent
```

See `backend/app/agents/` — each agent is a single file, sequentially invoked
from `services/pipeline.py`. Easy to swap for true orchestration later.

## API surface

| Endpoint              | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `POST /analyze`       | Multipart upload of 1..N images, returns brief   |
| `POST /export-report` | Generates a PDF from an analysis payload         |
| `GET  /reports/{id}`  | Download the generated PDF (short-lived)         |
| `POST /email-report`  | Stubbed: returns a download link for the PDF     |

## Tech choices

| Layer    | Choice                              | Why                                     |
| -------- | ----------------------------------- | --------------------------------------- |
| Mobile   | React Native + Expo                 | One codebase, camera, QR demo           |
| Backend  | Python + FastAPI                    | Quick, typed, great OpenAPI             |
| Vision   | Google Gemini `1.5-flash`           | Free tier, multimodal, JSON mode        |
| Search   | Tavily                              | Single key, JSON results, simple        |
| PDF      | ReportLab                           | Pure-Python, no headless browser needed |
| Email    | Stubbed (download link)             | Skipping SMTP signup for hackathon      |
| Hosting  | Render (free)                       | One-click `render.yaml` deploy          |
