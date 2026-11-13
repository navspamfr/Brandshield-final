# 🛡️ BrandShield | Enterprise AI Brand Compliance & Protection Platform

BrandShield is an enterprise-grade AI brand compliance, monitoring, and visual asset verification platform inspired by the visual sophistication of **Linear**, the dashboard quality of **Stripe**, and the intelligence of a dedicated compliance guardian.

---

## 🌟 Platform Capabilities

### 1. Executive Command Centre (`Dashboard`)
* **Live Brand Switcher & KPI Cards**: Total assets analyzed, compliance health score, active violation tracker, and configured brand profile metrics.
* **Interactive Analytics Trends**: Interactive compliance score trajectory and violation severity distribution charts (High, Medium, Low).
* **Live System Pulse**: Real-time AI Guardian status indicator.
* **Audit Trail**: Real-time log of recent audits and security events.

### 2. Multi-Modal Compliance Workbench (`Content Analysis`)
* **Multi-Format Ingestion**: Ingests marketing copy, slogans, **PDFs** (with page-by-page text & embedded image extraction), **Images** (PNG, JPG, WEBP, SVG), and **Campaign Spreadsheets** (CSV, JSON).
* **Interactive 1-Click Fixer**: Click **"⚡ Apply Fix"** on any detected violation to automatically rewrite copy in the live workbench.
* **Linguistic & Readability Depth**: Calculates **Flesch Reading Ease** and **Grade Level**; alerts when copy is too complex for target audiences.
* **WCAG 2.1 Visual Accessibility**: Analyzes contrast ratios between dominant foreground and background colors to ensure **WCAG AA (minimum 4.5:1)** compliance.
* **Channel Fit Recommendations**: Detects aspect ratios and recommends ideal distribution channels (1:1 Instagram, 16:9 LinkedIn/X, 9:16 Reels/TikTok, 4:5 Feed).
* **📁 Batch Multi-File Auditing**: Upload and audit up to 10 campaign assets simultaneously with a live progress bar and comparative matrix.
* **Executive HTML Certificates**: Generate and download printable, dark-themed **HTML Compliance Certificates** for campaigns.

### 3. Dedicated Brand Repository (`Brand Profiles`)
* **Multi-Brand Management**: Create, switch, and edit company profiles (Industry, Tagline, Mission, Target Audience).
* **Logo Asset Management**: Upload and manage official transparent logos.
* **Color Palette Builder**: Primary, secondary, and accent colors with interactive hex pickers and live swatch previews.
* **Phrase Dictionary**: Define mandatory **Preferred Phrases** and forbidden **Prohibited Terms**.

### 4. Rulebook Engine (`Guidelines & Rules`)
* **Rule Taxonomy**: Visual identity, Logo usage, Typography, Colour consistency, Brand voice, Content restrictions.
* **⚡ 1-Click Industry Presets**: Instant installation of vetted compliance packs for **SaaS & Enterprise Tech**, **FinTech & Banking**, **Healthcare & Life Sciences**, and **E-Commerce & DTC**.
* **Vector Semantic Retrieval**: Computes dense vector embeddings for rules (OpenAI or built-in subword vector embeddings in pure NumPy for 100% offline use).
* **PDF Rulebook Ingestion**: Automatic rule discovery using PyMuPDF.

### 5. Historical Audit Trail (`Activity History`)
* Searchable audit log filtered by keyword, brand profile, or compliance status.
* Drill-down expanders showing original vs. corrected copy and full violation logs.

### 6. Executive Reports & Certificates (`Compliance Reports`)
* Generate and download official compliance certificates.
* **Top Recurring Brand Risk Analysis**: Tracks the most frequent violations across all campaigns.
* **5-Audit Compliance Trajectory**: Measures whether brand compliance health is improving or declining over time.

### 7. Preferences & Account Security (`Settings`)
* User profile details & PBKDF2 password updating.
* Appearance settings & notification toggles.
* OpenAI API Key configuration with a live **"Test Connection"** validator.
* Vector database re-indexing & factory demo data reset.

---

## 📁 System Architecture

```
BrandShield/
├── backend/
│   ├── api/                   # REST API routes
│   ├── database/
│   │   └── db.py              # SQLite schema, migrations, presets & queries
│   ├── models/
│   │   └── schemas.py         # Pydantic schemas for API payloads
│   └── main.py                # Companion FastAPI REST service
├── frontend/
│   ├── app.py                 # Streamlit entry point and routing
│   ├── auth/
│   │   ├── authentication.py  # PBKDF2 user authentication
│   │   ├── demo_account.py    # Demo credentials
│   │   └── login.py           # Login & signup tabs
│   ├── components/
│   │   ├── header.py          # Executive glassmorphic view header
│   │   ├── metric_cards.py    # Linear-style KPI cards
│   │   └── sidebar.py         # Responsive navigation sidebar
│   ├── styles/
│   │   └── style.css          # Master Design System (Linear/Stripe dark cyber-purple)
│   └── views/
│       ├── dashboard.py       # Intelligent AI command centre & charts
│       ├── analysis.py        # Multi-modal audit workbench & interactive fixer
│       ├── profiles.py        # Dedicated brand profiles & phrase dictionary
│       ├── guidelines.py     # Rule taxonomy & 1-click industry presets
│       ├── history.py         # Searchable audit history
│       ├── reports.py         # Executive compliance certificates & recurring risk
│       └── settings.py        # Credentials, API keys & appearance settings
├── processing/
│   ├── ai_engine/
│   │   ├── analyzer.py        # Audit orchestrator (AI LLM + heuristic fallback)
│   │   └── vector_store.py    # Vector database & semantic rule retrieval
│   ├── compliance/
│   │   ├── deep_analyzer.py   # Linguistic, readability & WCAG contrast engine
│   │   ├── rules_engine.py    # Copy heuristics, severity scoring & diff generator
│   │   └── report_generator.py# Standalone printable HTML certificate generator
│   ├── document_extraction/
│   │   ├── multi_format_parser.py # PDF, image, text & CSV ingestion
│   │   └── pdf_extractor.py   # PyMuPDF text & candidate rule extractor
│   └── image_analysis/
│       └── visual_verifier.py # Dominant color extractor & RGB distance check
├── brandshield.db             # Persistent SQLite database
├── requirements.txt           # Python dependencies
└── README.md                  # System documentation
```

---

## 🚀 Quickstart Guide

### 1. Launch the Application
```powershell
cd C:\Users\HP\BrandShield
.\venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```
Open your browser at: **`http://localhost:8501`**

### 2. Sign In
- **Email**: `demo@brandshield.ai`
- **Password**: `BSdemo@2026`
*(Or click "Create Account" to register a new user profile.)*

### 3. Optional: Run Companion FastAPI Backend
```powershell
uvicorn backend.main:app --reload --port 8000
```
Interactive Swagger docs: **`http://localhost:8000/docs`**
