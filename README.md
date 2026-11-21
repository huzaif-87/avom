# TalentRank AI

AI-Based Resume Matching & Candidate Ranking System for corporate selection assignments.

---

## 📌 Project Overview & Stage Status

- **Stage 1 (Completed)**: Core Architectural Foundation, Modular API Architecture, React Shell, Modern SaaS Redesign & Candidate Gmail Outreach.
- **Stage 2A (Completed)**: Backend Resume Parsing (PyMuPDF & python-docx) & Job Description Analysis.
- **Stage 2B (Completed)**: Frontend Integration for Job Description Analysis and Bulk Resume Parsing.
- **Stage 3 (Upcoming)**: AI Semantic Matching Engine & Multi-factor Scoring (Sentence Transformers).
- **Stage 4 (Upcoming)**: Candidate Ranking, Multi-criteria Filtering & Selection Analytics Export.

---

## 📁 Project Architecture

```
TalentRank-AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── api.py                    # Mounts /health, /resumes, /jd
│   │   │   └── endpoints/
│   │   │       ├── health.py             # GET /api/health
│   │   │       ├── resumes.py            # POST /api/resumes/parse
│   │   │       └── jd.py                 # POST /api/jd/analyze
│   │   ├── schemas/
│   │   │   ├── resume.py                 # CandidateResumeResult, ResumeBatchResponse
│   │   │   └── jd.py                     # JDAnalyzeRequest, JDAnalyzeResponse
│   │   └── services/
│   │       ├── parsers/
│   │       │   ├── pdf_parser.py         # PyMuPDF in-memory text extraction
│   │       │   └── docx_parser.py        # python-docx (paragraphs + tables)
│   │       └── extractors/
│   │           ├── skills_taxonomy.py    # Curated regex taxonomy (80+ skills)
│   │           ├── candidate_extractor.py# Name, email, phone, edu, exp
│   │           └── jd_analyzer.py        # Section-based JD requirements parser
│   ├── main.py                           # FastAPI application entry point
│   ├── requirements.txt                  # Python dependencies
│   └── tests/
│       └── test_stage2a.py               # 10 automated backend test scenarios
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── CandidateDetailModal.jsx  # Candidate detail drawer with raw text view
    │   │   ├── ConnectCandidateButton.jsx# Reusable Gmail communication button
    │   │   ├── ConnectionStatusBadge.jsx # Single compact dynamic backend status pill
    │   │   ├── Header.jsx                # Clean SaaS top navigation
    │   │   └── Sidebar.jsx               # Deep graphite sidebar
    │   ├── pages/
    │   │   ├── DashboardPage.jsx         # Dashboard reflecting live session data
    │   │   ├── NewAnalysisPage.jsx       # Complete JD analysis + bulk resume parsing
    │   │   └── CandidatesPage.jsx        # Searchable candidate directory with detail modals
    │   ├── services/
    │   │   ├── api.js                    # Axios instance (health, JD analysis, resume parse)
    │   │   └── gmailService.js           # Secure pre-filled Gmail compose generator
    │   ├── App.jsx                       # In-memory session state manager & routing
    │   ├── main.jsx                      # React root entry point
    │   └── index.css                     # Tailwind CSS directives
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── package.json
```

---

## 🚀 How to Run the Applications

### 1. Start the FastAPI Backend
```bash
cd backend
python main.py
```
- API Base URL: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Start the React Frontend
```bash
cd frontend
npm run dev
```
- Application URL: [http://localhost:5173](http://localhost:5173)

---

## 🔬 Stage 2B Workflow Testing Guide

1. **Job Description Analysis**:
   - Navigate to **New Analysis**.
   - Paste job description text into the large textarea.
   - Click **Analyze Job Description**.
   - Notice the extracted requirements: required vs. preferred skills, minimum experience, and degree requirements.
2. **Bulk Resume Ingestion**:
   - Drag and drop or browse multiple `.pdf` or `.docx` files (supports 10+ resumes per batch).
   - Non-supported extensions or files exceeding 10MB are filtered out with clear notices.
   - Staged files display file names, formatted sizes, and removal buttons.
   - Click **Parse Resumes**.
   - The backend processes files in memory without saving to disk.
3. **Parsed Candidate Preview**:
   - Real-time candidate cards appear with name, contact info, experience, skills, and status.
   - Click any candidate row or **View** to inspect full details, warnings, and raw resume text.
   - Click **Connect** to open a pre-populated Gmail compose tab for candidates with detected emails.
4. **Session Synchronization**:
   - Navigate to **Candidates** to search and filter parsed profiles across the session.
   - Navigate to **Dashboard** to see the active session summary and candidate pipeline.
   - Click **Reset Session** on the New Analysis page to clear in-memory state.
