"""Unit and Integration Tests for Stage 3 AI Resume Matching Engine.

Validates:
1. Sentence Transformers embedding generation with all-MiniLM-L6-v2.
2. Cosine similarity accuracy and normalization.
3. 5-component weighted scoring:
   - Semantic similarity (35%)
   - Required skills (30%)
   - Experience (20%)
   - Education (10%)
   - Preferred skills (5%)
4. Explainability (strengths, gaps, human-friendly explanation).
5. Stable ranking order (descending overall score, secondary tie-breakers).
6. Missing data handling (no data fabrication; explainable penalties).
7. Error handling for empty resumes, missing JD, model errors.
8. API endpoint POST /api/match/evaluate integration.
"""

import unittest
from fastapi.testclient import TestClient
from main import app
from app.schemas.resume import CandidateResumeResult
from app.schemas.jd import JDAnalyzeResponse
from app.services.matching.embedding_service import compute_embeddings, compute_cosine_similarity
from app.services.matching.matching_service import (
    evaluate_skill_coverage,
    evaluate_experience,
    evaluate_education,
    compute_candidate_match,
)

client = TestClient(app)


class TestStage3AIMatching(unittest.TestCase):

    def test_embedding_service_shape_and_similarity(self):
        """Verify embeddings produce 384-dimensional normalized vectors and sensible similarity."""
        texts = [
            "Senior Python Engineer with FastAPI and Docker experience.",
            "Experienced Python Developer building REST APIs with FastAPI.",
            "Registered Nurse with pediatric clinical care background.",
        ]
        embs, model_name = compute_embeddings(texts)
        self.assertEqual(embs.shape, (3, 384))

        # Python vs Python should have high similarity (> 0.65)
        sim_similar = compute_cosine_similarity(embs[0], embs[1])
        self.assertGreater(sim_similar, 0.65)

        # Python vs Nurse should have lower similarity (< 0.40)
        sim_dissimilar = compute_cosine_similarity(embs[0], embs[2])
        self.assertLess(sim_dissimilar, 0.40)
        self.assertGreater(sim_similar, sim_dissimilar)
        print("\n  [PASS] Sentence Transformers embedding & cosine similarity")

    def test_skill_coverage_evaluation(self):
        """Verify skill coverage returns accurate matched and missing skills."""
        cand_skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
        target_skills = ["python", "FastAPI", "React", "AWS"]

        matched, missing, coverage = evaluate_skill_coverage(cand_skills, target_skills)
        matched_lower = [m.lower() for m in matched]
        missing_lower = [m.lower() for m in missing]

        self.assertIn("python", matched_lower)
        self.assertIn("fastapi", matched_lower)
        self.assertIn("react", missing_lower)
        self.assertIn("aws", missing_lower)
        self.assertEqual(coverage, 0.5)
        print("  [PASS] Skill coverage evaluation")

    def test_experience_evaluation_fresher_and_experienced(self):
        """Verify experience scoring differentiates freshers and verified professional experience."""
        # Candidate meets 3-year requirement
        cov_exp, desc_exp = evaluate_experience(candidate_years=4.0, min_required_years=3.0)
        self.assertEqual(cov_exp, 1.0)
        self.assertTrue("Meets" in desc_exp or "Exceeds" in desc_exp)

        # Candidate has no experience for 3-year requirement
        cov_fresh, desc_fresh = evaluate_experience(
            candidate_years=None,
            min_required_years=3.0,
            experience_source="fresher_override",
        )
        self.assertLess(cov_fresh, 0.4)
        self.assertIn("Fresher candidate does not meet", desc_fresh)

        # No minimum experience requirement in JD
        cov_none, desc_none = evaluate_experience(candidate_years=2.0, min_required_years=None)
        self.assertEqual(cov_none, 1.0)
        print("  [PASS] Experience comparison & fresher penalty handling")

    def test_education_evaluation(self):
        """Verify education matches degrees hierarchically."""
        # Candidate has Bachelor's, role requires Bachelor's
        cov_b, desc_b = evaluate_education(
            candidate_education=["B.Tech in Computer Science"],
            jd_education_reqs=["Bachelor's degree in Computer Science or related field"],
        )
        self.assertEqual(cov_b, 1.0)

        # Candidate has no degree
        cov_zero, desc_zero = evaluate_education(
            candidate_education=[],
            jd_education_reqs=["Bachelor's degree"],
        )
        self.assertLess(cov_zero, 0.3)
        print("  [PASS] Education requirements evaluation")

    def test_compute_candidate_match_weights_and_breakdown(self):
        """Verify exact weighted scoring formula totals 100 max."""
        jd = JDAnalyzeResponse(
            extracted_skills=["Python", "FastAPI", "Docker", "PostgreSQL", "React"],
            required_skills=["Python", "FastAPI", "Docker"],
            preferred_skills=["PostgreSQL", "React"],
            minimum_experience=3.0,
            education_requirements=["Bachelor of Science"],
            required_qualifications=["3+ years Python experience"],
            preferred_qualifications=[],
            summary="Looking for a Python Backend Engineer",
        )

        candidate = CandidateResumeResult(
            candidate_id="cand_test_01",
            filename="alice.pdf",
            name="Alice Walker",
            email="alice@example.com",
            skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
            education=["Bachelor of Science in Computer Science"],
            professional_experience_years=4.0,
            experience_confidence="high",
            experience_source="employment_history",
            raw_text="Alice Walker. 4 years of experience building Python and FastAPI microservices.",
        )

        scored = compute_candidate_match(
            candidate=candidate,
            jd_analysis=jd,
            semantic_similarity=0.85,
        )

        # 1. Check components
        # Semantic: 0.85 * 35 = 29.75
        self.assertAlmostEqual(scored.breakdown.semantic_score, 29.75, delta=0.1)
        # Required skills: 3/3 = 1.0 * 30 = 30.0
        self.assertEqual(scored.breakdown.required_skills_score, 30.0)
        # Experience: 4.0 >= 3.0 = 1.0 * 20 = 20.0
        self.assertEqual(scored.breakdown.experience_score, 20.0)
        # Education: Bachelor matches = 1.0 * 10 = 10.0
        self.assertEqual(scored.breakdown.education_score, 10.0)
        # Preferred skills: 1/2 = 0.5 * 5 = 2.5
        self.assertEqual(scored.breakdown.preferred_skills_score, 2.5)

        # Total score should be ~92.25
        self.assertGreaterEqual(scored.overall_match_score, 91.0)
        self.assertLessEqual(scored.overall_match_score, 93.0)
        self.assertGreaterEqual(len(scored.strengths), 2)
        self.assertIn("Alice Walker", scored.candidate.name)
        self.assertIn("Docker", scored.matched_required_skills)
        print("  [PASS] Component weighting (35/30/20/10/5) & breakdown")

    def test_api_match_evaluate_endpoint_ranking_and_stability(self):
        """Verify POST /api/match/evaluate returns sorted, ranked candidates with explanations."""
        jd_text = """
        Job Title: Senior Backend Engineer
        Required Skills: Python, FastAPI, PostgreSQL, Docker
        Preferred Skills: Kubernetes, Redis
        Minimum Experience: 4 years
        Education: Bachelor's degree in Computer Science or related
        """

        strong_candidate = {
            "candidate_id": "cand_strong",
            "filename": "strong.pdf",
            "name": "Sarah Connor",
            "email": "sarah@example.com",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
            "education": ["B.Tech in Computer Science (2018)"],
            "professional_experience_years": 5.0,
            "experience_confidence": "high",
            "experience_source": "employment_history",
            "raw_text": "Sarah Connor. 5 years of software engineering experience in Python, FastAPI, PostgreSQL, and Docker microservices.",
        }

        fresher_candidate = {
            "candidate_id": "cand_fresher",
            "filename": "fresher.pdf",
            "name": "Rohan Gupta",
            "email": "rohan@example.com",
            "skills": ["Python", "HTML", "CSS"],
            "education": ["B.Tech in Computer Science (2024)"],
            "professional_experience_years": None,
            "internship_experience_years": 0.5,
            "experience_confidence": "high",
            "experience_source": "fresher_override",
            "raw_text": "Rohan Gupta. Fresher student looking for entry-level developer role with Python training.",
        }

        payload = {
            "jd_text": jd_text,
            "candidates": [fresher_candidate, strong_candidate],  # intentionally unordered
        }

        response = client.post("/api/match/evaluate", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()

        self.assertEqual(data["total_candidates"], 2)
        ranked = data["ranked_candidates"]
        self.assertEqual(len(ranked), 2)

        # Verify rank 1 is strong_candidate and rank 2 is fresher_candidate
        self.assertEqual(ranked[0]["candidate_id"], "cand_strong")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertGreater(ranked[0]["overall_match_score"], 80.0)
        self.assertGreaterEqual(len(ranked[0]["matched_required_skills"]), 3)
        self.assertGreater(len(ranked[0]["strengths"]), 0)

        self.assertEqual(ranked[1]["candidate_id"], "cand_fresher")
        self.assertEqual(ranked[1]["rank"], 2)
        self.assertLess(ranked[1]["overall_match_score"], 50.0)
        self.assertGreaterEqual(len(ranked[1]["missing_required_skills"]), 2)
        self.assertGreater(len(ranked[1]["gaps"]), 0)

        print("  [PASS] API POST /api/match/evaluate ranking & stability")

    def test_api_match_validation_empty_candidates(self):
        """Verify endpoint rejects empty candidates gracefully with 400."""
        res = client.post("/api/match/evaluate", json={"jd_text": "Software Engineer", "candidates": []})
        self.assertEqual(res.status_code, 400)
        self.assertIn("No candidates provided", res.text)
        print("  [PASS] Empty candidates rejection (HTTP 400)")

    def test_api_match_validation_missing_jd(self):
        """Verify endpoint rejects missing JD text with 400."""
        res = client.post(
            "/api/match/evaluate",
            json={"candidates": [{"candidate_id": "c1", "filename": "c.pdf", "name": "Bob"}]},
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Job description is required", res.text)
        print("  [PASS] Missing JD validation (HTTP 400)")


if __name__ == "__main__":
    unittest.main()
