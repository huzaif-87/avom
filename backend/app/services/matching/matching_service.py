"""Stage 3 Transparent Weighted Scoring Engine.

Computes normalized dimensional match scores and composite overall score:
- Semantic similarity: 35%
- Required skill coverage: 30%
- Relevant experience: 20%
- Education relevance: 10%
- Preferred/additional skills: 5%

Enforces strict rules:
- No data fabrication: missing candidate fields penalize or explain score reduction.
- Explainable outputs: returns matched/missing skills, strengths, gaps, and human explanation.
- Deterministic, testable, and modular.
"""

from typing import List, Tuple, Optional, Dict, Any, Set
import re
from app.schemas.matching import MatchBreakdown, ScoredCandidate
from app.schemas.resume import CandidateResumeResult
from app.schemas.jd import JDAnalyzeResponse


def _normalize_skill(s: str) -> str:
    """Standardize skill string for case-insensitive and punctuation-tolerant matching."""
    if not s:
        return ""
    # Replace dots/hyphens with space or strip
    cleaned = re.sub(r"[^\w\s\+\#]", " ", s.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def evaluate_skill_coverage(
    candidate_skills: List[str], target_skills: List[str]
) -> Tuple[List[str], List[str], float]:
    """Compare candidate skills against a target skill set.

    Returns:
        Tuple of (matched_skills, missing_skills, coverage_ratio)
    """
    if not target_skills:
        # If the JD specifies no skills in this category, grant neutral full coverage
        return [], [], 1.0

    cand_set: Set[str] = {_normalize_skill(s) for s in candidate_skills if s}
    cand_original_lower = {s.lower().strip() for s in candidate_skills if s}

    matched: List[str] = []
    missing: List[str] = []

    for target in target_skills:
        target_norm = _normalize_skill(target)
        target_lower = target.lower().strip()

        # Check exact or normalized match, or substring match for phrases like 'react.js' vs 'react'
        is_match = (
            target_norm in cand_set
            or target_lower in cand_original_lower
            or any(
                target_norm == cs
                or (len(target_norm) > 2 and (target_norm in cs or cs in target_norm))
                for cs in cand_set
            )
        )

        if is_match:
            matched.append(target)
        else:
            missing.append(target)

    coverage = len(matched) / len(target_skills) if target_skills else 1.0
    return matched, missing, float(coverage)


def evaluate_experience(
    candidate_years: Optional[float],
    min_required_years: Optional[float],
    internship_years: Optional[float] = None,
    experience_source: str = "none",
) -> Tuple[float, str]:
    """Compare candidate experience against JD minimum requirements.

    Returns:
        Tuple of (normalized_score, qualitative_description)
    """
    if min_required_years is None or min_required_years <= 0.0:
        # No minimum experience requirement stated in JD
        if candidate_years is not None and candidate_years > 0:
            return 1.0, f"Candidate has {candidate_years} yrs verified experience (no minimum required)"
        if experience_source == "fresher_override":
            return 0.9, "Fresher / entry-level candidate (no minimum experience required)"
        return 0.8, "Experience not specified (no minimum required by role)"

    # Role requires specific minimum years
    if candidate_years is None:
        if experience_source == "fresher_override":
            if min_required_years <= 1.0:
                # Entry level role fits fresher with internships
                intern_note = f" with {internship_years} yrs internship" if internship_years else ""
                return 0.7, f"Fresher candidate{intern_note} for entry-level role (req: {min_required_years} yr)"
            return 0.2, f"Fresher candidate does not meet the minimum {min_required_years} yrs professional experience"
        
        # Missing / unknown experience
        if internship_years and internship_years > 0:
            return 0.4, f"No full-time experience verified; has {internship_years} yrs internship (req: {min_required_years} yrs)"
        return 0.1, f"Experience not detected in resume (role requires {min_required_years} yrs)"

    # Candidate has verified experience
    ratio = candidate_years / min_required_years
    if ratio >= 1.0:
        if ratio >= 2.0 and min_required_years >= 2.0:
            return 1.0, f"Exceeds requirement: {candidate_years} yrs vs {min_required_years} yrs required"
        return 1.0, f"Meets requirement: {candidate_years} yrs vs {min_required_years} yrs required"
    elif ratio >= 0.7:
        return 0.75, f"Close to requirement: {candidate_years} yrs vs {min_required_years} yrs required"
    elif ratio >= 0.4:
        return 0.5, f"Partially meets requirement: {candidate_years} yrs vs {min_required_years} yrs required"
    else:
        return 0.25, f"Below requirement: {candidate_years} yrs vs {min_required_years} yrs required"


def evaluate_education(
    candidate_education: List[str], jd_education_reqs: List[str]
) -> Tuple[float, str]:
    """Compare candidate degrees against JD education criteria.

    Returns:
        Tuple of (normalized_score, qualitative_description)
    """
    if not jd_education_reqs:
        # JD did not specify explicit degrees
        if candidate_education:
            return 1.0, f"Candidate holds {candidate_education[0]} (no specific degree required)"
        return 0.8, "No specific degree requirements stated in job description"

    if not candidate_education:
        return 0.2, f"No degree detected in resume (role prefers/requires {jd_education_reqs[0]})"

    cand_text = " ".join(candidate_education).lower()
    jd_text = " ".join(jd_education_reqs).lower()

    # Degree level hierarchy check
    has_masters = any(term in cand_text for term in ["master", "m.tech", "m.e.", "m.s.", "msc", "mba", "mca", "postgraduate"])
    has_bachelors = any(term in cand_text for term in ["bachelor", "b.tech", "b.e.", "b.s.", "bsc", "bca", "undergraduate"])
    has_phd = any(term in cand_text for term in ["ph.d", "phd", "doctorate"])

    req_masters = any(term in jd_text for term in ["master", "m.tech", "m.s.", "msc", "mba"])
    req_phd = any(term in jd_text for term in ["ph.d", "phd", "doctorate"])
    req_bachelors = any(term in jd_text for term in ["bachelor", "b.tech", "b.e.", "b.s.", "degree"])

    if req_phd:
        if has_phd:
            return 1.0, "Meets PhD / Doctorate educational requirement"
        if has_masters:
            return 0.6, "Candidate holds Master's degree; PhD preferred/required"
        return 0.4, "Education below PhD requirement"

    if req_masters:
        if has_phd or has_masters:
            return 1.0, f"Meets Master's degree requirement ({candidate_education[0]})"
        if has_bachelors:
            return 0.75, f"Holds Bachelor's degree ({candidate_education[0]}); Master's preferred/required"
        return 0.3, "Does not meet Master's requirement"

    if req_bachelors:
        if has_phd or has_masters or has_bachelors:
            return 1.0, f"Meets degree requirement ({candidate_education[0]})"
        return 0.5, f"Relevant technical background ({candidate_education[0]})"

    # Default general match
    return 0.9, f"Relevant qualification: {candidate_education[0]}"


def compute_candidate_match(
    candidate: CandidateResumeResult,
    jd_analysis: JDAnalyzeResponse,
    semantic_similarity: float,
) -> ScoredCandidate:
    """Calculate the complete Stage 3 AI Match for a single candidate.

    Scoring Weights (Total = 100):
    - Semantic similarity: 35%
    - Required skill coverage: 30%
    - Relevant experience: 20%
    - Education relevance: 10%
    - Preferred/additional skills: 5%
    """
    # 1. Semantic Similarity Component (35 pts)
    # Cosine similarity is in [0.0, 1.0]
    sem_sim = max(0.0, min(1.0, float(semantic_similarity)))
    sem_score = round(sem_sim * 35.0, 2)

    # 2. Required Skills Component (30 pts)
    req_skills = jd_analysis.required_skills or jd_analysis.extracted_skills
    matched_req, missing_req, req_cov = evaluate_skill_coverage(
        candidate.skills, req_skills
    )
    req_score = round(req_cov * 30.0, 2)

    # 3. Preferred Skills Component (5 pts)
    pref_skills = jd_analysis.preferred_skills
    matched_pref, missing_pref, pref_cov = evaluate_skill_coverage(
        candidate.skills, pref_skills
    )
    pref_score = round(pref_cov * 5.0, 2)

    # 4. Relevant Experience Component (20 pts)
    prof_years = (
        candidate.professional_experience_years
        if candidate.professional_experience_years is not None
        else candidate.experience_years
    )
    intern_years = candidate.internship_experience_years
    exp_cov, exp_desc = evaluate_experience(
        candidate_years=prof_years,
        min_required_years=jd_analysis.minimum_experience,
        internship_years=intern_years,
        experience_source=candidate.experience_source,
    )
    exp_score = round(exp_cov * 20.0, 2)

    # 5. Education Relevance Component (10 pts)
    edu_cov, edu_desc = evaluate_education(
        candidate_education=candidate.education,
        jd_education_reqs=jd_analysis.education_requirements,
    )
    edu_score = round(edu_cov * 10.0, 2)

    # Total Overall Score (0 - 100)
    total_score = round(sem_score + req_score + exp_score + edu_score + pref_score, 1)
    total_score = max(0.0, min(100.0, total_score))

    # Compile Breakdown
    breakdown = MatchBreakdown(
        semantic_similarity=round(sem_sim, 3),
        semantic_score=sem_score,
        required_skill_coverage=round(req_cov, 3),
        required_skills_score=req_score,
        experience_relevance=round(exp_cov, 3),
        experience_score=exp_score,
        education_relevance=round(edu_cov, 3),
        education_score=edu_score,
        preferred_skill_coverage=round(pref_cov, 3),
        preferred_skills_score=pref_score,
    )

    # Strengths Analysis
    strengths: List[str] = []
    if sem_sim >= 0.75:
        strengths.append(f"Strong semantic alignment ({int(sem_sim * 100)}%) with job responsibilities and domain context.")
    elif sem_sim >= 0.60:
        strengths.append(f"Good semantic relevance ({int(sem_sim * 100)}%) to the role description.")

    if matched_req:
        strengths.append(f"Possesses {len(matched_req)} core required skill(s): {', '.join(matched_req[:4])}{'...' if len(matched_req) > 4 else ''}.")

    if matched_pref:
        strengths.append(f"Brings {len(matched_pref)} preferred/bonus skill(s): {', '.join(matched_pref[:3])}.")

    if exp_cov >= 1.0:
        strengths.append(exp_desc)

    if edu_cov >= 1.0 and candidate.education:
        strengths.append(f"Strong educational background: {candidate.education[0]}.")

    # Gaps Analysis
    gaps: List[str] = []
    if missing_req:
        gaps.append(f"Missing {len(missing_req)} required skill(s): {', '.join(missing_req[:4])}{'...' if len(missing_req) > 4 else ''}.")

    if exp_cov < 0.7:
        gaps.append(exp_desc)

    if edu_cov < 0.7:
        gaps.append(edu_desc)

    if not candidate.email:
        gaps.append("Missing candidate contact email in resume.")

    if candidate.warnings:
        gaps.extend(candidate.warnings[:2])

    # Recruiter-friendly Short Explanation
    if total_score >= 80.0:
        summary_tone = "Excellent match"
    elif total_score >= 65.0:
        summary_tone = "Strong contender"
    elif total_score >= 50.0:
        summary_tone = "Moderate match"
    else:
        summary_tone = "Limited alignment"

    skills_summary = (
        f"{len(matched_req)} of {len(req_skills)} required skills matched"
        if req_skills
        else "broad skill alignment"
    )

    explanation = (
        f"{summary_tone} ({total_score}%). Candidate demonstrates {int(sem_sim * 100)}% semantic relevance with {skills_summary}. "
        f"{exp_desc}. {edu_desc}."
    )

    return ScoredCandidate(
        candidate_id=candidate.candidate_id,
        rank=1,  # Rank will be assigned stably after sorting batch
        overall_match_score=total_score,
        semantic_similarity=round(sem_sim, 3),
        matched_required_skills=matched_req,
        missing_required_skills=missing_req,
        matched_preferred_skills=matched_pref,
        missing_preferred_skills=missing_pref,
        experience_match=exp_desc,
        education_match=edu_desc,
        strengths=strengths,
        gaps=gaps,
        explanation=explanation,
        breakdown=breakdown,
        candidate=candidate,
    )
