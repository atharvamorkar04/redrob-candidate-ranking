import datetime
from src.features import extract_candidate_texts
from src.honeypot import detect_honeypot

REF_DATE = datetime.date.today()

def safe_signal(value, sentinel=-1):
    return None if value == sentinel else value

IT_SERVICES = {
    'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini',
    'ibm', 'hcl', 'tech mahindra', 'mindtree', 'mphasis', 'hexaware',
    'ltimindtree', 'coforge', 'persistent', 'niit'
}

def is_services_firm(company_name: str) -> bool:
    return company_name.lower().strip() in IT_SERVICES

def score_candidate(candidate: dict) -> dict:
    """
    Computes all component scores, disqualification penalty, availability multiplier,
    and final score for a candidate.
    Returns:
        A dictionary containing the final_score and all sub-component metrics for analytics.
    """
    # Extract texts
    texts = extract_candidate_texts(candidate)
    full_text_lower = texts['full_text'].lower()
    current_role_desc_lower = texts['current_role_desc'].lower()
    
    # ─── COMPONENT A: skill_match_score (0.0–1.0) ───────────────────────────
    MUST_A = [
        # Explicit
        'embedding','embeddings','sentence-transformer','sentence_transformer',
        'vector embed','dense retrieval','semantic search','semantic similarity',
        'bi-encoder','cross-encoder','vector search','neural retrieval',
        'faiss','bge','e5','openai embed','text-embedding',
        # Implicit — same concept different words
        'recommendation system','recommender system','similar item',
        'nearest neighbor','knn','ann search','approximate nearest',
        'two-tower','candidate retrieval','recall layer','item2vec',
        'content-based filtering','collaborative filtering',
        'relevance ranking','search relevance','query understanding',
        'information retrieval','document retrieval','passage retrieval',
    ]

    MUST_B = [
        # Explicit
        'pinecone','weaviate','qdrant','milvus','opensearch',
        'elasticsearch','faiss','vector database','vector db',
        'vector store','hybrid search','ann index',
        # Implicit
        'solr','vespa','typesense','pgvector','redis search',
        'mongodb atlas search','azure cognitive search','algolia',
        'inverted index','bm25','tf-idf','sparse retrieval',
        'dense-sparse hybrid','reranking','re-ranking',
    ]

    MUST_C = ['python','pytorch','tensorflow','scikit-learn','numpy','pandas']

    MUST_D = [
        'ndcg','mrr','map@','mean average precision','ranking eval',
        'learning to rank','ltr','offline evaluation','precision@','recall@',
        'information retrieval','recsys evaluation',
        'click-through rate','ctr optimization','position bias',
        'online evaluation','uplift model','causal ranking',
    ]

    NICE = [
        'lora','qlora','peft','fine-tun','finetun','xgboost','lightgbm',
        'learning-to-rank','hr-tech','recruiting tech','distributed inference',
        'open-source contrib','rag','retrieval augmented','llm fine',
        'reranker','colbert','splade','matryoshka','distillation',
        'onnx','tensorrt','triton serve','knowledge distill',
    ]

    def group_hit(terms, text_lower):
        return any(t in text_lower for t in terms)
        
    must_hits = sum([
        group_hit(MUST_A, full_text_lower),
        group_hit(MUST_B, full_text_lower),
        group_hit(MUST_C, full_text_lower),
        group_hit(MUST_D, full_text_lower)
    ])
    nice_hits = sum(1 for t in NICE if t in full_text_lower)
    skill_match_score = (must_hits * 0.20 + min(nice_hits, 5) * 0.04)
    skill_match_score = min(skill_match_score, 1.0)

    # ─── COMPONENT B: career_quality_score (0.0–1.0) ────────────────────────
    career = candidate.get('career_history', [])
    total_roles = len(career)
    non_services_roles = sum(1 for j in career if not is_services_firm(j.get('company', '')))
    product_ratio = non_services_roles / max(total_roles, 1)

    yoe = candidate.get('profile', {}).get('years_of_experience', 0.0)
    if 5 <= yoe <= 9:   yoe_score = 1.0
    elif 4 <= yoe < 5:  yoe_score = 0.85
    elif 3 <= yoe < 4:  yoe_score = 0.65
    elif 9 < yoe <= 12: yoe_score = 0.80
    elif yoe > 12:      yoe_score = 0.55
    else:               yoe_score = 0.25

    latest_role_ai = 0.15 if any(kw in current_role_desc_lower for kw in
        ['ml','ai','nlp','search','retrieval','ranking','recommendation']) else 0.0
        
    career_quality_score = 0.50 * product_ratio + 0.35 * yoe_score + 0.15 * latest_role_ai
    career_quality_score = min(career_quality_score, 1.0)

    # ─── COMPONENT C: role_fit_score (0.0–1.0) ──────────────────────────────
    HIGH_FIT_TITLES = ['ml engineer','ai engineer','data scientist',
                       'machine learning','applied scientist','nlp engineer',
                       'search engineer','backend engineer','software engineer',
                       'platform engineer','research engineer','data engineer']
    MED_FIT_TITLES  = ['senior engineer','full stack','backend developer']
    LOW_FIT_TITLES  = ['manager','director','vp ','head of','architect']
    NO_FIT_TITLES   = ['marketing','sales','finance','hr','recruiter',
                       'content','designer','operations','accountant']
                       
    current_title = candidate.get('profile', {}).get('current_title', '').lower()
    
    if any(t in current_title for t in NO_FIT_TITLES):
        title_score = 0.0
    elif any(t in current_title for t in HIGH_FIT_TITLES):
        title_score = 1.0
    elif any(t in current_title for t in MED_FIT_TITLES):
        title_score = 0.70
    elif any(t in current_title for t in LOW_FIT_TITLES):
        title_score = 0.30
    else:
        title_score = 0.15

    IDEAL_CITIES = ['pune','noida','delhi','gurgaon','gurugram','hyderabad',
                    'mumbai','bangalore','bengaluru','chennai']
    location = candidate.get('profile', {}).get('location', '').lower()
    willing_relocate = candidate.get('redrob_signals', {}).get('willing_to_relocate', False)
    country = candidate.get('profile', {}).get('country', '').lower()
    
    if any(c in location for c in IDEAL_CITIES): 
        loc_score = 1.0
    elif willing_relocate:   
        loc_score = 0.75
    elif country in ('india', 'in'):  
        loc_score = 0.55
    else: 
        loc_score = 0.25

    nd = candidate.get('redrob_signals', {}).get('notice_period_days', 90)
    notice_score = 1.0 if nd<=15 else 0.85 if nd<=30 else 0.65 if nd<=60 else 0.40

    wm = candidate.get('redrob_signals', {}).get('preferred_work_mode', '').lower()
    work_mode_score = 1.0 if wm in ('hybrid','flexible','onsite') else 0.60

    role_fit_score = 0.35*title_score + 0.30*loc_score + 0.20*notice_score + 0.15*work_mode_score
    role_fit_score = min(role_fit_score, 1.0)

    # ─── COMPONENT D: engagement_signal_score (0.0–1.0) ─────────────────────
    s = candidate.get('redrob_signals', {})
    sig = 0.0
    if s.get('open_to_work_flag', False):
        sig += 0.20
        
    active_date_str = s.get('last_active_date', '')
    if not active_date_str:
        active_date_str = REF_DATE.isoformat()
    try:
        active_date = datetime.date.fromisoformat(active_date_str)
    except Exception:
        try:
            parts = active_date_str.split('-')
            active_date = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            active_date = REF_DATE
            
    days_since = (REF_DATE - active_date).days
    if days_since <= 14:  sig += 0.18
    elif days_since <= 30: sig += 0.14
    elif days_since <= 90: sig += 0.08
    else:                  sig += 0.02
    
    comp_score = s.get('profile_completeness_score', 0)
    if comp_score >= 85: sig += 0.12
    elif comp_score >= 65: sig += 0.07
    
    resp_rate = s.get('recruiter_response_rate', 0.0)
    if resp_rate >= 0.70: sig += 0.12
    elif resp_rate >= 0.40: sig += 0.06
    
    int_rate = s.get('interview_completion_rate', 0.0)
    if int_rate >= 0.80: sig += 0.10
    elif int_rate >= 0.50: sig += 0.05
    
    if s.get('verified_email', False) and s.get('verified_phone', False):
        sig += 0.06
        
    gh = safe_signal(s.get('github_activity_score', -1))
    if gh is not None:
        if gh >= 60:   sig += 0.08
        elif gh >= 30: sig += 0.04
        
    oar = safe_signal(s.get('offer_acceptance_rate', -1))
    if oar is not None:
        if oar >= 0.80:  sig += 0.05
        elif oar < 0.20: sig -= 0.03
    
    if s.get('saved_by_recruiters_30d', 0) >= 3: sig += 0.06
    if s.get('applications_submitted_30d', 0) >= 1: sig += 0.04
    if s.get('avg_response_time_hours', 99.0) <= 4.0: sig += 0.04
    
    engagement_signal_score = min(sig, 1.0)

    # ─── COMPONENT E: education_score (0.0–1.0) ─────────────────────────────
    tier_map = {'tier_1': 1.0, 'tier_2': 0.75, 'tier_3': 0.50, 'tier_4': 0.30, 'unknown': 0.40}
    edu_score = max((tier_map.get(e.get('tier','unknown'), 0.40)
                     for e in candidate.get('education',[])), default=0.30)
                     
    STEM_FIELDS = ['computer science','cs','machine learning','statistics',
                    'mathematics','electrical','electronics','information']
    field_bonus = 0.10 if any(f in (e.get('field_of_study') or '').lower()
                              for e in candidate.get('education',[])
                              for f in STEM_FIELDS) else 0.0
                              
    education_score = min(edu_score + field_bonus, 1.0)

    # ─── AVAILABILITY MULTIPLIER ─────────────────────────────────────────────
    mult = 1.0
    rrr = s.get('recruiter_response_rate', 1.0)
    icr = s.get('interview_completion_rate', 1.0)
    
    if not s.get('open_to_work_flag', False):
        if days_since > 365:   mult *= 0.65   # 1+ year inactive, not open
        elif days_since > 180: mult *= 0.80   # 6 months — gentle penalty
        # Under 180 days: no penalty
    # open_to_work_flag=True: NO multiplier penalty regardless of activity date

    if rrr < 0.10: mult *= 0.75   # almost never responds
    if icr < 0.25: mult *= 0.85   # ghosts interviews
    mult = max(mult, 0.50)         # floor — never drop below 50%
    availability_multiplier = mult

    # ─── DISQUALIFICATION PENALTY ────────────────────────────────────────────
    penalty = 0.0
    if career and all(is_services_firm(j.get('company', '')) for j in career):
        penalty += 0.35
        
    if any(t in current_title for t in ['marketing','sales','finance','hr manager','recruiter',
                                       'content writer','accountant','operations']):
        penalty += 0.50
        
    if yoe < 1.0:
        penalty += 0.25
        
    disqualification_penalty = min(penalty, 0.90)

    # ─── HONEYPOT PENALTY ────────────────────────────────────────────
    hp_res = detect_honeypot(candidate)
    hp_penalty = hp_res['penalty']

    # ─── RAW SCORE AND FINAL SCORE ───────────────────────────────────────────
    raw_score = (
        0.30 * skill_match_score       +
        0.25 * career_quality_score    +
        0.20 * role_fit_score          +
        0.15 * engagement_signal_score +
        0.10 * education_score
    ) - disqualification_penalty - hp_penalty

    final_score = raw_score * availability_multiplier
    final_score = max(min(final_score, 1.0), 0.0)

    return {
        'final_score': final_score,
        'raw_score': raw_score,
        'skill_match_score': skill_match_score,
        'career_quality_score': career_quality_score,
        'role_fit_score': role_fit_score,
        'engagement_signal_score': engagement_signal_score,
        'education_score': education_score,
        'disqualification_penalty': disqualification_penalty,
        'availability_multiplier': availability_multiplier,
        'honeypot_penalty': hp_penalty,
        'is_honeypot': hp_res['is_honeypot'],
        'triggered_signals': hp_res['triggered_signals'],
        'must_hits': must_hits,
        'components': {
            'skill_match': skill_match_score,
            'career_quality': career_quality_score,
            'role_fit': role_fit_score,
            'engagement': engagement_signal_score,
            'education': education_score
        }
    }
