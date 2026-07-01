import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.honeypot import detect_honeypot

def test_expert_zero_months_flagged():
    # Trigger H3 (expert + 0 months) and H5 (many advanced skills with low duration)
    candidate = {
        "profile": {"years_of_experience": 5.0},
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 0},
            {"name": "SQL", "proficiency": "advanced", "duration_months": 1},
            {"name": "Git", "proficiency": "advanced", "duration_months": 1},
            {"name": "AWS", "proficiency": "advanced", "duration_months": 1},
            {"name": "Docker", "proficiency": "advanced", "duration_months": 1}
        ],
        "career_history": [],
        "redrob_signals": {}
    }
    result = detect_honeypot(candidate)
    assert result['is_honeypot'] is True
    assert result['penalty'] == 0.80

def test_perfect_signals_flagged():
    # Trigger H4 (perfect signals) and H3 (expert + 0 months)
    candidate = {
        "profile": {"years_of_experience": 5.0},
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 0}
        ],
        "career_history": [],
        "redrob_signals": {
            "profile_completeness_score": 100,
            "recruiter_response_rate": 1.0,
            "offer_acceptance_rate": 1.0,
            "interview_completion_rate": 1.0
        }
    }
    result = detect_honeypot(candidate)
    assert result['is_honeypot'] is True
    assert result['penalty'] == 0.80

def test_normal_candidate_not_flagged():
    candidate = {
        "profile": {"years_of_experience": 5.0},
        "skills": [
            {"name": "Python", "proficiency": "advanced", "duration_months": 36}
        ],
        "career_history": [
            {"company": "Google", "duration_months": 36}
        ],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "recruiter_response_rate": 0.8,
            "offer_acceptance_rate": 0.8,
            "interview_completion_rate": 0.8
        }
    }
    result = detect_honeypot(candidate)
    assert result['is_honeypot'] is False
    assert result['penalty'] == 0.0

def test_active_before_signup_flagged():
    # Trigger H7 (last_active_date < signup_date) and H3 (expert + 0 months)
    candidate = {
        "profile": {"years_of_experience": 5.0},
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 0}
        ],
        "career_history": [],
        "redrob_signals": {
            "signup_date": "2026-05-02",
            "last_active_date": "2025-11-29"
        }
    }
    result = detect_honeypot(candidate)
    assert result['is_honeypot'] is True
    assert result['penalty'] == 0.80
