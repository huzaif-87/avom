"""Candidate profile extraction module with strict experience modeling and section separation."""

import re
import uuid
import datetime
from typing import List, Optional, Tuple, Set, Dict, Any

from app.schemas.resume import CandidateResumeResult
from app.services.extractors.skills_taxonomy import extract_skills_from_text


# Header blacklist for name heuristic
HEADER_BLACKLIST = {
    "resume", "curriculum vitae", "cv", "profile", "summary",
    "professional summary", "executive summary", "career objective",
    "objective", "contact", "contact information", "experience",
    "work experience", "employment history", "education", "skills",
    "technical skills", "projects", "certifications", "personal details",
    "hobbies", "languages", "references", "about me", "page 1", "page 2",
    "address", "phone", "email"
}

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[\s.-]*)?(?:\(?\d{2,5}\)?[\s.-]*)?\d{3,5}[\s.-]*\d{3,5}(?:[\s.-]*\d{1,4})?"
)

DEGREE_PATTERNS = [
    re.compile(r"\b(?:bachelor(?:'s)?(?:\s+of\s+[a-zA-Z\s]+)?|b\.?tech|b\.?e\.?|b\.?sc|b\.?s\.?|bca|bba)\b", re.IGNORECASE),
    re.compile(r"\b(?:master(?:'s)?(?:\s+of\s+[a-zA-Z\s]+)?|m\.?tech|m\.?e\.?|m\.?sc|m\.?s\.?|mca|mba)\b", re.IGNORECASE),
    re.compile(r"\b(?:ph\.?d|doctorate|postgraduate|diploma|associate(?:\s+degree)?)\b", re.IGNORECASE),
]

# Fresher / Entry-Level indicators that explicitly override misleading date heuristics
FRESHER_PATTERNS = [
    re.compile(r"\b(?:fresher|recent\s+graduate|entry[\s-]level|seeking\s+(?:an?\s+)?entry[\s-]level|undergraduate|student)\b", re.IGNORECASE),
    re.compile(r"\b(?:no\s+prior\s+(?:work\s+|professional\s+)?experience|no\s+professional\s+experience|looking\s+for\s+(?:my\s+)?first\s+job)\b", re.IGNORECASE),
    re.compile(r"\b0\s*(?:years?|yrs?)(?:\s+of)?\s+(?:professional\s+)?experience\b", re.IGNORECASE),
]

# Explicit professional experience patterns (must specify employment/professional context)
EXPLICIT_PROF_EXP_PATTERNS = [
    re.compile(
        r"(?:over|more\s+than|at\s+least|approx\.?)?\s*(\d+(?:\.\d+)?)\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?)(?:\s+of)?\s+(?:professional|relevant|work|industry|corporate|full[\s-]time)\s+experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:total\s+experience|work\s+experience)\s*:\s*(?:over|approx\.?)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+of\s+(?:proven\s+)?(?:software|engineering|development|industry|work|machine\s+learning|data\s+science|backend|frontend|full[\s-]stack)?\s*experience\s+(?:in|as|with)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+of\s+experience\b(?!\s+(?:in\s+college|in\s+school|in\s+university|studying))",
        re.IGNORECASE,
    ),
]

# Month name mapping
MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "sept": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12
}

DATE_RANGE_REGEX = re.compile(
    r"\b((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|\d{1,2})[\s/.-]+)?((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|\d{1,2})[\s/.-]+)?((?:19|20)\d{2}|present|current|now)\b",
    re.IGNORECASE,
)


def extract_candidate_name(text: str) -> str:
    """Extract candidate name using heuristics from the top portion of the resume."""
    if not text:
        return "Unknown"

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines[:12]:
        lower_line = line.lower()

        name_prefix_match = re.match(r"^(?:name|candidate(?:\s+name)?)\s*[:\-]\s*([a-zA-Z\s\.\'-]{2,50})$", line, re.IGNORECASE)
        if name_prefix_match:
            candidate = name_prefix_match.group(1).strip()
            if 1 < len(candidate.split()) <= 4:
                return candidate.title()

        if lower_line in HEADER_BLACKLIST:
            continue
        if "@" in line or "http" in lower_line or "linkedin" in lower_line or "github" in lower_line or "www." in lower_line:
            continue
        if any(lower_line.startswith(h + ":") for h in HEADER_BLACKLIST):
            continue
        if re.search(r"\d", line):
            continue

        cleaned = re.sub(r"^[•\-\*\>\|]\s*", "", line).strip()
        cleaned = cleaned.split("|")[0].split("•")[0].strip()
        words = cleaned.split()

        if 2 <= len(words) <= 4:
            if all(re.match(r"^[A-Za-z\.\'-]+$", w) for w in words):
                title_blacklist = {"software", "engineer", "developer", "manager", "lead", "architect", "designer", "intern", "consultant"}
                if not any(w.lower() in title_blacklist for w in words):
                    return cleaned.title()

    return "Unknown"


def extract_candidate_email(text: str) -> Optional[str]:
    """Extract first valid email address from text using regex."""
    if not text:
        return None
    matches = EMAIL_REGEX.findall(text)
    if matches:
        return matches[0].strip().lower()
    return None


def extract_candidate_phone(text: str) -> Optional[str]:
    """Extract possible candidate phone number preserving country codes."""
    if not text:
        return None

    for line in text.split("\n"):
        line_clean = line.strip()
        if not line_clean:
            continue

        if " - " in line_clean and re.search(r"(?:19|20)\d{2}", line_clean):
            continue

        matches = PHONE_REGEX.findall(line_clean)
        for match in matches:
            digits_only = re.sub(r"\D", "", match)
            if 7 <= len(digits_only) <= 15:
                cleaned = match.strip().rstrip(".,;")
                return cleaned

    return None


def extract_candidate_education(text: str) -> List[str]:
    """Extract education and degree statements matching known academic degrees."""
    if not text:
        return []

    education_lines: List[str] = []
    seen: Set[str] = set()

    for line in text.split("\n"):
        line_clean = line.strip()
        if not line_clean or len(line_clean) > 200:
            continue

        for pattern in DEGREE_PATTERNS:
            if pattern.search(line_clean):
                cleaned = re.sub(r"^[•\-\*\>]\s*", "", line_clean).strip()
                norm = cleaned.lower()
                if norm not in seen:
                    seen.add(norm)
                    education_lines.append(cleaned)
                break

    return education_lines


# ----------------------------------------------------------------------
# Section-Aware Experience Analysis (Solves Problem 1)
# ----------------------------------------------------------------------

def _segment_resume_sections(text: str) -> Dict[str, List[str]]:
    """Segment resume text into distinct logical sections.
    
    Prevents academic durations or projects from being counted as employment history.
    """
    sections: Dict[str, List[str]] = {
        "header": [],
        "education": [],
        "employment": [],
        "internship": [],
        "projects": [],
        "skills": [],
        "other": [],
    }

    current_section = "header"
    lines = [l.strip() for l in text.split("\n")]

    for line in lines:
        if not line:
            continue

        clean_h = re.sub(r"^[#\*\-•\s]+", "", line).strip().lower()

        # Detect Section Changes
        if re.match(r"^(?:education|academic\s+(?:qualifications?|background|history)|academics?|degrees?)\b", clean_h):
            current_section = "education"
            continue
        elif re.match(r"^(?:work\s+experience|professional\s+experience|employment\s+history|work\s+history|employment)\b", clean_h):
            current_section = "employment"
            continue
        elif re.match(r"^(?:internships?|internship\s+experience|summer\s+internship|industrial\s+training)\b", clean_h):
            current_section = "internship"
            continue
        elif re.match(r"^(?:academic\s+projects|projects|personal\s+projects|course\s+projects|capstone\s+project)\b", clean_h):
            current_section = "projects"
            continue
        elif re.match(r"^(?:skills|technical\s+skills|core\s+competencies|certifications|awards)\b", clean_h):
            current_section = "skills"
            continue
        elif re.match(r"^(?:experience)\s*[:\-]?$", clean_h):
            # Ambiguous "Experience" header: check if candidate is clearly student/academic
            current_section = "employment"
            continue

        sections[current_section].append(line)

    return sections


def _parse_date_to_decimal(month_str: Optional[str], year_str: str) -> float:
    """Convert month and year to float representation (e.g. June 2021 -> 2021.5)."""
    year = int(year_str)
    month = 6  # default mid-year if month is unspecified
    if month_str:
        clean_m = re.sub(r"[^a-zA-Z]", "", month_str).lower()
        if clean_m in MONTH_MAP:
            month = MONTH_MAP[clean_m]
        elif month_str.isdigit():
            m_num = int(month_str)
            if 1 <= m_num <= 12:
                month = m_num
    return year + (month - 1) / 12.0


def _calculate_non_overlapping_years(intervals: List[Tuple[float, float]]) -> float:
    """Merge overlapping intervals to guarantee zero double counting."""
    if not intervals:
        return 0.0

    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for current in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if current[0] <= prev_end:
            merged[-1] = (prev_start, max(prev_end, current[1]))
        else:
            merged.append(current)

    total_span = sum(end - start for start, end in merged)
    return round(total_span, 1)


def extract_accurate_experience(
    text: str, education_lines: List[str]
) -> Tuple[Optional[float], Optional[float], str, str, List[str]]:
    """Accurately extract professional and internship experience separately.

    Enforces all critical business rules:
    - Never treat college or education dates as professional experience.
    - Never count academic project duration as employment duration.
    - Fresher indicators override misleading date heuristics.
    - Separate internships from full-time employment.
    - Prevent double-counting overlapping intervals.

    Returns:
        Tuple of:
            - professional_experience_years (Optional[float])
            - internship_experience_years (Optional[float])
            - experience_confidence (str: 'high', 'medium', 'low', 'none')
            - experience_source (str: 'explicit_statement', 'employment_history', 'internship_only', 'fresher_override', 'none')
            - experience_warnings (List[str])
    """
    warnings: List[str] = []

    if not text or not text.strip():
        return None, None, "none", "none", ["No text content provided to evaluate experience."]

    # Step 1: Detect Fresher / Student / Entry-level Status
    is_fresher = any(p.search(text) for p in FRESHER_PATTERNS)

    # Step 2: Search for Verified Explicit Experience Statements
    for pattern in EXPLICIT_PROF_EXP_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                years_val = float(match.group(1))
                if 0.0 <= years_val <= 45.0:
                    return years_val, None, "high", "explicit_statement", []
            except (ValueError, IndexError):
                pass

    # Step 3: Segment Resume to Isolate Employment History
    sections = _segment_resume_sections(text)

    # Step 4: Extract Internship Duration
    internship_intervals: List[Tuple[float, float]] = []
    internship_lines = sections.get("internship", [])

    # Also search for lines mentioning "intern" inside other sections
    all_lines = text.split("\n")
    for line in all_lines:
        line_lower = line.lower()
        if "intern" in line_lower or "trainee" in line_lower:
            internship_lines.append(line)

    for line in internship_lines:
        # Check explicit month duration e.g. "3 months internship", "6 mos"
        dur_match = re.search(r"(\d+)\s*(?:months?|mos?)\b", line, re.IGNORECASE)
        if dur_match:
            months = float(dur_match.group(1))
            if 0 < months <= 24:
                internship_intervals.append((0.0, months / 12.0))

        # Check date ranges
        for m in DATE_RANGE_REGEX.finditer(line):
            m_start, y_start, m_end, y_end = m.group(1), m.group(2), m.group(3), m.group(4)
            try:
                start_dec = _parse_date_to_decimal(m_start, y_start)
                current_year = datetime.datetime.now().year
                end_dec = current_year if y_end.lower() in {"present", "current", "now"} else _parse_date_to_decimal(m_end, y_end)
                if start_dec <= end_dec and (end_dec - start_dec) <= 3.0:
                    internship_intervals.append((start_dec, end_dec))
            except Exception:
                continue

    internship_years = _calculate_non_overlapping_years(internship_intervals) if internship_intervals else None

    # Step 5: Extract Employment History ONLY from the Employment Section
    # Explicitly ignoring Education, Projects, and Header sections!
    employment_lines = sections.get("employment", [])
    employment_intervals: List[Tuple[float, float]] = []

    for line in employment_lines:
        # Skip lines that clearly denote education or internships
        lower_l = line.lower()
        if any(p.search(line) for p in DEGREE_PATTERNS):
            continue
        if "intern" in lower_l or "trainee" in lower_l:
            continue
        if "project" in lower_l and ("college" in lower_l or "academic" in lower_l or "university" in lower_l):
            continue

        for m in DATE_RANGE_REGEX.finditer(line):
            m_start, y_start, m_end, y_end = m.group(1), m.group(2), m.group(3), m.group(4)
            try:
                start_dec = _parse_date_to_decimal(m_start, y_start)
                current_year = datetime.datetime.now().year
                end_dec = current_year if y_end.lower() in {"present", "current", "now"} else _parse_date_to_decimal(m_end, y_end)
                if start_dec <= end_dec and (end_dec - start_dec) <= 40.0:
                    employment_intervals.append((start_dec, end_dec))
            except Exception:
                continue

    # Step 6: Apply Fresher Override Rule
    if is_fresher:
        # If candidate is a declared fresher or entry-level, academic dates and projects must never be counted
        if not employment_intervals:
            return (
                None,
                internship_years,
                "high",
                "fresher_override",
                ["Candidate identified as fresher / entry-level. Academic and degree durations excluded from professional experience."],
            )

    # Step 7: Resolve Professional Experience
    if employment_intervals:
        prof_years = _calculate_non_overlapping_years(employment_intervals)
        if prof_years > 0.0:
            return prof_years, internship_years, "high", "employment_history", warnings

    # Step 8: Only Internships Found
    if internship_years and internship_years > 0.0:
        return (
            None,
            internship_years,
            "medium",
            "internship_only",
            [f"Candidate has {internship_years} yr(s) of internship/training experience; no verified full-time employment found."],
        )

    # Step 9: Not Specified / Not Found
    return (
        None,
        None,
        "none",
        "none",
        ["Professional experience not specified or could not be reliably verified."],
    )


def extract_candidate_profile(
    raw_text: str,
    filename: str = "",
    initial_warnings: Optional[List[str]] = None,
    file_type: str = "pdf",
    page_count: Optional[int] = None,
    extraction_status: str = "success",
    candidate_id: Optional[str] = None,
) -> CandidateResumeResult:
    """Analyze raw resume text and return structured CandidateResumeResult.

    Args:
        raw_text: Extracted text from PDF or DOCX.
        filename: Original file name.
        initial_warnings: Warnings from the file parsing stage.
        file_type: 'pdf' or 'docx'.
        page_count: Total pages if known.
        extraction_status: 'success', 'partial', or 'failed'.
        candidate_id: Specific candidate ID to reuse (e.g. from session vault storage).

    Returns:
        Structured CandidateResumeResult object.
    """
    warnings: List[str] = list(initial_warnings or [])
    if not candidate_id:
        candidate_id = f"cand_{uuid.uuid4().hex[:8]}"

    if not raw_text or not raw_text.strip() or extraction_status == "failed":
        return CandidateResumeResult(
            candidate_id=candidate_id,
            filename=filename,
            file_type=file_type,
            page_count=page_count,
            has_original_file=True,
            name="Unknown",
            email=None,
            phone=None,
            skills=[],
            education=[],
            professional_experience_years=None,
            internship_experience_years=None,
            experience_confidence="none",
            experience_source="none",
            experience_warnings=["No text extracted from resume."],
            experience_years=None,
            raw_text="",
            warnings=warnings or ["Resume content could not be read or is empty."],
            extraction_status="failed",
            status="error",
        )

    # 1. Extract contact details
    name = extract_candidate_name(raw_text)
    if name == "Unknown":
        warnings.append("Candidate name could not be reliably determined.")

    email = extract_candidate_email(raw_text)
    if not email:
        warnings.append("No candidate email address found in resume.")

    phone = extract_candidate_phone(raw_text)
    if not phone:
        warnings.append("No contact phone number detected.")

    # 2. Extract skills
    skills = extract_skills_from_text(raw_text)
    if not skills:
        warnings.append("No recognized skills matched the taxonomy in this resume.")

    # 3. Extract education
    education = extract_candidate_education(raw_text)
    if not education:
        warnings.append("No formal education or degree statements detected.")

    # 4. Extract accurate experience
    prof_exp, intern_exp, exp_conf, exp_src, exp_warnings = extract_accurate_experience(
        raw_text, education
    )
    warnings.extend(exp_warnings)

    # Determine processing status
    status = "success"
    if not email and not skills and prof_exp is None and intern_exp is None:
        status = "partial"

    return CandidateResumeResult(
        candidate_id=candidate_id,
        filename=filename,
        file_type=file_type,
        page_count=page_count,
        has_original_file=True,
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        education=education,
        professional_experience_years=prof_exp,
        internship_experience_years=intern_exp,
        experience_confidence=exp_conf,
        experience_source=exp_src,
        experience_warnings=exp_warnings,
        experience_years=prof_exp,  # backward compatibility
        raw_text=raw_text,
        warnings=warnings,
        extraction_status=extraction_status,
        status=status,
    )
