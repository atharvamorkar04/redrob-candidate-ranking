import pytest
import csv
import json
import tempfile
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ranker import run_ranking

def test_output_format_end_to_end():
    # Create 120 mock candidates
    candidates = []
    for i in range(1, 121):
        cid = f"CAND_{i:07d}"
        candidates.append({
            "candidate_id": cid,
            "profile": {
                "years_of_experience": 5.0 + (i % 5),
                "current_title": "AI Engineer" if i % 2 == 0 else "Backend Developer",
                "current_company": f"Product Company {i}",
                "location": "Pune",
                "country": "India"
            },
            "skills": [
                {"name": "Python", "proficiency": "advanced", "duration_months": 36},
                {"name": "retrieval", "proficiency": "advanced", "duration_months": 12},
                {"name": "pinecone", "proficiency": "advanced", "duration_months": 12},
                {"name": "ndcg", "proficiency": "advanced", "duration_months": 12}
            ],
            "education": [
                {"tier": "tier_1", "field_of_study": "Computer Science"}
            ],
            "career_history": [
                {"company": f"Product Company {i}", "title": "AI Engineer", "duration_months": 24, "description": "built retrieval search engine using python"}
            ],
            "redrob_signals": {
                "open_to_work_flag": True,
                "last_active_date": "2025-05-20",
                "notice_period_days": 15,
                "profile_completeness_score": 90,
                "recruiter_response_rate": 0.8,
                "offer_acceptance_rate": 0.8,
                "interview_completion_rate": 0.8,
                "verified_email": True,
                "verified_phone": True
            }
        })
        
    # Write to a temporary jsonl file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as temp:
        for c in candidates:
            temp.write(json.dumps(c) + "\n")
        temp_path = temp.name

    try:
        # Run ranking
        results = run_ranking(temp_path, top_k=100)
        
        # Test: exactly 100 rows
        assert len(results) == 100
        
        # Write to a temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as temp_csv:
            writer = csv.writer(temp_csv)
            writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
            for row in results:
                writer.writerow([row['candidate_id'], row['rank'], f"{row['score']:.4f}", row['reasoning']])
            csv_path = temp_csv.name
            
        try:
            # Read and verify the CSV file
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                assert header == ['candidate_id', 'rank', 'score', 'reasoning']
                
                rows = list(reader)
                
            # Test: exactly 100 rows
            assert len(rows) == 100
            
            seen_ids = set()
            seen_ranks = set()
            scores = []
            reasonings = []
            
            for row in rows:
                cid, rank_s, score_s, reasoning = row
                
                # Test: candidate_ids start with CAND_ and are unique
                assert cid.startswith("CAND_")
                assert cid not in seen_ids
                seen_ids.add(cid)
                
                # Test: ranks 1 to 100 unique
                rank = int(rank_s)
                assert 1 <= rank <= 100
                assert rank not in seen_ranks
                seen_ranks.add(rank)
                
                score = float(score_s)
                scores.append(score)
                
                # Test: reasoning not empty
                assert reasoning.strip() != ""
                assert len(reasoning) <= 200
                reasonings.append(reasoning)
                
            # Test: ranks 1 to 100 are present
            assert seen_ranks == set(range(1, 101))
            
            # Test: scores are non-increasing
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1]
                
            # Test: reasoning not all identical
            assert len(set(reasonings)) > 1
            
        finally:
            os.remove(csv_path)
    finally:
        os.remove(temp_path)
