---
title: ChartLens
emoji: 🏥
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ChartLens

> AI-powered medical record chronology for solo personal injury attorneys.

ChartLens eliminates one of the most time-consuming tasks in personal injury law — manually combing through hundreds of pages of medical records to build a chronology. Upload a PDF, get a structured timeline in minutes, with inconsistencies flagged automatically and reports ready to download.

Built for solo PI attorneys who bill by the hour and can't afford to spend that time on paperwork.

---

## What It Does

1. **Upload** — Drag and drop a medical records PDF (up to 50MB)
2. **Extract** — AI reads every page using a Map-Reduce pipeline
3. **Chronology** — Events sorted by date: visits, diagnoses, procedures, billing
4. **Inconsistency Detection** — Flags gaps, contradictions, and anomalies automatically
5. **Download** — Export as a formatted PDF report or Excel spreadsheet

---

## Demo

**Demo case:** Maria Rodriguez, Tampa FL — auto accident  
13 medical events extracted · $26,264 total billed · 3 inconsistency flags caught automatically

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| AI Pipeline | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| PDF Extraction | PyMuPDF |
| Database | SQLAlchemy + SQLite |
| Templates | Jinja2 + Tailwind CSS (CDN) |
| Reports | ReportLab (PDF) + openpyxl (Excel) |
| Auth | JWT (HttpOnly cookies) + bcrypt |
| Billing | Lemon Squeezy |
| Deployment | HuggingFace Spaces (Docker) |

---

## Project Structure

```
ChartLens/
├── app.py                        # FastAPI app entry point
├── config.py                     # Settings + env vars (pydantic-settings)
├── requirements.txt
├── CLAUDE.md                     # Project bible for AI-assisted development
│
├── models/
│   ├── database.py               # SQLAlchemy engine + session
│   ├── user.py                   # User model (auth + billing state)
│   └── case.py                   # Case model (upload + pipeline state)
│
├── core/
│   ├── pdf_extractor.py          # PyMuPDF text extraction
│   ├── chunker.py                # Page chunking for Map-Reduce
│   ├── claude_client.py          # All Anthropic API calls (single source of truth)
│   ├── analyzer.py               # Map phase — extract events per chunk
│   ├── chronology_builder.py     # Reduce phase — merge + sort events
│   ├── inconsistency_detector.py # Flag gaps, contradictions, anomalies
│   └── report_generator.py       # ReportLab PDF + openpyxl Excel output
│
├── routes/
│   ├── auth.py                   # Register, login, logout (JWT + HttpOnly cookie)
│   ├── cases.py                  # Upload, dashboard, results, delete, background pipeline
│   ├── reports.py                # PDF, Excel, JSON download endpoints
│   └── billing.py                # Lemon Squeezy checkout, webhook, cancel
│
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── results.html
│   ├── billing.html
│   ├── billing_success.html
│   └── billing_cancel.html
│
├── static/
│   └── js/
│       └── upload.js             # Drag-and-drop + polling for pipeline status
│
└── tests/
    └── sample_records/
        └── demo_us_case.pdf      # Maria Rodriguez demo case
```

---

## AI Pipeline — How It Works

ChartLens uses a **Map-Reduce pattern** to handle large medical record PDFs that exceed a single LLM context window.

```
PDF Upload
    │
    ▼
PyMuPDF Extraction         — Raw text extracted page by page
    │
    ▼
Chunker                    — Pages grouped into overlapping chunks (~10 pages each)
    │
    ▼
MAP: Analyzer              — Claude extracts medical events from each chunk in parallel
    │                         (date, event type, provider, facility, cost, notes)
    ▼
REDUCE: Chronology Builder — All events merged, deduplicated, sorted by date
    │
    ▼
Inconsistency Detector     — Claude scans the full chronology for:
    │                         • Date gaps (unexplained breaks in treatment)
    │                         • Billing anomalies (charges without corresponding visits)
    │                         • Contradictory diagnoses across providers
    ▼
Report Generator           — PDF (ReportLab) + Excel (openpyxl) generated
    │
    ▼
Results Page               — Chronology table + flags displayed, reports available
```

---

## Billing Model

- **Free Trial** — 3 case uploads, no credit card required
- **Pro Plan** — $149/month via Lemon Squeezy, unlimited uploads
- Trial enforcement happens at the route level before the background pipeline starts
- Webhook handles subscription lifecycle: activation, payment failure, cancellation

---

## Local Development Setup

### Prerequisites

- Python 3.12
- A `.env` file (see below)
- Anthropic API key

### Installation

```bash
git clone https://github.com/Mustafaaa819/ChartLens.git
cd ChartLens

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
# App
SECRET_KEY=your-secret-key-here
APP_ENV=development

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Lemon Squeezy
LEMONSQUEEZY_API_KEY=your_ls_api_key
LEMONSQUEEZY_STORE_ID=your_store_id
LEMONSQUEEZY_VARIANT_ID=your_variant_id
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret
```

### Run

```bash
uvicorn app:app --reload
```

Open `http://localhost:8000`

### Reset Database

```bash
# Stop the server first
del chartlens.db        # Windows
# rm chartlens.db       # Mac/Linux

# Restart — tables recreate automatically on startup
uvicorn app:app --reload
```

---

## Deployment — HuggingFace Spaces

ChartLens is deployed via Docker on HuggingFace Spaces at port 7860.

All environment variables are stored as HF Spaces Secrets (never committed to git).

```bash
git init
git remote add hf https://huggingface.co/spaces/AgentZERO819/ChartLens
git push hf main
```

---

## Key Technical Decisions

**Why Map-Reduce for the AI pipeline?**
Medical record PDFs are often 100-300 pages. No single LLM call can handle that context reliably. Chunking and parallelizing extraction, then reducing into a single chronology, gives consistent results regardless of document size.

**Why SQLite?**
Solo attorneys uploading a handful of cases per day don't need Postgres. SQLite with SQLAlchemy is simpler to deploy, easier to back up, and has zero infrastructure overhead on HF Spaces.

**Why Lemon Squeezy over Stripe?**
Stripe doesn't support Pakistani bank accounts for payouts. Lemon Squeezy acts as Merchant of Record and supports international payouts, making it the right choice for this stack.

**Why HttpOnly cookies for JWT?**
Storing JWTs in localStorage makes them accessible to JavaScript and vulnerable to XSS. HttpOnly cookies are invisible to JS — the browser handles them automatically on every request.

---

## Roadmap

- [ ] Multi-PDF upload per case
- [ ] Client portal (share results link with client)
- [ ] Settlement demand letter generation
- [ ] Provider-level billing summary
- [ ] HIPAA compliance audit

---

## Author

**Muhammad Mustafa** — AgentZERO  
HuggingFace: [AgentZERO819](https://huggingface.co/AgentZERO819)  
GitHub: [Mustafaaa819](https://github.com/Mustafaaa819)

---

## License

Private — All rights reserved. Not open source.