# TalentRank AI

> **Intelligent, persistent, and explainable AI recruitment SaaS platform.**  
> Screen, rank, and shortlist candidate resumes against target job descriptions with transparent multi-factor scoring, secure recruiter authentication, and cloud persistence.

---

## 🌐 Live Deployments

- **Frontend (Vercel)**: [https://frontend-ten-psi-86.vercel.app](https://frontend-ten-psi-86.vercel.app)
- **Backend API (Render)**: [https://avom.onrender.com](https://avom.onrender.com)
- **API Documentation (Swagger UI)**: [https://avom.onrender.com/docs](https://avom.onrender.com/docs)
- **Database**: MongoDB Atlas Cluster

---

## 🎨 Design Direction

TalentRank AI is styled with a calm, modern, and trustworthy editorial palette:

- **Primary Colors**:
  - **Sage Green (`#A8B5A2`)**: Active navigation states, score highlights, positive actions.
  - **Deep Olive (`#5E6B55`)**: Sidebar branding, primary CTA buttons, badges.
  - **Soft Cream (`#F2EFEA`)**: Clean, editorial background.
- **Supporting Palette**:
  - **Warm Charcoal (`#2E332D`)**: High-contrast typography and headers.
  - **Muted Sage (`#DCE3D8`)**: Subtle dividers and borders.
  - **Light Olive (`#E6E9E0`)**: Metric badge backgrounds.
  - **Soft Terracotta (`#C58C78`)**: Spared for alert and warning notifications.

---

## ⚡ Key Features & System Capabilities

### 1. Recruiter Authentication & Multi-Tenant Isolation
- **Secure Sign Up & Login**: Password hashing using `bcrypt`, input validation, email duplicate prevention, and JWT Bearer token authentication.
- **Strict Data Isolation**: Each recruiter has an isolated workspace. Analyses, candidate pools, and decision statuses are scoped exclusively to the authenticated recruiter.
- **Session Auto-Restore**: When refreshing the browser or logging back in, the recruiter's most recent active screening session and candidate rankings are automatically restored from MongoDB Atlas.

### 2. High-Performance AI Semantic Matching Engine
- **Lightweight Semantic Vectorization**: High-speed, n-gram sublinear TF-IDF vectorizer (`scikit-learn`) producing normalized semantic embeddings in **< 10ms** with zero PyTorch overhead, preventing memory exhaustion and 502 Bad Gateway timeouts on cloud tiers.
- **Transparent Multi-Factor Scoring (0–100 Scale)**:
  - **Semantic Similarity (35%)**: Contextual alignment between JD requirements and candidate resume experience.
  - **Required Skills Coverage (30%)**: Exact, normalized, and substring matching against required core competencies.
  - **Experience Relevance (20%)**: Full-time professional tenure evaluation against minimum job criteria.
  - **Education Relevance (10%)**: Degree level and field of study verification.
  - **Preferred Skills (5%)**: Bonus points for secondary qualifications.
- **Explainable Insights**: Provides recruiter-friendly explanations, key candidate strengths, and gaps/missing skills for every candidate.

### 3. Job Description Analysis & Document Ingestion
- **Automated JD Extraction**: Parses raw job postings into structured requirements (required vs. preferred skills, minimum experience, education criteria).
- **In-Memory Resume Parsing**: Zero-disk footprint document parsing supporting `.pdf` (via PyMuPDF) and `.docx` (via python-docx) across batches of 10+ resumes simultaneously.
- **Vault Storage & Preview**: Resumes are securely stored in the private file vault, enabling inline in-browser PDF/DOCX preview and direct download.

### 4. Recruiter Workspace & Candidate Pipeline
- **Decision Tracking**: Track candidates through hiring stages: `Unreviewed`, `Shortlisted`, `Maybe`, and `Rejected`. Decisions persist in MongoDB Atlas.
- **Analysis History**: Reopen past screening sessions, compare talent pools, or delete outdated analyses.
- **One-Click Candidate Outreach**: Built-in Gmail integration generates pre-filled interview invitations with recruiter and candidate details.

---

## 📁 Project Architecture

```
avom/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── api.py                    # Root API router (/api)
│   │   │   └── endpoints/
│   │   │       ├── health.py             # GET /api/health
│   │   │       ├── auth.py               # POST /api/auth/register, /login, GET /me
│   │   │       ├── jd.py                 # POST /api/jd/analyze
│   │   │       ├── resumes.py            # POST /api/resumes/parse, GET /:id/view, /:id/download
│   │   │       ├── matching.py           # POST /api/match/evaluate
│   │   │       └── analyses.py           # GET/POST/DELETE /api/analyses, status updates
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic BaseSettings & CORS configuration
│   │   │   ├── database.py               # Motor MongoDB async client lifecycle
│   │   │   ├── errors.py                 # Standardized JSON error response handler
│   │   │   └── security.py               # JWT encoding/decoding & bcrypt hashing
│   │   ├── schemas/
│   │   │   ├── auth.py                   # Recruiter auth request/response schemas
│   │   │   ├── jd.py                     # Job description extraction schemas
│   │   │   ├── resume.py                 # Candidate profile extraction schemas
│   │   │   ├── matching.py               # AI match request, scored candidate, breakdown
│   │   │   └── analysis.py               # Persistent workspace & shortlist schemas
│   │   └── services/
│   │       ├── parsers/                  # PyMuPDF and python-docx parsers
│   │       ├── extractors/               # Skills taxonomy (80+ skills), candidate contact & experience
│   │       ├── matching/                 # TF-IDF semantic vectorizer & 5-factor scoring engine
│   │       └── storage/                  # Local and MongoDB storage managers
│   ├── main.py                           # FastAPI application entry point with CORS
│   ├── requirements.txt                  # Python dependencies
│   ├── Dockerfile                        # Production container definition
│   └── tests/                            # Automated test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/                   # Modals, badges, navigation, resume viewer
│   │   ├── context/
│   │   │   └── AuthContext.jsx           # Global recruiter authentication state
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx             # Recruiter login page
│   │   │   ├── RegisterPage.jsx          # Recruiter registration page
│   │   │   ├── DashboardPage.jsx         # Executive dashboard with analytics & recent roles
│   │   │   ├── NewAnalysisPage.jsx       # JD analysis, resume upload, and AI matching
│   │   │   ├── CandidatesPage.jsx        # Searchable candidate pipeline & shortlist view
│   │   │   └── AnalysisHistoryPage.jsx   # Saved analysis history & role re-opening
│   │   ├── services/
│   │   │   ├── api.js                    # Centralized Axios client with JWT interceptor
│   │   │   └── gmailService.js           # Pre-filled Gmail communication composer
│   │   ├── App.jsx                       # Main application shell & session restoration
│   │   └── index.css                     # Editorial design tokens & Tailwind directives
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── render.yaml                           # Render cloud deployment configuration
├── Procfile                              # Container process definition
└── README.md
```

---

## 🛠️ REST API Reference

| Endpoint | Method | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `/api/health` | `GET` | Health check probe & API status | No |
| `/api/auth/register` | `POST` | Register a new recruiter account | No |
| `/api/auth/login` | `POST` | Authenticate recruiter & obtain JWT token | No |
| `/api/auth/me` | `GET` | Fetch authenticated recruiter profile | Yes |
| `/api/jd/analyze` | `POST` | Parse requirements from Job Description text | No |
| `/api/resumes/parse` | `POST` | Upload and parse multiple resume files (`.pdf`, `.docx`) | No |
| `/api/match/evaluate` | `POST` | Evaluate & rank candidates against a Job Description | No |
| `/api/resumes/{id}/view` | `GET` | Inline preview of original resume document | Yes |
| `/api/resumes/{id}/download` | `GET` | Download candidate's original resume | Yes |
| `/api/analyses` | `GET` | List saved job analyses for current recruiter | Yes |
| `/api/analyses` | `POST` | Save or update complete screening in MongoDB | Yes |
| `/api/analyses/{id}` | `GET` | Get full details of saved analysis with all candidates | Yes |
| `/api/analyses/{id}` | `DELETE` | Delete analysis and associated candidate records | Yes |
| `/api/analyses/{id}/candidates/{cid}/status` | `PATCH` | Update candidate decision status (`shortlisted`, etc.) | Yes |

---

## 💻 Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local instance or MongoDB Atlas URI)

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your MONGODB_URL and JWT_SECRET_KEY

# Start backend server
python main.py
```
- The backend will start on **`http://localhost:8000`**
- Swagger docs accessible at **`http://localhost:8000/docs`**

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```
- The frontend will start on **`http://localhost:5173`**

---

## 🔒 Security & Privacy Notes

- **Password Protection**: Passwords are never stored in plaintext and are salted and hashed using `bcrypt`.
- **JWT Protection**: Protected routes require a valid `Bearer <token>` header, automatically attached by the frontend Axios interceptor.
- **CORS Hardening**: Strict CORS configuration allowlists the production Vercel deployment and local development origins with credentials enabled.
- **In-Memory Text Processing**: Resume content is parsed directly in memory during screening. Original documents are protected with token-based authorization.

---

## 📄 License
This project is proprietary and developed for AI-assisted corporate recruitment assignments.
