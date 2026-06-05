# CLAUDE.md — ChartLens Project Bible
# Read this file completely before writing a single line of code.
# This is your source of truth for everything.

---

## 1. WHAT IS CHARTLENS?

ChartLens is a SaaS web application for solo personal injury (PI) lawyers in the United States.

**The One-Line Pitch:**
"Upload your client's medical records. Get a court-ready damages chronology in minutes, not days."

**The Problem It Solves:**
When a PI lawyer takes on a new client (car accident, slip and fall, workplace injury), they receive
medical record PDF dumps from hospitals, clinics, and specialists. These records can be 500–3,000
pages across multiple providers. The lawyer must read every page to find:
- What injuries were diagnosed
- What treatments were given
- What it all cost
- Any inconsistencies that could hurt or help the case

This takes 6–20 hours per case. Manually. A solo lawyer with 20–30 active cases is drowning in
paper. ChartLens cuts that to 30 minutes of AI-powered extraction + human verification.

**What ChartLens Outputs:**
1. A structured chronological timeline of all medical events (date, provider, diagnosis, treatment,
   billed amount, page citation)
2. Inconsistency flags (e.g. "Patient denied prior back pain on 3/14/2023 but records from
   11/2/2021 show chronic lumbar treatment")
3. A damages summary (total billed, total paid, outstanding balance)
4. A downloadable PDF report formatted for demand letters
5. A downloadable Excel chronology for case management

---

## 2. WHO IS THE CUSTOMER?

**Primary Target: Solo PI Lawyers in the United States**

Specifics:
- Solo practitioners or firms with 1–5 attorneys
- Practice areas: personal injury, auto accidents, slip and fall, workplace injuries,
  medical malpractice
- Geographic focus: Florida, Texas, California, Georgia (highest PI case volumes in the US)
- Tech comfort: moderate — they use Clio, MyCase, or similar practice management software
- Budget: willingness to pay $149–$249/month for tools that demonstrably save time

**Why They Will Pay:**
- Average billing rate: $288/hour
- Saving 8 hours/case = $2,304 worth of time recovered per case
- At $149/month, ChartLens pays for itself in under 31 minutes of their billing rate
- They already pay $79–$139/month for Clio or MyCase — a focused AI tool at $149 is a clear yes

**What They Are NOT:**
- BigLaw firms (they have paralegals and enterprise tools like Harvey AI at $1,200+/seat/month)
- Corporate lawyers
- Pakistani or local market lawyers (US market only for MVP)

---

## 3. BUSINESS MODEL

**Pricing:** $149/month flat subscription
**Free Trial:** First 3 cases free, no credit card required
**Payment Processor:** LemonSqueezy (Stripe does not support Pakistan)
**First Revenue Goal:** $500 MRR (4 paying customers)
**Long-term Goal:** $50,000 MRR

**Unit Economics:**
- 4 customers = $596/month (first milestone)
- 25 customers = $3,725/month
- 100 customers = $14,900/month
- 336 customers = ~$50,000/month

---

## 4. TECH STACK — NON-NEGOTIABLE

Use exactly these technologies. Do not substitute without asking.

| Layer          | Technology                        | Notes                                      |
|----------------|-----------------------------------|--------------------------------------------|
| Backend        | FastAPI                           | Python 3.12.7                              |
| Templates      | Jinja2                            | Server-side rendering                      |
| Styling        | Tailwind CSS (CDN)                | No build step required                     |
| PDF Extraction | PyMuPDF (fitz)                    | Primary PDF parser                         |
| OCR fallback   | Tesseract / pytesseract           | For scanned/image-based PDFs (Phase 2)     |
| AI Model       | Claude claude-sonnet-4-20250514   | Via Anthropic Python SDK                   |
| AI Pattern     | Map-Reduce chunking               | Never send full PDF to Claude at once      |
| Async          | Python asyncio + httpx            | For parallel Claude API calls              |
| Auth           | Simple email+password             | JWT tokens, no OAuth for MVP               |
| Database       | SQLite (dev) → PostgreSQL (prod)  | SQLAlchemy ORM                             |
| Payments       | LemonSqueezy                      | Subscription billing (Stripe unsupported in Pakistan) |
| PDF Reports    | reportlab                         | Generate downloadable PDF output           |
| Excel Reports  | openpyxl                          | Generate downloadable Excel chronology     |
| Deployment     | Hugging Face Spaces               | Docker container                           |
| Environment    | python-dotenv                     | .env file for all secrets                  |

**Python Version:** 3.12.7
**Project Location:** F:\PythonProjects\ChartLens\
**Virtual Environment:** F:\PythonProjects\ChartLens\.venv

---

## 5. PROJECT FOLDER STRUCTURE

Build exactly this structure. Do not deviate.

```
ChartLens/
├── CLAUDE.md                        ← This file
├── README.md                        ← Project overview
├── .env                             ← Secrets (never commit this)
├── .env.example                     ← Template for .env (safe to commit)
├── .gitignore
├── requirements.txt
├── Dockerfile
├── app.py                           ← FastAPI entry point
│
├── core/
│   ├── __init__.py
│   ├── pdf_extractor.py             ← PyMuPDF text + page extraction
│   ├── chunker.py                   ← Split large docs into processable chunks
│   ├── claude_client.py             ← All Claude API calls live here
│   ├── analyzer.py                  ← Main AI pipeline orchestrator
│   ├── chronology_builder.py        ← Sort + merge extracted events
│   ├── inconsistency_detector.py    ← Flag contradictions across records
│   └── report_generator.py         ← Build PDF + Excel output files
│
├── models/
│   ├── __init__.py
│   ├── database.py                  ← SQLAlchemy setup
│   ├── user.py                      ← User model
│   └── case.py                      ← Case model
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                      ← Login, register, JWT
│   ├── cases.py                     ← Case CRUD + upload
│   └── reports.py                   ← Report generation + download
│
├── templates/
│   ├── base.html                    ← Base layout with nav
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard.html               ← Case list overview
│   ├── upload.html                  ← PDF upload page
│   └── results.html                 ← Chronology + report view
│
├── static/
│   ├── css/
│   │   └── custom.css
│   └── js/
│       └── upload.js                ← Upload progress + UI interactions
│
└── tests/
    ├── test_extractor.py
    ├── test_analyzer.py
    └── sample_records/              ← Test PDF files (not real patient data)
```

---

## 6. ENVIRONMENT VARIABLES

The .env file must contain exactly these variables:

```
ANTHROPIC_API_KEY=your_key_here
LEMONSQUEEZY_API_KEY=your_key_here
LEMONSQUEEZY_STORE_ID=your_store_id_here
LEMONSQUEEZY_VARIANT_ID=12345  # placeholder until product published
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret_here
SECRET_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///./chartlens.db
MAX_UPLOAD_SIZE_MB=50
MAX_PAGES_MVP=500
```

Never hardcode any of these values anywhere in the codebase.
Always load via os.getenv() or python-dotenv.

---

## 7. THE AI PIPELINE — MOST IMPORTANT SECTION

This is the core of the product. Get this right above everything else.

### 7.1 The Problem With Large PDFs

Claude has a context window limit. Even if it didn't, sending 500 pages at once produces
poor extraction quality because the model loses focus over massive inputs.

**The solution: Map-Reduce chunking pattern.**

### 7.2 Map-Reduce Pipeline

```
STEP 1 — EXTRACT
Raw PDF → PyMuPDF → Plain text per page + page numbers

STEP 2 — CHUNK (Map phase)
Group pages into chunks of 30–50 pages each
Each chunk = one Claude API call
Run all chunks in parallel using asyncio

STEP 3 — EXTRACT STRUCTURED DATA (per chunk)
Claude extracts from each chunk:
{
  "events": [
    {
      "date": "2023-03-14",
      "provider": "Dr. Ahmed, Tampa General Hospital",
      "visit_type": "Emergency",
      "diagnosis": ["Lumbar strain", "Cervical sprain"],
      "icd_codes": ["M54.5", "S13.4XXA"],
      "treatment": "MRI ordered, Ibuprofen 800mg prescribed",
      "billed_amount": 4200.00,
      "paid_amount": 1890.00,
      "page_numbers": [14, 15, 16],
      "raw_quote": "Patient presents with acute lower back pain..."
    }
  ],
  "notes": "Any ambiguous findings or extraction uncertainties"
}

STEP 4 — MERGE (Reduce phase)
Combine all chunk results into one master event list
Deduplicate events that appear in overlapping chunks
Sort chronologically by date

STEP 5 — INCONSISTENCY DETECTION
One final Claude call on the merged summary (not full text)
Find contradictions: prior conditions denied, symptom escalations,
gaps in treatment, date anomalies

STEP 6 — REPORT GENERATION
Build chronology table → reportlab PDF
Build Excel sheet → openpyxl
Store both in database linked to case
```

### 7.3 Claude Prompt Engineering Rules

These rules are mandatory. The quality of extraction IS the product.

**Extraction Prompt Must:**
- Always request JSON output only — no prose, no explanation
- Include explicit field definitions for every field
- Specify date format: YYYY-MM-DD always
- Ask Claude to use null for missing fields, never guess
- Include page numbers for every extracted event (for lawyer verification)
- Specify currency format: always float, never string
- Tell Claude to flag uncertainty with a confidence field

**Inconsistency Prompt Must:**
- Receive only the merged chronology summary, NOT the full text
- Ask for specific contradiction types: prior condition denial, treatment gaps,
  billing anomalies, provider statement conflicts
- Return structured JSON with: inconsistency_type, date_1, date_2,
  description, severity (low/medium/high), page_references

**Golden Rule:**
Never trust Claude output without JSON validation.
Always wrap Claude responses in try/except with fallback handling.
Always validate required fields exist before processing.

### 7.4 Async Implementation

Use asyncio for parallel chunk processing:

```python
async def process_all_chunks(chunks: list[str]) -> list[dict]:
    tasks = [process_single_chunk(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Handle any failed chunks gracefully
    return [r for r in results if not isinstance(r, Exception)]
```

A 300-page PDF split into 10 chunks processed in parallel = ~10x speed improvement
over sequential processing.

---

## 8. ROUTES — COMPLETE API SPECIFICATION

### Auth Routes (routes/auth.py)
```
POST /auth/register     → Create account (email, password, firm_name)
POST /auth/login        → Return JWT token
POST /auth/logout       → Invalidate token
GET  /auth/me           → Current user info
```

### Case Routes (routes/cases.py)
```
GET  /                  → Redirect to /dashboard if logged in, else /login
GET  /dashboard         → List all cases for current user
GET  /upload            → Upload page (form)
POST /cases/upload      → Accept PDF upload, create case, trigger analysis
GET  /cases/{case_id}   → Results page for specific case
DELETE /cases/{case_id} → Delete case and all associated files
GET  /cases/{case_id}/status → Polling endpoint — returns analysis progress %
```

### Report Routes (routes/reports.py)
```
GET /reports/{case_id}/pdf      → Download PDF report
GET /reports/{case_id}/excel    → Download Excel chronology
GET /reports/{case_id}/json     → Raw JSON data (for future API access)
```

### LemonSqueezy Routes (routes/billing.py)
```
GET  /billing               → Billing management page
POST /billing/subscribe     → Create LemonSqueezy checkout session
POST /billing/cancel        → Cancel subscription via LS API
POST /billing/webhook       → LemonSqueezy webhook handler (HMAC-SHA256 verified)
GET  /billing/success       → Post-payment success page
GET  /billing/cancel-page   → Cancelled payment page
```

---

## 9. DATABASE MODELS

### User Model
```python
class User:
    id: UUID
    email: str (unique)
    password_hash: str
    firm_name: str
    created_at: datetime
    lemon_customer_id: str (nullable, unique)   # LemonSqueezy customer ID
    lemon_subscription_id: str (nullable)        # LemonSqueezy subscription ID
    subscription_status: str  # 'trial', 'active', 'cancelled', 'past_due', 'canceled'
    trial_cases_used: int  # max 3 on free trial (default 0)
    cases: relationship → Case[]
```

### Case Model
```python
class Case:
    id: UUID
    user_id: UUID (FK → User)
    client_name: str
    case_number: str (nullable)
    original_filename: str
    file_path: str
    page_count: int
    status: str  # 'uploading', 'processing', 'complete', 'failed'
    progress_percent: int  # 0–100
    created_at: datetime
    completed_at: datetime (nullable)
    chronology_json: Text  # Full extracted data as JSON string
    pdf_report_path: str (nullable)
    excel_report_path: str (nullable)
    error_message: str (nullable)
```

---

## 10. FRONTEND — PAGE BY PAGE SPEC

### All Pages
- Tailwind CSS via CDN
- Mobile responsive
- Professional, clean design — lawyers expect trustworthy, not flashy
- Color palette: Deep navy (#1e3a5f), White (#ffffff), Accent blue (#2563eb),
  Success green (#16a34a), Warning amber (#d97706), Error red (#dc2626)
- Font: System font stack — no custom fonts needed for MVP

### Login Page (/login)
- Email + password fields
- "Remember me" checkbox
- Link to register
- No social login for MVP

### Register Page (/register)
- Email, password, confirm password, firm name
- Agree to terms checkbox
- After registration → redirect to dashboard

### Dashboard (/dashboard)
- Header with firm name + logout button
- Subscription status badge (Trial: X cases remaining / Active / Cancelled)
- "Upload New Case" button (primary CTA)
- Cases table: client name, case number, date uploaded, status, actions
- Status shows processing spinner if analysis in progress
- Actions: View Results, Download PDF, Download Excel, Delete

### Upload Page (/upload)
- Large drag-and-drop zone for PDF
- Client name field (required)
- Case number field (optional)
- File size limit display (50MB max for MVP)
- Page count estimate after file selection
- Submit button triggers upload + analysis
- Progress bar during upload
- After upload: redirect to results page with processing spinner

### Results Page (/cases/{case_id})
- Case header: client name, case number, date, total pages analyzed
- Summary cards row: Total Events, Total Billed, Total Paid, Inconsistencies Found
- Chronology table:
  - Columns: Date, Provider, Diagnosis, Treatment, Billed, Paid, Page(s)
  - Sortable by date
  - Each row has page citation that links to page number reference
- Inconsistencies section:
  - Each flag shows: type, severity badge, description, relevant dates, page refs
- Download buttons: Download PDF Report, Download Excel
- Back to Dashboard link

---

## 11. MVP SCOPE — WHAT IS IN AND WHAT IS OUT

### IN SCOPE (Build This Now)
- Clean digital PDF upload only (not scanned)
- Single PDF file per case (not multiple files)
- Up to 500 pages per PDF
- Email + password auth
- Basic dashboard with case list
- Full AI extraction pipeline
- PDF report download
- Excel chronology download
- LemonSqueezy subscription ($149/month)
- Free trial (3 cases)
- Deploy to Hugging Face Spaces

### OUT OF SCOPE (Phase 2 — Do Not Build Now)
- Multiple file upload per case
- Scanned PDF / OCR support (Tesseract)
- Image file support (JPG, PNG)
- DOCX support
- Pages over 500
- Case collaboration / sharing
- Client portal
- Email notifications
- API access for third parties
- Mobile app
- Integrations with Clio / MyCase

**When a feature is out of scope and you are tempted to build it anyway: stop. Finish the
MVP first. Ship to real customers. Then add features based on what they actually ask for.**

---

## 12. ERROR HANDLING — MANDATORY RULES

Every Claude API call must be wrapped in try/except.
Every file operation must be wrapped in try/except.
Every database operation must be wrapped in try/except.

**Claude API failures:**
- If a chunk fails extraction: log the error, skip the chunk, continue with others
- If more than 50% of chunks fail: mark case as failed with descriptive error message
- Never crash the entire analysis because one chunk failed

**PDF extraction failures:**
- If PyMuPDF cannot open file: return clear error "Invalid or corrupted PDF file"
- If PDF has no extractable text: return error "This PDF appears to be scanned.
  Scanned PDF support coming soon."
- If PDF exceeds 500 pages: return error "PDF exceeds 500 page limit for MVP"

**Upload failures:**
- If file exceeds 50MB: reject before processing
- If file is not PDF: reject with clear message
- Always clean up temp files even on failure

---

## 13. SECURITY RULES

- Never log patient data or medical record content
- Never store raw PDF text in logs
- JWT tokens expire after 24 hours
- Passwords hashed with bcrypt (never plain text, never MD5/SHA1)
- All file uploads stored with UUID filenames (never original filename on disk)
- LemonSqueezy webhook signature must be verified on every webhook call (HMAC-SHA256)
- Rate limit upload endpoint: max 10 uploads per user per hour
- HTTPS only in production (HF Spaces handles this)

---

## 14. DEVELOPMENT BUILD ORDER — WEEK BY WEEK

### Week 1 — Foundation (Days 1–7)
Goal: PDF goes in, raw text comes out, Claude responds.

Day 1–2:
- [ ] Create project folder and venv
- [ ] Install all dependencies (requirements.txt)
- [ ] Create .env with all required variables
- [ ] Build app.py with basic FastAPI setup
- [ ] Health check endpoint GET /health returns {"status": "ok"}

Day 3–4:
- [ ] Build core/pdf_extractor.py — extract text + page numbers from PDF
- [ ] Build POST /cases/upload endpoint — accept file, save to disk
- [ ] Test extraction on a real sample PDF

Day 5–7:
- [ ] Build core/claude_client.py — single chunk extraction call
- [ ] Build core/chunker.py — split text into 30-50 page chunks
- [ ] Test: upload PDF → extract text → send one chunk to Claude → get JSON back
- [ ] Week 1 is done when this pipeline works end-to-end

### Week 2 — AI Pipeline (Days 8–14)
Goal: Full extraction pipeline working with real accuracy.

Day 8–9:
- [ ] Build core/analyzer.py — orchestrates full Map-Reduce pipeline
- [ ] Implement asyncio parallel chunk processing
- [ ] Build chronology_builder.py — merge + sort + deduplicate events

Day 10–11:
- [ ] Build inconsistency_detector.py — final Claude pass for contradictions
- [ ] Prompt engineering: iterate on extraction prompt until accuracy is solid
- [ ] Test on multiple sample PDFs of varying complexity

Day 12–14:
- [ ] Build database models (User + Case)
- [ ] Add case status tracking (processing → complete/failed)
- [ ] Add progress polling endpoint GET /cases/{id}/status
- [ ] Week 2 done when full pipeline runs reliably on 5 different test PDFs

### Week 3 — UI + Output (Days 15–21)
Goal: A lawyer can use this without instructions.

Day 15–16:
- [ ] Build base.html template with nav
- [ ] Build login.html + register.html
- [ ] Build auth routes (register, login, JWT)

Day 17–18:
- [ ] Build dashboard.html — case list
- [ ] Build upload.html — drag and drop with progress bar
- [ ] Build results.html — chronology table + inconsistency flags

Day 19–21:
- [ ] Build report_generator.py — PDF report via reportlab
- [ ] Build Excel export via openpyxl
- [ ] Wire up download endpoints
- [ ] Week 3 done when a non-technical person can upload a PDF and download a report

### Week 4 — Launch (Days 22–28)
Goal: Live product, first real users.

Day 22–23:
- [x] Integrate LemonSqueezy subscription ($149/month plan) — DONE
- [x] Build billing routes + HMAC-SHA256 webhook handler — DONE
- [x] Build billing templates (billing, success, cancel) — DONE

Day 24:
- [ ] Trial enforcement sweep — gate all statuses (cancelled, past_due, expired)
- [ ] Add slowapi rate limiting — 10 uploads/hour by user ID
- [ ] Add favicon to static/

Day 25:
- [ ] Build Dockerfile

Day 26:
- [ ] Deploy to Hugging Face Spaces
- [ ] Test full flow on production deployment
- [ ] Publish LS product, swap in real LEMONSQUEEZY_VARIANT_ID in HF secrets

Day 27–28:
- [ ] Record 60-second Loom demo (Maria Rodriguez case)
- [ ] Outreach: Reddit r/Lawyertalk, LinkedIn, FL/TX/GA bar directories
- [ ] Week 4 done when 1 real lawyer has used the product

---

## 15. REQUIREMENTS.TXT

```
fastapi==0.111.0
uvicorn==0.29.0
jinja2==3.1.4
python-multipart==0.0.9
python-dotenv==1.0.1
anthropic==0.28.0
pymupdf==1.24.3
pytesseract==0.3.10
Pillow==10.3.0
sqlalchemy==2.0.30
alembic==1.13.1
bcrypt==4.1.3
python-jose[cryptography]==3.3.0
slowapi==0.1.9
reportlab==4.2.0
openpyxl==3.1.2
httpx==0.27.0
aiofiles==23.2.1
```

---

## 16. SAMPLE EXTRACTION PROMPT (Starting Point)

Refine this as accuracy improves. This is version 1.

```
You are a medical record extraction specialist for personal injury law cases.

Extract ALL medical events from the following medical record text.
Return ONLY a valid JSON object. No prose. No explanation. No markdown.

Required JSON format:
{
  "events": [
    {
      "date": "YYYY-MM-DD or null if not found",
      "provider_name": "Doctor or facility name",
      "provider_type": "Hospital/Clinic/Specialist/Pharmacy/etc",
      "visit_type": "Emergency/Follow-up/Consultation/Procedure/etc",
      "diagnosis": ["list of diagnoses as strings"],
      "icd_codes": ["list of ICD-10 codes if present, else empty array"],
      "treatment": "Description of treatment, medications, procedures",
      "billed_amount": 0.00,
      "paid_amount": 0.00,
      "page_numbers": [list of page numbers where this event appears],
      "confidence": "high/medium/low",
      "notes": "Any ambiguity or extraction uncertainty"
    }
  ],
  "extraction_notes": "Any overall notes about this chunk"
}

Rules:
- Use null for any field where data is not present. Never guess.
- Dates must be YYYY-MM-DD format. If only month/year known, use first of month.
- Dollar amounts must be floats. If not found, use 0.00.
- Include page numbers for every event — this is mandatory for lawyer verification.
- If multiple events occur in one visit, create separate event objects for each.
- Confidence is high if all fields are clearly stated, medium if some inferred,
  low if heavily uncertain.

Medical record text (pages {start_page}–{end_page}):
{chunk_text}
```

---

## 17. CODING STANDARDS

- All functions must have type hints
- All functions must have docstrings
- Maximum function length: 50 lines (split into helpers if longer)
- No print() statements — use Python logging module
- No hardcoded strings — use constants or config
- No TODO comments in committed code — finish it or create a GitHub issue
- Every endpoint must return proper HTTP status codes
- All file paths use pathlib.Path — never string concatenation

---

## 18. WHAT SUCCESS LOOKS LIKE

**Week 1 Success:** Upload a 50-page PDF, get raw extracted text back from Claude.

**Week 2 Success:** Upload a 200-page medical record PDF, get a structured JSON
chronology with accurate dates, providers, diagnoses, and costs.

**Week 3 Success:** A non-technical person can log in, upload a PDF, and download
a professional PDF report without any instructions from Mustafa.

**Week 4 Success:** The product is live on Hugging Face Spaces. At least one real
PI lawyer has used it and given feedback. LemonSqueezy is accepting payments.

**Month 2 Success:** 4 paying customers. $596 MRR. First real revenue.

---

## 19. IMPORTANT CONTEXT ABOUT THE DEVELOPER

- Developer: Mustafa (self-taught, Pakistan)
- Experience: 20+ Python/AI projects, FastAPI, Jinja2, Tailwind, Claude API,
  CrewAI, LangChain, LangGraph, HF Spaces deployment
- IDE: Cursor
- Python: 3.12.7 with per-project venvs
- Previous deployments: RadIQ (HF Spaces), SaaS Feedback Intelligence (HF Spaces)
- Preferred AI: Claude API (Anthropic) — not OpenAI
- DO NOT suggest switching to OpenAI, Streamlit, or Gradio
- DO NOT suggest Django — FastAPI only
- DO NOT add unnecessary complexity — Mustafa values clean, simple, working code

---

## 20. FINAL INSTRUCTION TO CLAUDE CODE

When you start a new session on this project:
1. Read this entire CLAUDE.md file first
2. Check what files already exist before creating new ones
3. Build in the exact order specified in Section 14
4. Ask before deviating from any spec in this file
5. The AI pipeline in Section 7 is the most critical — get it right
6. When in doubt: simpler is better, working is better than perfect
7. Never skip error handling
8. Never commit .env or any file containing real API keys

The goal is a working product in the hands of real lawyers within 4 weeks.
Not a perfect product. A working one. Ship it.

---

## 21. DEV WORKFLOW NOTES

### Resetting the database
SQLite tables are only created once at server startup via init_db() in the lifespan handler.

To reset cleanly:
1. Stop the server (Ctrl+C)
2. Delete chartlens.db
3. Restart: uvicorn app:app --reload

Never delete chartlens.db while the server is running — tables will not recreate until restart.

### Running the server
cd F:\PythonProjects\ChartLens
.venv\Scripts\activate
uvicorn app:app --reload
Open: http://localhost:8000

### Testing uploads
Use PDFs from tests/sample_records/
Test error state: rename a .txt file to .pdf and attempt upload — should return 400, not 500.