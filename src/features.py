def extract_candidate_texts(candidate: dict) -> dict:
    """
    Extracts and prepares concatenated text fields for keyword search and semantic matching.
    """
    skills = candidate.get('skills', [])
    skill_text = ' '.join([
        s.get('name', '') for s in skills
        if s.get('proficiency', '') in ('advanced', 'expert')
    ])
    
    career = candidate.get('career_history', [])
    career_text = ' '.join([j.get('description', '') for j in career if j.get('description')])
    
    full_text = f"{skill_text} {career_text}"
    
    current_role_desc = ""
    if career:
        curr_job = next((j for j in career if j.get('is_current')), career[0])
        current_role_desc = f"{curr_job.get('title', '')} {curr_job.get('description', '')}"
        
    return {
        'skill_text': skill_text,
        'career_text': career_text,
        'full_text': full_text,
        'current_role_desc': current_role_desc
    }
