"""Job description (JD) rule-based analyzer and requirement extractor."""

import re
from typing import List, Optional, Tuple, Set

from app.schemas.jd import JDAnalyzeResponse
from app.services.extractors.skills_taxonomy import extract_skills_from_text


# Section header detection regex patterns
REQUIRED_SECTION_PATTERN = re.compile(
    r"^(?:(?:core\s+|basic\s+|minimum\s+)?requirements?|(?:required|minimum|basic)\s+qualifications?|must[\s-]haves?|what\s+you(?:'ll)?\s+need|eligibility(?:\s+criteria)?|who\s+you\s+are)\s*[:\-]?$",
    re.IGNORECASE,
)

PREFERRED_SECTION_PATTERN = re.compile(
    r"^(?:preferred\s+(?:qualifications?|skills?|requirements?)|nice[\s-]to[\s-]haves?|good[\s-]to[\s-]haves?|bonus(?:\s+points|\s+qualifications?)?|pluses|desired\s+(?:skills?|qualifications?)|what\s+sets\s+you\s+apart)\s*[:\-]?$",
    re.IGNORECASE,
)

# Minimum experience patterns in JD
MIN_EXPERIENCE_PATTERNS = [
    re.compile(
        r"(?:minimum|at\s+least|min\.?|around|approx\.?)?\s*(\d+(?:\.\d+)?)\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?)(?:\s+of)?\s+(?:relevant\s+|professional\s+|hands-on\s+|work\s+|industry\s+|software\s+|technical\s+)?(?:experience|exp)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:experience|experience\s+required)\s*[:\-]\s*(?:at\s+least|minimum)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:proven\s+experience|experience\s+with|experience\s+in)",
        re.IGNORECASE,
    ),
]

# Degree keywords in JD
JD_DEGREE_PATTERN = re.compile(
    r"\b(?:bachelor(?:'s)?|b\.?tech|b\.?e\.?|b\.?sc|b\.?s\.?|master(?:'s)?|m\.?tech|m\.?e\.?|m\.?sc|m\.?s\.?|mba|mca|ph\.?d|degree\s+in\s+[a-zA-Z\s]+)\b",
    re.IGNORECASE,
)


def extract_minimum_experience(text: str) -> Optional[float]:
    """Extract minimum required years of experience from job description text."""
    if not text:
        return None

    found_values: List[float] = []

    for pattern in MIN_EXPERIENCE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                val = float(match.group(1))
                if 0.0 <= val <= 30.0:
                    found_values.append(val)
            except (ValueError, IndexError):
                continue

    if found_values:
        # Minimum required experience is typically the lowest non-zero threshold specified
        non_zero = [v for v in found_values if v > 0]
        return min(non_zero) if non_zero else found_values[0]

    return None


def extract_education_requirements(text: str) -> List[str]:
    """Extract education statements from job description text."""
    if not text:
        return []

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    education_lines: List[str] = []
    seen: Set[str] = set()

    for line in lines:
        if len(line) > 250:
            continue
        if JD_DEGREE_PATTERN.search(line):
            cleaned = re.sub(r"^[•\-\*\>]\s*", "", line).strip()
            norm = cleaned.lower()
            if norm not in seen:
                seen.add(norm)
                education_lines.append(cleaned)

    return education_lines


def analyze_job_description(jd_text: str) -> JDAnalyzeResponse:
    """Analyze a job description and extract skills, qualifications, and experience benchmarks.

    This is a rule-based parser that partitions text by section headers and matches
    against the modular skills taxonomy. It does not pretend to be an AI model.

    Args:
        jd_text: Raw text of the job description.

    Returns:
        Structured JDAnalyzeResponse.
    """
    if not jd_text or not jd_text.strip():
        return JDAnalyzeResponse(
            extracted_skills=[],
            required_skills=[],
            preferred_skills=[],
            minimum_experience=None,
            education_requirements=[],
            required_qualifications=[],
            preferred_qualifications=[],
            summary="Empty job description provided.",
        )

    lines = [line.strip() for line in jd_text.split("\n")]

    current_section = "general"
    required_lines: List[str] = []
    preferred_lines: List[str] = []

    for line in lines:
        if not line:
            continue

        clean_header_check = re.sub(r"^[#\*\-•\s]+", "", line).strip()

        if REQUIRED_SECTION_PATTERN.match(clean_header_check):
            current_section = "required"
            continue
        elif PREFERRED_SECTION_PATTERN.match(clean_header_check):
            current_section = "preferred"
            continue
        elif re.match(r"^(?:benefits|perks|about\s+(?:us|the\s+company)|responsibilities|what\s+you(?:'ll)?\s+do)\b", clean_header_check, re.IGNORECASE):
            current_section = "general"
            continue

        # Save qualification statements
        cleaned_bullet = re.sub(r"^[•\-\*\>]\s*", "", line).strip()
        if len(cleaned_bullet) >= 10:
            if current_section == "required":
                required_lines.append(cleaned_bullet)
            elif current_section == "preferred":
                preferred_lines.append(cleaned_bullet)

    # Extract all skills from full text
    all_skills = extract_skills_from_text(jd_text)

    # Extract skills specifically from required and preferred sections
    req_text = " \n ".join(required_lines)
    pref_text = " \n ".join(preferred_lines)

    required_skills = extract_skills_from_text(req_text) if req_text else []
    preferred_skills = extract_skills_from_text(pref_text) if pref_text else []

    # If section headers were not detected, classify based on inline keywords
    if not required_skills and not preferred_skills and all_skills:
        for skill in all_skills:
            # Check if skill appears near "preferred", "nice to have", "plus"
            pref_match = re.search(rf"\b(?:preferred|plus|nice\s+to\s+have|bonus)\b[^\n]*\b{re.escape(skill)}\b", jd_text, re.IGNORECASE)
            if pref_match:
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)
    elif not required_skills and all_skills:
        # Default skills not marked as preferred into required
        required_skills = [s for s in all_skills if s not in preferred_skills]

    # Extract minimum experience
    min_exp = extract_minimum_experience(jd_text)

    # Extract education requirements
    edu_reqs = extract_education_requirements(jd_text)

    # Generate transparent summary
    summary_parts = [f"Extracted {len(all_skills)} skill(s)"]
    if required_skills:
        summary_parts.append(f"{len(required_skills)} required")
    if preferred_skills:
        summary_parts.append(f"{len(preferred_skills)} preferred")
    if min_exp is not None:
        summary_parts.append(f"minimum {min_exp} year(s) experience")
    if edu_reqs:
        summary_parts.append(f"{len(edu_reqs)} education criteria")

    summary = "; ".join(summary_parts) + "."

    return JDAnalyzeResponse(
        extracted_skills=all_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        minimum_experience=min_exp,
        education_requirements=edu_reqs,
        required_qualifications=required_lines,
        preferred_qualifications=preferred_lines,
        summary=summary,
    )
