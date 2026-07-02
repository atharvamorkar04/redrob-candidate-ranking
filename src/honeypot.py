import datetime

def honeypot_penalty(candidate: dict) -> float:
    """
    Returns a -0.80 penalty if candidate is flagged as a honeypot (2+ signals matched).
    """
    res = detect_honeypot(candidate)
    return res['penalty']

def detect_honeypot(candidate: dict) -> dict:
    """
    Evaluates the candidate against all 7 honeypot rules.
    Returns details on triggered signals, flag counts, and the penalty.
    """
    flags = 0
    triggered = []
    skills = candidate.get('skills', [])
    profile = candidate.get('profile', {})
    yoe = profile.get('years_of_experience', 0.0)
    rs = candidate.get('redrob_signals', {})
    
    # H1: Company age paradox (duration_months > 48 for fictitious companies)
    suspicious_companies = {
        'dunder mifflin', 'initech', 'initrode', 'pied piper', 'hooli', 
        'globodyne', 'prestige worldwide', 'vandelay', 'soylent corp', 
        'cyberdyne', 'umbrella corp', 'massive dynamic'
    }
    has_h1 = False
    for job in candidate.get('career_history', []):
        company = job.get('company', '').lower().strip()
        duration_months = job.get('duration_months', 0)
        if company in suspicious_companies and duration_months > 48:
            has_h1 = True
            triggered.append(f"H1: Implausibly long tenure ({duration_months}mo) at fictitious company '{job.get('company')}'")
            break
    if has_h1:
        flags += 1
        
    # H2: Skills impossibility (sum of duration_months > YoE * 14 * 12)
    total_skill_months = sum(s.get('duration_months', 0) for s in skills)
    if total_skill_months > yoe * 14 * 12:
        flags += 1
        triggered.append(f"H2: Improbable skill experience sum ({total_skill_months} months for {yoe} YOE)")
        
    # H3: Expert with 0 months duration
    if any(s.get('proficiency') == 'expert' and s.get('duration_months', 1) == 0 for s in skills):
        flags += 1
        triggered.append("H3: Expert proficiency skill(s) claimed with 0 months of use")
        
    # H4: Perfect engagement metrics
    if (rs.get('profile_completeness_score', 0) == 100 
            and rs.get('recruiter_response_rate', 0.0) == 1.0
            and rs.get('offer_acceptance_rate', 0.0) == 1.0
            and rs.get('interview_completion_rate', 0.0) == 1.0):
        flags += 1
        triggered.append("H4: Suspiciously perfect recruiter response, acceptance, and interview rates (all 100%)")
        
    # H5: Many advanced skills with tiny duration (< 3 months)
    low_dur_adv = [s for s in skills if s.get('proficiency') in ('advanced', 'expert')
                   and s.get('duration_months', 99) < 3]
    if len(low_dur_adv) > 3:
        flags += 1
        triggered.append(f"H5: {len(low_dur_adv)} advanced/expert skills with duration < 3 months")
        
    # H6: Expert skills with 0 endorsements (> 5 skills)
    no_endorse_expert = [s for s in skills if s.get('proficiency') == 'expert'
                         and s.get('endorsements', 0) == 0]
    if len(no_endorse_expert) > 5:
        flags += 1
        triggered.append(f"H6: {len(no_endorse_expert)} expert skills with zero endorsements")
        
    # H7: Active-before-signup inconsistency
    signup_date_str = rs.get('signup_date', '')
    active_date_str = rs.get('last_active_date', '')
    if signup_date_str and active_date_str:
        try:
            signup_date = datetime.date.fromisoformat(signup_date_str)
            active_date = datetime.date.fromisoformat(active_date_str)
            if active_date < signup_date:
                flags += 1
                triggered.append(f"H7: Last active date ({active_date_str}) is before signup date ({signup_date_str})")
        except:
            pass
            
    penalty = 0.80 if flags >= 2 else 0.0
    return {
        'penalty': penalty,
        'flags_count': flags,
        'triggered_signals': triggered,
        'is_honeypot': flags >= 2
    }
