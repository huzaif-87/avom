"""Comprehensive test suite for Task 1: Experience Extraction Accuracy.

Verifies:
1. Fresher with four-year college duration is NOT detected as having 4 years experience.
2. Fresher with multiple academic projects is not given project durations as experience.
3. Candidate with 2-year explicit professional experience gets 2.0 years.
4. Candidate with internships only has internship_experience_years set, professional_experience_years as null.
5. Candidate with overlapping employment dates avoids double-counting.
6. Candidate with graduation year but no work experience has null experience.
7. Resume explicitly stating no professional experience returns null / 0.0 with fresher_override.
8. Resume with unknown experience returns null and low/none confidence.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.extractors.candidate_extractor import extract_candidate_profile, extract_accurate_experience


def test_fresher_with_four_year_college():
    """TEST 1: Fresher with four-year college duration (2018 - 2022)."""
    resume_text = """
    Rohan Sharma
    rohan.sharma@example.com | +91 98765 43210
    
    PROFILE
    Computer Science Fresher seeking entry-level software development roles. Passionate about algorithms and web development.
    
    EDUCATION
    Bachelor of Technology in Computer Science and Engineering
    Indian Institute of Technology (2018 - 2022)
    GPA: 8.9 / 10
    
    SKILLS
    Python, C++, Data Structures, Algorithms, Git
    """
    res = extract_candidate_profile(resume_text, filename="rohan_fresher.pdf")
    print("\n[TEST 1 - Fresher 4-year College]")
    print(f"  Name: {res.name}")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Experience Source: {res.experience_source}")
    print(f"  Warnings: {res.experience_warnings}")

    # Must NOT be 4 years!
    assert res.professional_experience_years is None or res.professional_experience_years == 0.0, (
        f"CRITICAL ERROR: Fresher was assigned {res.professional_experience_years} years!"
    )
    assert res.experience_source in ("fresher_override", "none")
    print("  PASS: College duration was NOT counted as professional experience.")


def test_fresher_with_academic_projects():
    """TEST 2: Fresher with multiple academic projects with year ranges."""
    resume_text = """
    Priya Patel
    priya.patel@example.com | +1 555 123 4567
    
    OBJECTIVE
    Recent graduate looking for entry-level front-end developer opportunities.
    
    EDUCATION
    B.Tech Computer Science, State University (2019 - 2023)
    
    ACADEMIC PROJECTS
    Autonomous Drone Navigation (2022 - 2023)
    - Built computer vision pipeline using Python and OpenCV.
    
    Hospital Management System (2021 - 2022)
    - Developed full stack web portal using React and Node.js.
    
    SKILLS
    React, JavaScript, Python, OpenCV
    """
    res = extract_candidate_profile(resume_text, filename="priya_projects.pdf")
    print("\n[TEST 2 - Fresher with Academic Projects]")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Experience Source: {res.experience_source}")

    assert res.professional_experience_years is None or res.professional_experience_years == 0.0, (
        f"ERROR: Project years counted as experience: {res.professional_experience_years}"
    )
    print("  PASS: Project dates were NOT counted as professional experience.")


def test_explicit_professional_experience():
    """TEST 3: Candidate with 2-year explicit professional experience."""
    resume_text = """
    Alex Johnson
    alex.j@example.com | +1 555 222 3333
    
    SUMMARY
    Full Stack Developer with 2 years of professional experience building scalable cloud applications.
    
    WORK EXPERIENCE
    Software Engineer - Apex Labs (2022 - 2024)
    - Developed backend microservices using FastAPI and PostgreSQL.
    
    EDUCATION
    B.S. in Computer Science (2018 - 2022)
    
    SKILLS
    Python, FastAPI, PostgreSQL, Docker
    """
    res = extract_candidate_profile(resume_text, filename="alex_explicit.pdf")
    print("\n[TEST 3 - Explicit 2-year Professional Experience]")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Experience Source: {res.experience_source}")
    print(f"  Confidence: {res.experience_confidence}")

    assert res.professional_experience_years == 2.0, (
        f"Expected 2.0, got {res.professional_experience_years}"
    )
    assert res.experience_confidence == "high"
    print("  PASS: Verified explicit professional experience correctly recognized as 2.0 years.")


def test_candidate_with_internships_only():
    """TEST 4: Candidate with internships only."""
    resume_text = """
    Kavita Reddy
    kavita.r@example.com | +91 99887 76655
    
    EDUCATION
    B.Tech in Information Technology (2020 - 2024)
    
    INTERNSHIP EXPERIENCE
    Software Engineering Intern - CloudWorks (May 2023 - Nov 2023)
    - Assisted in building CI/CD deployment pipelines using Docker.
    
    SKILLS
    Docker, Python, Git
    """
    res = extract_candidate_profile(resume_text, filename="kavita_intern.pdf")
    print("\n[TEST 4 - Internships Only]")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Internship Experience: {res.internship_experience_years}")
    print(f"  Experience Source: {res.experience_source}")

    assert res.professional_experience_years is None or res.professional_experience_years == 0.0
    assert res.internship_experience_years is not None and res.internship_experience_years > 0.0
    assert res.experience_source == "internship_only"
    print(f"  PASS: Internships tracked separately ({res.internship_experience_years} yrs) without conflating with full-time.")


def test_overlapping_employment_dates():
    """TEST 5: Candidate with overlapping employment dates (no double counting)."""
    resume_text = """
    Marcus Vance
    marcus@example.com | +1 555 444 8888
    
    WORK EXPERIENCE
    Senior Developer - Alpha Corp (2020 - 2023)
    Part-time Technical Consultant - Beta Inc (2021 - 2023)
    
    EDUCATION
    B.Sc Computer Science (2016 - 2020)
    
    SKILLS
    Java, Spring Boot, MySQL
    """
    res = extract_candidate_profile(resume_text, filename="marcus_overlap.pdf")
    print("\n[TEST 5 - Overlapping Employment Dates]")
    print(f"  Professional Experience: {res.professional_experience_years}")

    # 2020 to 2023 is 3 years total. If double counted, it would be (2023-2020) + (2023-2021) = 3 + 2 = 5 years!
    assert res.professional_experience_years == 3.0, (
        f"Overlapping periods double-counted! Expected 3.0, got {res.professional_experience_years}"
    )
    print("  PASS: Overlapping employment dates merged correctly to 3.0 years.")


def test_graduation_year_no_work_experience():
    """TEST 6: Candidate with graduation year but no work experience."""
    resume_text = """
    Sarah Lin
    sarah.lin@example.com | +1 555 777 9999
    
    EDUCATION
    Graduated in 2021 with Bachelor of Science in Information Systems.
    
    SKILLS
    SQL, Tableau, Excel, Python
    """
    res = extract_candidate_profile(resume_text, filename="sarah_grad.pdf")
    print("\n[TEST 6 - Graduation Year Only]")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Experience Source: {res.experience_source}")

    assert res.professional_experience_years is None
    print("  PASS: Graduation year alone was NOT interpreted as professional experience.")


def test_explicitly_no_professional_experience():
    """TEST 7: Resume explicitly stating no professional experience."""
    resume_text = """
    David Kim
    david.kim@example.com | +1 555 888 1111
    
    SUMMARY
    Energetic college student with no professional experience. Seeking first junior web developer position.
    
    EDUCATION
    Associate Degree in Computer Programming (2022 - 2024)
    
    SKILLS
    HTML, CSS, JavaScript
    """
    res = extract_candidate_profile(resume_text, filename="david_no_exp.pdf")
    print("\n[TEST 7 - Explicit No Experience]")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Experience Source: {res.experience_source}")

    assert res.professional_experience_years is None or res.professional_experience_years == 0.0
    assert res.experience_source == "fresher_override"
    print("  PASS: Stated no experience honored with fresher_override.")


def test_unknown_experience():
    """TEST 8: Resume with completely unknown experience."""
    resume_text = """
    Taylor Brooks
    taylor.brooks@example.com | +1 555 333 4444
    
    SKILLS
    Python, Git, Linux
    """
    res = extract_candidate_profile(resume_text, filename="taylor_unknown.pdf")
    print("\n[TEST 8 - Unknown Experience]")
    print(f"  Professional Experience: {res.professional_experience_years}")
    print(f"  Confidence: {res.experience_confidence}")
    print(f"  Source: {res.experience_source}")

    assert res.professional_experience_years is None
    assert res.experience_confidence == "none"
    assert res.experience_source == "none"
    print("  PASS: Unknown experience returns null with confidence 'none'.")


if __name__ == "__main__":
    test_fresher_with_four_year_college()
    test_fresher_with_academic_projects()
    test_explicit_professional_experience()
    test_candidate_with_internships_only()
    test_overlapping_employment_dates()
    test_graduation_year_no_work_experience()
    test_explicitly_no_professional_experience()
    test_unknown_experience()
    print("\n" + "=" * 70)
    print("ALL 8 EXPERIENCE ACCURACY TEST CASES PASSED SUCCESSFULLY!")
    print("=" * 70)
