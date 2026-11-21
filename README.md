# TalentRank AI

> **Assistive candidate screening and resume matching platform for recruiters.**  
> Evaluates candidate resumes against job description criteria using TF-IDF n-gram text similarity, multi-factor scoring, secure recruiter authentication, and persistent cloud storage.

---

## 🌐 Live Deployments & Repository

- **Frontend Application (Vercel)**: [https://frontend-ten-psi-86.vercel.app](https://frontend-ten-psi-86.vercel.app)
- **Backend API (Render)**: [https://avom.onrender.com](https://avom.onrender.com)
- **Interactive API Documentation (Swagger UI)**: [https://avom.onrender.com/docs](https://avom.onrender.com/docs)
- **GitHub Repository**: [https://github.com/huzaif-87/avom](https://github.com/huzaif-87/avom)
- **Database**: MongoDB Atlas Cluster

---

## 📸 Application Screenshots

The following interface views illustrate the recruiter workflow across the platform. Image files can be placed in the `docs/screenshots/` directory using the referenced filenames below.

| View | Description | Screenshot Placeholder |
| :--- | :--- | :--- |
| **Recruiter Dashboard** | Metric overview, screening statistics, and recent position evaluations. | `docs/screenshots/01-dashboard.png` |
| **Job Description Analysis** | Extracted technical skills (required vs. preferred), experience, and degree requirements. | `docs/screenshots/02-jd-analysis.png` |
| **Resume Upload Zone** | Multi-file drop zone for batch document parsing (`.pdf`, `.docx`) with validation notices. | `docs/screenshots/03-resume-upload.png` |
| **Candidate Ranking** | Stably sorted candidate cards displaying composite match percentages and primary signals. | `docs/screenshots/04-candidate-ranking.png` |
| **Score Breakdown & Detail** | Comprehensive candidate view with dimensional scoring, matched/missing skills, and explanations. | `docs/screenshots/05-candidate-details.png` |
| **Shortlist Pipeline** | Recruiter decision tracking across `Shortlisted`, `Maybe`, `Rejected`, and `Unreviewed` tiers. | `docs/screenshots/06-shortlist.png` |
| **Analysis History** | Archive of past job assessments with one-click workspace restoration. | `docs/screenshots/07-analysis-history.png` |
| **Recruiter Authentication** | Secure sign-up and login interface with input validation and password strength checks. | `docs/screenshots/08-auth.png` |

> *To populate screenshots in your own deployment, capture 1920×1080 images of the application tabs, save them into `docs/screenshots/` matching the filenames above, and commit them to the repository.*

---

## ⚖️ Responsible AI & Ethical Hiring Disclosure

TalentRank AI is designed strictly as an **assistive screening and prioritization tool** to help recruiters organize and review applicant batches. It does not replace human judgment.

> [!IMPORTANT]
> **Human-in-the-Loop Principle**: All employment decisions—including interview selection, advancement, and rejection—must be reviewed and confirmed by qualified human recruiters or hiring managers.

- **Assistive Scoring**: Automated match scores reflect lexical and heuristic similarity between the submitted resume text and the job description. They do not evaluate candidate character, adaptability, or unstated potential.
- **Parsing Limitations**: Automated text extraction from complex, multi-column, or graphic-heavy resume formats can occasionally omit details or misinterpret non-standard headers. Recruiters should always consult the original resume document (accessible via the inline document viewer) prior to making decisions.
- **No Automated Rejections**: Candidates should not be disqualified solely on the basis of an automated score.
- **Fairness & Consistency**: The scoring algorithm applies identical criteria across all resumes within a batch, ignoring non-job-relevant demographic identifiers.

---

## 🧠 Matching Engine & Algorithmic Architecture

### Terminology & Matching Approach
The deployed matching pipeline utilizes **scikit-learn TF-IDF (Term Frequency–Inverse Document Frequency) vectorization with n-gram features and cosine similarity**, complemented by deterministic heuristic extractors.

- **Why Not Sentence Transformers / PyTorch?**  
  Early prototypes utilized transformer models (`sentence-transformers/all-MiniLM-L6-v2`). However, PyTorch and transformer weight dependencies require over 500 MB of resident memory (RSS) and trigger container OOM (Out Of Memory) process kills and 502 Bad Gateway errors on container tiers with 512 MB memory constraints (such as Render Free Tier).
- **The Engineering Trade-Off**:  
  Replacing heavy neural models with a `scikit-learn` TF-IDF vectorizer reduces memory consumption from over 500 MB down to **under 50 MB**, completely eliminates model cold-start delays, and delivers execution times under cloud environments.  
  *Trade-off consideration*: While TF-IDF with unigrams, bigrams, and trigrams captures term frequency and phrase co-occurrence effectively, it relies on lexical overlap and does not offer the deep contextual language understanding or synonym resolution of large transformer embeddings.

### Five-Factor Weighted Scoring Model
Every candidate is evaluated on a transparent **0–100 weighted scale**:

$$\text{Final Score} = (0.35 \times \text{Text Similarity}) + (0.30 \times \text{Required Skills}) + (0.20 \times \text{Experience}) + (0.10 \times \text{Education}) + (0.05 \times \text{Preferred Skills})$$

| Component | Weight | Implementation Details |
| :--- | :---: | :--- |
| **Text Similarity** | **35%** | Vectorizes JD and candidate texts using sublinear TF-IDF with n-gram range `(1, 3)`, stop-word filtering, and L2 normalization; evaluates pairwise cosine similarity. |
| **Required Skills** | **30%** | Compares extracted candidate skills against mandatory competencies extracted from the JD using normalized, exact, and phrase-tolerant substring matching. |
| **Relevant Experience** | **20%** | Evaluates verified full-time professional experience tenure against the minimum years requested in the JD. |
| **Education Match** | **10%** | Evaluates candidate degree level (Bachelor's, Master's, Ph.D.) and academic discipline against position requirements. |
| **Preferred Skills** | **5%** | Evaluates secondary or bonus qualifications identified in the job specification. |

---

## 🎨 Visual Design System

TalentRank AI features an editorial-inspired design system:

- **Sage Green (`#A8B5A2`)**: Active states, match indicators, primary accents.
- **Deep Olive (`#5E6B55`)**: Primary buttons, sidebar branding, key callouts.
- **Soft Cream (`#F2EFEA`)**: Application background.
- **Warm Charcoal (`#2E332D`)**: High-contrast typography and headers.
- **Muted Sage (`#DCE3D8`)**: Subtle borders and dividers.
- **Light Olive (`#E6E9E0`)**: Secondary pill backgrounds and badge containers.
- **Soft Terracotta (`#C58C78`)**: Warning and error states only.

---

## 🔍 Factual Technical Audit & Features

- **In-Memory Text Processing & File Vault**:  
  Text extraction (PyMuPDF for `.pdf`, python-docx for `.docx`) is executed in memory during upload. Concurrently, original uploaded resume binaries are saved to the server's private file vault directory (`storage/resumes` or `/tmp/resumes`) to power inline browser preview (`/api/resumes/{id}/view`) and downloads (`/api/resumes/{id}/download`).
- **Batch Processing**:  
  The `/api/resumes/parse` endpoint accepts multiple file uploads simultaneously (`UploadFile` list) and processes resumes sequentially with per-file status handling.
- **Multi-Tenant Recruiter Isolation**:  
  Recruiter accounts are password-protected with `bcrypt` hashes. Saved analyses, candidate pipelines, and review decisions in MongoDB Atlas are partitioned by `recruiter_id`. All workspace mutations require a validated JWT Bearer token.
- **CORS Hardening**:  
  FastAPI's `CORSMiddleware` allowlists the production Vercel deployment URL (`https://frontend-ten-psi-86.vercel.app`), Vercel preview URLs via regular expression, and local developer hosts (`localhost:5173`, `127.0.0.1:5173`, `localhost:3000`).
- **Session Auto-Restoration**:  
  Upon page refresh or re-login, the frontend automatically restores the recruiter's most recent active screening session from MongoDB Atlas, populating the dashboard metrics, candidate pool, and shortlist.

---

## 📁 Repository Directory Structure

```
avom/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── api.py                    # Root API router mounting all endpoints
│   │   │   └── endpoints/
│   │   │       ├── health.py             # GET /api/health probe
│   │   │       ├── auth.py               # POST /register, /login, GET /me
│   │   │       ├── jd.py                 # POST /api/jd/analyze
│   │   │       ├── resumes.py            # POST /parse, GET /:id/view, GET /:id/download
│   │   │       ├── matching.py           # POST /api/match/evaluate
│   │   │       └── analyses.py           # CRUD /api/analyses, status tracking
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic Settings, CORS origins, environment
│   │   │   ├── database.py               # Motor async MongoDB client & lifecycle
│   │   │   ├── errors.py                 # Centralized HTTP error handlers
│   │   │   └── security.py               # Password hashing (bcrypt) & JWT operations
│   │   ├── schemas/
│   │   │   ├── auth.py                   # Sign-up, login, token schemas
│   │   │   ├── jd.py                     # Job description extraction schemas
│   │   │   ├── resume.py                 # Candidate extraction result schemas
│   │   │   ├── matching.py               # Evaluation request, ranking response schemas
│   │   │   └── analysis.py               # Persistent workspace & shortlist schemas
│   │   └── services/
│   │       ├── parsers/                  # PyMuPDF & python-docx extraction logic
│   │       ├── extractors/               # Skills taxonomy (80+ skills), contact, experience
│   │       ├── matching/                 # TF-IDF vectorizer & 5-factor scoring engine
│   │       └── storage/                  # Local resume file vault storage manager
│   ├── main.py                           # FastAPI application entry point
│   ├── requirements.txt                  # Python dependencies
│   ├── Dockerfile                        # Multi-stage production container definition
│   └── tests/                            # Automated test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/                   # Modals, status pills, badges, resume viewer
│   │   ├── context/
│   │   │   └── AuthContext.jsx           # Global recruiter authentication state provider
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx             # Recruiter sign-in page
│   │   │   ├── RegisterPage.jsx          # Recruiter registration page
│   │   │   ├── DashboardPage.jsx         # Executive dashboard with analytics & recent roles
│   │   │   ├── NewAnalysisPage.jsx       # JD analysis, resume upload, and AI matching
│   │   │   ├── CandidatesPage.jsx        # Searchable candidate pipeline & shortlist view
│   │   │   └── AnalysisHistoryPage.jsx   # Saved analysis history & role re-opening
│   │   ├── services/
│   │   │   ├── api.js                    # Centralized Axios client with JWT interceptor
│   │   │   └── gmailService.js           # Pre-filled Gmail communication composer
│   │   ├── App.jsx                       # Application routing & session restoration
│   │   └── index.css                     # Editorial design tokens & Tailwind directives
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── render.yaml                           # Render cloud deployment specification
├── Procfile                              # Container process definition
└── README.md
```

---

## 🛠️ Complete REST API Reference

| Endpoint | Method | Description | Auth Required |
| :--- | :---: | :--- | :---: |
| `/api/health` | `GET` | Health check probe & service status | No |
| `/api/auth/register` | `POST` | Register a new recruiter account | No |
| `/api/auth/login` | `POST` | Authenticate recruiter & obtain JWT access token | No |
| `/api/auth/me` | `GET` | Retrieve authenticated recruiter profile | **Yes (Bearer Token)** |
| `/api/auth/logout` | `POST` | Invalidate recruiter session | Optional |
| `/api/jd/analyze` | `POST` | Parse criteria from Job Description text | No |
| `/api/resumes/parse` | `POST` | Parse uploaded resume batch (`.pdf`, `.docx`) | No |
| `/api/match/evaluate` | `POST` | Rank and score candidates against a Job Description | No |
| `/api/resumes/{id}/view` | `GET` | Inline preview of original resume document | **Yes (Bearer / Query)** |
| `/api/resumes/{id}/download` | `GET` | Download original uploaded resume binary | **Yes (Bearer / Query)** |
| `/api/resumes/{id}` | `DELETE` | Remove resume document from storage | Optional |
| `/api/analyses` | `GET` | List saved job analyses for current recruiter | **Yes (Bearer Token)** |
| `/api/analyses` | `POST` | Persist or update job analysis & candidates | **Yes (Bearer Token)** |
| `/api/analyses/{id}` | `GET` | Retrieve full analysis with scored candidates | **Yes (Bearer Token)** |
| `/api/analyses/{id}` | `DELETE` | Delete analysis and associated candidate records | **Yes (Bearer Token)** |
| `/api/analyses/{id}/candidates/{cid}/status` | `PATCH` | Update candidate decision status (`shortlisted`, etc.) | **Yes (Bearer Token)** |

---

## 💻 Local Installation & Setup Guide

### Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 installed
- **Node.js**: Version 18.x or 20.x installed
- **MongoDB**: A running local MongoDB instance or a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster connection URI

---

### Step 1: Backend Setup (Windows PowerShell Primary)

Open a **PowerShell** terminal in the repository root:

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1

# Note: If PowerShell shows an Execution_Policies error, run:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Create local environment configuration
Copy-Item .env.example .env
```

#### Windows Command Prompt (CMD) Alternative:
```cmd
cd backend
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

#### Linux / macOS Alternative:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

#### Configuring `backend/.env`:
Open `backend/.env` in your text editor and verify the configuration:

```ini
PROJECT_NAME="TalentRank AI"
VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=True
API_PREFIX="/api"
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:3000"]

# MongoDB Connection (Local or Atlas)
MONGODB_URL="mongodb://localhost:27017"
DATABASE_NAME="talentrank_ai"

# JWT Security (Generate a secure random key in production)
JWT_SECRET_KEY="replace-with-a-secure-random-secret-key-in-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Private Resume File Vault
RESUME_STORAGE_DIR="storage/resumes"
```

#### Run the Backend Server:
```powershell
python main.py
```
- API is available at: **`http://localhost:8000`**
- Interactive Swagger UI: **`http://localhost:8000/docs`**
- Health Probe: **`http://localhost:8000/api/health`**

---

### Step 2: Frontend Setup

Open a **separate** terminal window:

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Set environment variables (defaults to localhost:8000)
Copy-Item .env.example .env
```

#### Run the Frontend Development Server:
```powershell
npm run dev
```
- Application is available at: **`http://localhost:5173`**

---

## 🔒 Security & Privacy Practices

- **Password Cryptography**: Passwords are never stored in plain text; they are salted and hashed using `bcrypt`.
- **JWT Protection**: Secured endpoints require a valid `Bearer <token>` authorization header, managed via HTTP interceptors in the frontend client.
- **Cross-Origin Protection**: Strict CORS origin allowlisting restricts browser requests to authenticated client domains.
- **Multi-Tenant Separation**: All queries in the candidate and analysis stores are scoped strictly to the authenticated recruiter's ID (`recruiter_id`).

---

## 📄 Proprietary Ownership Notice

This software is proprietary and developed for AI-assisted corporate talent acquisition workflows. All rights reserved.
