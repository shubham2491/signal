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

## Repo layout

```
signal/
├── backend/         FastAPI + agentic pipeline (OpenAI vision, Tavily search,
│                    ReportLab PDF export)
└── mobile/          React Native + Expo client (iOS + Android, one codebase)
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

## Quick start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY and TAVILY_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live on `http://localhost:8000`. See `GET /` for a health
check and `GET /docs` for the OpenAPI explorer.

### Mobile

```bash
cd mobile
npm install
# Point the client at your backend (LAN IP, ngrok, or hosted URL)
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
| Vision   | OpenAI `gpt-4o`                     | Multimodal, JSON mode, fast iteration   |
| Search   | Tavily                              | Single key, JSON results, simple        |
| PDF      | ReportLab                           | Pure-Python, no headless browser needed |
| Email    | Stubbed (download link)             | Skipping SMTP signup for hackathon      |
