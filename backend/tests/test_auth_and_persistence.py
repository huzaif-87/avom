"""Unit and integration tests for Recruiter Authentication, Persistence, and Ownership security."""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import pymongo


class TestRecruiterAuthAndPersistence(unittest.TestCase):
    """Test suite for Recruiter Authentication and Persistence."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and direct pymongo client for cleanup."""
        cls.client = TestClient(app)
        cls.sync_mongo = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        cls.sync_db = cls.sync_mongo["talentrank_ai"]

        # Clean prior test artifacts
        cls.sync_db.recruiters.delete_many({"email": {"$regex": "@test-talentrank.io"}})
        cls.sync_db.job_analyses.delete_many({"recruiter_id": {"$regex": "^rec_"}})
        cls.sync_db.candidates.delete_many({"recruiter_id": {"$regex": "^rec_"}})

    @classmethod
    def tearDownClass(cls):
        """Clean up test records."""
        cls.sync_db.recruiters.delete_many({"email": {"$regex": "@test-talentrank.io"}})
        cls.sync_db.job_analyses.delete_many({"recruiter_id": {"$regex": "^rec_"}})
        cls.sync_db.candidates.delete_many({"recruiter_id": {"$regex": "^rec_"}})
        cls.sync_mongo.close()

    def test_01_register_recruiter(self):
        """Test recruiter registration with validation and password hashing."""
        payload = {
            "full_name": "Sarah Connor",
            "email": "sarah@test-talentrank.io",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["recruiter"]["email"], "sarah@test-talentrank.io")
        self.assertEqual(data["recruiter"]["full_name"], "Sarah Connor")
        # Ensure password is never exposed
        self.assertNotIn("password", str(data))
        self.assertNotIn("hashed_password", str(data))

    def test_02_duplicate_email_rejection(self):
        """Test rejection of duplicate email registration."""
        payload = {
            "full_name": "Sarah Duplicate",
            "email": "sarah@test-talentrank.io",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 409)

    def test_03_login_success_and_wrong_password(self):
        """Test login verification with bcrypt."""
        # Wrong password
        res = self.client.post("/api/auth/login", json={"email": "sarah@test-talentrank.io", "password": "WrongPassword99!"})
        self.assertEqual(res.status_code, 401)

        # Correct password
        res = self.client.post("/api/auth/login", json={"email": "sarah@test-talentrank.io", "password": "Password123!"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)

    def test_04_profile_and_protected_route(self):
        """Test GET /api/auth/me with Bearer token."""
        # Without token
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

        # Login to get fresh token
        login_res = self.client.post("/api/auth/login", json={"email": "sarah@test-talentrank.io", "password": "Password123!"})
        token = login_res.json()["access_token"]

        res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], "sarah@test-talentrank.io")

    def test_05_save_and_retrieve_analysis(self):
        """Test persistent save, retrieve, and recruiter scoping."""
        # Register Recruiter A
        rec_a = self.client.post(
            "/api/auth/register",
            json={"full_name": "Recruiter A", "email": "recruiter_a@test-talentrank.io", "password": "Password123!", "confirm_password": "Password123!"},
        ).json()
        token_a = rec_a["access_token"]

        # Register Recruiter B
        rec_b = self.client.post(
            "/api/auth/register",
            json={"full_name": "Recruiter B", "email": "recruiter_b@test-talentrank.io", "password": "Password123!", "confirm_password": "Password123!"},
        ).json()
        token_b = rec_b["access_token"]

        # Recruiter A saves an analysis
        analysis_payload = {
            "job_title": "Lead Python Engineer",
            "jd_text": "We need a senior python engineer with 5+ years experience in FastAPI and React.",
            "jd_analysis": {
                "required_skills": ["Python", "FastAPI"],
                "preferred_skills": ["React"],
                "minimum_experience": 5.0,
                "summary": "Senior python role",
            },
            "candidates": [
                {
                    "candidate_id": "cand_test_001",
                    "name": "Alice Pythonista",
                    "email": "alice@example.com",
                    "skills": ["Python", "FastAPI", "Docker"],
                    "experience_years": 6.0,
                    "overall_match_score": 92,
                    "rank": 1,
                }
            ],
        }

        save_res = self.client.post("/api/analyses", json=analysis_payload, headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(save_res.status_code, 201)
        analysis_id = save_res.json()["id"]

        # Recruiter A can retrieve it
        get_res = self.client.get(f"/api/analyses/{analysis_id}", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["candidate_count"], 1)

        # Recruiter B CANNOT access Recruiter A's analysis (HTTP 403)
        b_res = self.client.get(f"/api/analyses/{analysis_id}", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(b_res.status_code, 403)

        # Update candidate status to 'shortlisted'
        status_res = self.client.patch(
            f"/api/analyses/{analysis_id}/candidates/cand_test_001/status",
            json={"status": "shortlisted"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["status"], "shortlisted")

        # Verify shortlist count updated
        updated_analysis = self.client.get(f"/api/analyses/{analysis_id}", headers={"Authorization": f"Bearer {token_a}"}).json()
        self.assertEqual(updated_analysis["shortlisted_count"], 1)

        # List analyses for Recruiter A
        list_res = self.client.get("/api/analyses", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # List analyses for Recruiter B (must be 0)
        list_b = self.client.get("/api/analyses", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(list_b.status_code, 200)
        self.assertEqual(len(list_b.json()), 0)


if __name__ == "__main__":
    unittest.main()
