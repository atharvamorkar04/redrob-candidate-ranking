import gzip
import json
import heapq
from src.scorer import score_candidate
from src.reasoning import generate_reasoning

class HeapElement:
    """
    Wrapper for heapq elements to implement custom tie-breaking.
    Under-performing candidates (lower score, or equal score with alphabetically larger ID)
    are treated as 'less than' so they bubble to the top of the min-heap for removal.
    """
    def __init__(self, score: float, candidate_id: str, candidate: dict, score_result: dict):
        self.score = score
        self.candidate_id = candidate_id
        self.candidate = candidate
        self.score_result = score_result

    def __lt__(self, other):
        if self.score != other.score:
            return self.score < other.score
        # For equal scores, larger candidate ID is worse (should be popped/replaced)
        return self.candidate_id > other.candidate_id

def run_ranking(jsonl_path: str, top_k: int = 100, return_metrics: bool = False):
    """
    Orchestrates the streaming, scoring, heap-filtering, and sorting of candidates.
    Runs entirely on CPU with O(top_k) memory.
    """
    from src.ingest import stream_candidates
    
    heap = []
    pool_size = 0
    honeypots_flagged = 0
    honeypot_list = []
    sample_scores = []
    
    for candidate in stream_candidates(jsonl_path):
        pool_size += 1
        score_result = score_candidate(candidate)
        final_score = round(score_result['final_score'], 4)
        
        # Track metrics in a single pass
        if score_result.get('honeypot_penalty', 0.0) > 0.0:
            honeypots_flagged += 1
            if len(honeypot_list) < 100:
                honeypot_list.append({
                    'candidate_id': candidate.get('candidate_id', 'N/A'),
                    'final_score': 0.0,
                    'current_title': candidate.get('profile', {}).get('current_title', 'N/A'),
                    'honeypot_penalty': 0.80
                })
        
        if pool_size <= 1000:
            sample_scores.append(final_score)
            
        element = HeapElement(final_score, candidate['candidate_id'], candidate, score_result)
        
        if len(heap) < top_k:
            heapq.heappush(heap, element)
        elif heap[0] < element:
            heapq.heapreplace(heap, element)
                
    # Sort descending by score, ascending by candidate_id to break ties
    top = sorted(heap, key=lambda x: (-x.score, x.candidate_id))
    
    results = []
    from src.reasoning import ensure_unique_reasonings
    for rank_idx, element in enumerate(top, start=1):
        reasoning = generate_reasoning(
            element.candidate, 
            element.score, 
            rank_idx, 
            element.score_result
        )
        results.append({
            'candidate_id': element.candidate_id,
            'rank': rank_idx,
            'score': round(element.score, 4),
            'reasoning': reasoning,
            'profile': element.candidate.get('profile', {}),
            'skills': element.candidate.get('skills', []),
            'signals': element.candidate.get('redrob_signals', {}),
            'education': element.candidate.get('education', []),
            'career_history': element.candidate.get('career_history', []),
            'score_breakdown': element.score_result,
            'honeypot_penalty': element.score_result.get('honeypot_penalty', 0.0)
        })
        
    results = ensure_unique_reasonings(results)
    
    if return_metrics:
        metrics = {
            'pool_size': pool_size,
            'est_honeypots': honeypots_flagged,
            'honeypot_list': honeypot_list,
            'sample_scores': sample_scores
        }
        return results, metrics
        
    return results
