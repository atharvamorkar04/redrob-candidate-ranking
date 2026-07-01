import pytest
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scorer import score_candidate

def test_marketing_manager_is_disqualified():
    candidate = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "years_of_experience": 5.0,
            "current_title": "Marketing Manager",
            "current_company": "Marketing Corp",
            "location": "Pune",
            "country": "India"
        },
        "skills": [
            {"name": "Python", "proficiency": "advanced", "duration_months": 36}
        ],
        "education": [
            {"tier": "tier_1", "field_of_study": "Computer Science"}
        ],
        "career_history": [
            {"company": "Marketing Corp", "title": "Marketing Manager", "duration_months": 24, "description": "Manage marketing campaigns"}
        ],
        "redrob_signals": {
            "open_to_work_flag": True,
            "last_active_date": "2025-06-01",
            "notice_period_days": 15,
            "profile_completeness_score": 90,
            "recruiter_response_rate": 0.9,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.9,
            "verified_email": True,
            "verified_phone": True
        }
    }
    result = score_candidate(candidate)
    # The title contains 'marketing' which is a low-fit/no-fit and adds a 0.50 disqualification penalty.
    assert result['final_score'] < 0.15

def test_ai_engineer_5yr_scores_high():
    candidate = {
        "candidate_id": "CAND_0000002",
        "profile": {
            "years_of_experience": 5.0,
            "current_title": "Senior AI Engineer",
            "current_company": "Tech Product Inc",
            "location": "Pune",
            "country": "India"
        },
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 60, "endorsements": 10},
            {"name": "sentence-transformers", "proficiency": "expert", "duration_months": 24, "endorsements": 10},
            {"name": "pinecone", "proficiency": "expert", "duration_months": 24, "endorsements": 10},
            {"name": "ndcg", "proficiency": "expert", "duration_months": 24, "endorsements": 10}
        ],
        "education": [
            {"tier": "tier_1", "field_of_study": "Computer Science"}
        ],
        "career_history": [
            {"company": "Tech Product Inc", "title": "Senior AI Engineer", "duration_months": 60, "description": "Developed embeddings-based search systems with Pinecone and evaluation metric NDCG using Python."}
        ],
        "redrob_signals": {
            "open_to_work_flag": True,
            "last_active_date": "2025-06-01",
            "notice_period_days": 15,
            "profile_completeness_score": 90,
            "recruiter_response_rate": 0.9,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.9,
            "verified_email": True,
            "verified_phone": True,
            "github_activity_score": 80,
            "saved_by_recruiters_30d": 5,
            "applications_submitted_30d": 2,
            "avg_response_time_hours": 2
        }
    }
    result = score_candidate(candidate)
    # This is an ideal fit, score should be >0.75
    assert result['final_score'] > 0.75

def test_services_only_career_penalized():
    # Career only at IT services firms (TCS, Wipro, etc.)
    candidate = {
        "candidate_id": "CAND_0000003",
        "profile": {
            "years_of_experience": 5.0,
            "current_title": "AI Engineer",
            "current_company": "TCS",
            "location": "Pune",
            "country": "India"
        },
        "skills": [
            {"name": "Python", "proficiency": "advanced", "duration_months": 36}
        ],
        "education": [
            {"tier": "tier_1", "field_of_study": "Computer Science"}
        ],
        "career_history": [
            {"company": "TCS", "title": "AI Engineer", "duration_months": 24, "description": "Worked on AI projects"},
            {"company": "Wipro", "title": "Developer", "duration_months": 36, "description": "Software development"}
        ],
        "redrob_signals": {
            "open_to_work_flag": True,
            "last_active_date": "2025-06-01",
            "notice_period_days": 15,
            "profile_completeness_score": 90,
            "recruiter_response_rate": 0.9,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.9,
            "verified_email": True,
            "verified_phone": True
        }
    }
    result = score_candidate(candidate)
    # The career_quality_score should be < 0.40 because all companies are in IT_SERVICES
    assert result['career_quality_score'] < 0.40

def test_high_yoe_in_range():
    # 7 YOE should get yoe_score = 1.0 (career_quality_score should reflect this)
    candidate = {
        "candidate_id": "CAND_0000004",
        "profile": {
            "years_of_experience": 7.0,
            "current_title": "AI Engineer",
            "current_company": "Tech Corp",
            "location": "Pune",
            "country": "India"
        },
        "skills": [],
        "education": [],
        "career_history": [],
        "redrob_signals": {}
    }
    result = score_candidate(candidate)
    # product_ratio=0, latest_role_ai=0. Max career_quality_score is 0.35 * yoe_score = 0.35
    assert abs(result['career_quality_score'] - 0.35) < 1e-5

def test_availability_multiplier_inactive():
    import datetime
    from src.scorer import REF_DATE
    inactive_date = (REF_DATE - datetime.timedelta(days=200)).isoformat()
    candidate = {
        "candidate_id": "CAND_0000005",
        "profile": {
            "years_of_experience": 5.0,
            "current_title": "AI Engineer",
            "current_company": "Tech Corp",
            "location": "Pune",
            "country": "India"
        },
        "skills": [],
        "education": [],
        "career_history": [],
        "redrob_signals": {
            "open_to_work_flag": False,
            "last_active_date": inactive_date,
            "recruiter_response_rate": 0.8,
            "interview_completion_rate": 0.8
        }
    }
    result = score_candidate(candidate)
    assert abs(result['availability_multiplier'] - 0.80) < 1e-5

def test_sentinel_minus1_does_not_corrupt_score():
    candidate = {
        "candidate_id": "CAND_0000006",
        "profile": {
            "years_of_experience": 5.0,
            "current_title": "AI Engineer",
            "current_company": "Tech Corp",
            "location": "Pune",
            "country": "India"
        },
        "skills": [],
        "education": [],
        "career_history": [],
        "redrob_signals": {
            "github_activity_score": -1,
            "offer_acceptance_rate": -1
        }
    }
    result = score_candidate(candidate)
    assert 0.0 < result['final_score'] < 1.0
    print(f'Sentinel test passed: {result["final_score"]}')
