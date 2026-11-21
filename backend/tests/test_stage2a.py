"""Automated verification suite for Stage 2A: Resume Parsing and JD Analysis."""

import io
import os
import sys
import fitz  # PyMuPDF
import docx

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def create_synthetic_pdf(
    name: str = "Alice Walker",
    email: str = "alice.walker@example.com",
    phone: str = "+1-555-0199",
    skills: str = "Python, FastAPI, Docker, PostgreSQL, React",
    experience: str = "5 years of experience in backend software development",
    education: str = "B.Tech in Computer Science from National Institute of Technology",
    include_dates: bool = True,
) -> bytes:
    """Generate a synthetic valid PDF in memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()

    lines = [
        name,
        f"{email} | {phone}",
        "",
        "SUMMARY",
        f"Software engineer with {experience}." if experience else "Software engineer.",
        "",
        "TECHNICAL SKILLS",
        skills,
        "",
        "EDUCATION",
        education,
        "",
        "WORK EXPERIENCE",
        "Senior Software Engineer - Tech Solutions (2019 - Present)" if include_dates else "Junior Developer - Project Trainee",
        "- Developed REST APIs with Python and FastAPI",
        "- Deployed microservices using Docker and PostgreSQL",
    ]

    text = "\n".join(lines)
    page.insert_text((50, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_synthetic_docx(
    name: str = "Bob Smith",
    email: str = "bob.smith@example.com",
    phone: str = "+44 20 7946 0991",
    skills: str = "Java, Spring Boot, AWS, Kubernetes, MySQL",
    experience: str = "3 years of experience as Java Developer",
    education: str = "Master of Science in Information Technology (2021)",
) -> bytes:
    """Generate a synthetic valid DOCX in memory using python-docx."""
    doc = docx.Document()
    doc.add_heading(name, level=1)
    doc.add_paragraph(f"Email: {email} | Phone: {phone}")

    doc.add_heading("Profile", level=2)
    doc.add_paragraph(f"Results-driven developer with {experience}.")

    doc.add_heading("Skills", level=2)
    # Add skills in paragraph
    doc.add_paragraph(skills)

    # Add education
    doc.add_heading("Education", level=2)
    doc.add_paragraph(education)

    # Add a table to test table extraction
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Category"
    table.cell(0, 1).text = "Technologies"
    table.cell(1, 0).text = "Cloud & DevOps"
    table.cell(1, 1).text = "AWS, Kubernetes, Docker, CI/CD"

    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


def run_all_tests():
    print("=" * 70)
    print("RUNNING TALENTRANK AI - STAGE 2A BACKEND TEST SUITE")
    print("=" * 70)

    # ---------------------------------------------------------
    # TEST 1: PDF Text Extraction
    # ---------------------------------------------------------
    print("\n[TEST 1] PDF Text Extraction")
    pdf_data = create_synthetic_pdf(
        name="Elena Rostova",
        email="elena.rostova@example.com",
        phone="+1-555-9876",
        skills="Python, Django, Scikit-Learn, PyTorch",
        experience="4 years of experience in machine learning",
        education="Bachelor of Science in Mathematics (2020)",
    )
    res = client.post(
        "/api/resumes/parse",
        files=[("files", ("elena_resume.pdf", pdf_data, "application/pdf"))],
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["total_files"] == 1
    assert data["successful"] == 1
    result = data["results"][0]
    assert result["name"] == "Elena Rostova"
    assert result["email"] == "elena.rostova@example.com"
    assert result["phone"] == "+1-555-9876"
    assert "Python" in result["skills"]
    assert "PyTorch" in result["skills"]
    assert result["experience_years"] == 4.0
    assert len(result["education"]) >= 1
    assert result["status"] == "success"
    print("  PASS: Extracted name, email, phone, skills, experience, education from PDF.")

    # ---------------------------------------------------------
    # TEST 2: DOCX Extraction
    # ---------------------------------------------------------
    print("\n[TEST 2] DOCX Extraction (Paragraphs & Tables)")
    docx_data = create_synthetic_docx(
        name="Marcus Vance",
        email="marcus.vance@example.com",
        phone="+1-555-4321",
        skills="Java, Spring Boot, MySQL",
        experience="6 years of experience",
        education="Bachelor of Engineering in Computer Science (2018)",
    )
    res = client.post(
        "/api/resumes/parse",
        files=[("files", ("marcus_resume.docx", docx_data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["successful"] == 1
    result = data["results"][0]
    assert result["name"] == "Marcus Vance"
    assert result["email"] == "marcus.vance@example.com"
    assert "Java" in result["skills"]
    # Table contained AWS, Kubernetes, Docker
    assert "AWS" in result["skills"] or "Kubernetes" in result["skills"]
    assert result["experience_years"] == 6.0
    assert result["status"] == "success"
    print("  PASS: Extracted paragraphs and tables from DOCX.")

    # ---------------------------------------------------------
    # TEST 3: Resume with Missing Email
    # ---------------------------------------------------------
    print("\n[TEST 3] Resume with Missing Email")
    no_email_pdf = create_synthetic_pdf(
        name="Chloe Zhao",
        email="",  # intentionally empty
        phone="+1-555-7788",
        skills="Go, Docker, Kubernetes",
        experience="3 years of experience as Go engineer",
        education="B.Tech Computer Science (2021)",
    )
    res = client.post(
        "/api/resumes/parse",
        files=[("files", ("chloe_resume.pdf", no_email_pdf, "application/pdf"))],
    )
    assert res.status_code == 200
    result = res.json()["results"][0]
    assert result["email"] is None
    assert any("No candidate email address found" in w for w in result["warnings"])
    print("  PASS: Safely handled missing email with warning.")

    # ---------------------------------------------------------
    # TEST 4: Resume with Missing Experience
    # ---------------------------------------------------------
    print("\n[TEST 4] Resume with Missing Experience")
    no_exp_pdf = create_synthetic_pdf(
        name="Daniel Craig",
        email="daniel.craig@example.com",
        phone="+1-555-0007",
        skills="HTML, CSS, JavaScript",
        experience="",  # no explicit years
        education="B.Sc in Web Design",
        include_dates=False,
    )
    res = client.post(
        "/api/resumes/parse",
        files=[("files", ("daniel_resume.pdf", no_exp_pdf, "application/pdf"))],
    )
    assert res.status_code == 200
    result = res.json()["results"][0]
    # Experience should be None or not determined
    assert result["experience_years"] is None or result["experience_years"] == 0
    assert any("experience" in w.lower() for w in result["warnings"])
    print("  PASS: Safely returned null/explanation when experience could not be reliably determined.")

    # ---------------------------------------------------------
    # TEST 5: Batch Upload with 10 Files
    # ---------------------------------------------------------
    print("\n[TEST 5] Batch Upload with 10 Files")
    batch_files = []
    for i in range(10):
        if i % 2 == 0:
            content = create_synthetic_pdf(
                name=f"Applicant {i+1}",
                email=f"applicant{i+1}@example.com",
                skills="Python, SQL, Git",
                experience=f"{i+1} years of experience",
            )
            batch_files.append(("files", (f"applicant_{i+1}.pdf", content, "application/pdf")))
        else:
            content = create_synthetic_docx(
                name=f"Applicant {i+1}",
                email=f"applicant{i+1}@example.com",
                skills="React, TypeScript, Tailwind CSS",
                experience=f"{i+1} years of experience",
            )
            batch_files.append(("files", (f"applicant_{i+1}.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))

    res = client.post("/api/resumes/parse", files=batch_files)
    assert res.status_code == 200
    data = res.json()
    assert data["total_files"] == 10
    assert data["successful"] == 10
    assert data["failed"] == 0
    assert len(data["results"]) == 10
    print("  PASS: Successfully parsed batch of 10 mixed PDF/DOCX resumes in single request.")

    # ---------------------------------------------------------
    # TEST 6: Unsupported File Type
    # ---------------------------------------------------------
    print("\n[TEST 6] Unsupported File Type")
    txt_content = b"Candidate Name: Invalid User\nEmail: test@test.com"
    res = client.post(
        "/api/resumes/parse",
        files=[("files", ("resume.txt", txt_content, "text/plain"))],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_files"] == 1
    assert data["failed"] == 1
    result = data["results"][0]
    assert result["status"] == "error"
    assert any("Unsupported file format" in w for w in result["warnings"])
    print("  PASS: Gracefully flagged unsupported file type without failing request.")

    # ---------------------------------------------------------
    # TEST 7: Corrupted File
    # ---------------------------------------------------------
    print("\n[TEST 7] Corrupted File Handling")
    corrupt_pdf = b"%PDF-1.4\nthis is completely corrupted binary garbage that will fail parsing"
    res = client.post(
        "/api/resumes/parse",
        files=[("files", ("corrupted.pdf", corrupt_pdf, "application/pdf"))],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["failed"] == 1
    result = data["results"][0]
    assert result["status"] == "error"
    assert any("corrupted" in w.lower() or "unable" in w.lower() for w in result["warnings"])
    print("  PASS: Safely caught corrupted file without crashing.")

    # ---------------------------------------------------------
    # TEST 8: JD Analysis with Common Skills
    # ---------------------------------------------------------
    print("\n[TEST 8] Job Description Analysis with Common Skills")
    sample_jd = """
    Role: Senior Full Stack Python Developer
    Location: Remote
    
    Requirements:
    - 3+ years of experience with Python and FastAPI
    - Strong experience in PostgreSQL and Redis
    - Bachelor's degree in Computer Science or related technical discipline
    
    Preferred Qualifications:
    - Experience deploying containers with Docker and Kubernetes
    - Hands-on knowledge of AWS and CI/CD pipelines
    """
    res = client.post("/api/jd/analyze", json={"text": sample_jd})
    assert res.status_code == 200
    jd_res = res.json()
    assert "Python" in jd_res["extracted_skills"]
    assert "FastAPI" in jd_res["extracted_skills"]
    assert "PostgreSQL" in jd_res["extracted_skills"]
    assert "Redis" in jd_res["extracted_skills"]
    assert "Python" in jd_res["required_skills"]
    assert "Docker" in jd_res["preferred_skills"] or "AWS" in jd_res["preferred_skills"]
    assert jd_res["minimum_experience"] == 3.0
    assert len(jd_res["education_requirements"]) >= 1
    assert len(jd_res["required_qualifications"]) >= 1
    assert len(jd_res["preferred_qualifications"]) >= 1
    print("  PASS: Correctly extracted skills, required/preferred split, experience, and education from JD.")

    # ---------------------------------------------------------
    # TEST 9: Empty JD
    # ---------------------------------------------------------
    print("\n[TEST 9] Empty JD Validation")
    res_empty = client.post("/api/jd/analyze", json={"text": ""})
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["error"]["message"].lower()

    res_whitespace = client.post("/api/jd/analyze", json={"text": "     \n  \t  "})
    assert res_whitespace.status_code == 400
    print("  PASS: Cleanly rejected empty and whitespace-only JD with HTTP 400.")

    # ---------------------------------------------------------
    # TEST 10: Health Endpoint Remains Working
    # ---------------------------------------------------------
    print("\n[TEST 10] Health Check Endpoint Verification")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert health_data["service"] == "TalentRank AI"
    assert "version" in health_data
    assert "timestamp" in health_data
    print("  PASS: GET /api/health returned 200 OK and valid health payload.")

    print("\n" + "=" * 70)
    print("ALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
