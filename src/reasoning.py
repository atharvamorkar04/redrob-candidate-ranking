JD_PRIORITY_SKILLS = [
    'Sentence Transformers','FAISS','Pinecone','Weaviate','Qdrant','Milvus',
    'Elasticsearch','OpenSearch','Vector Search','Semantic Search','Embeddings',
    'Learning to Rank','NDCG','Information Retrieval','Dense Retrieval',
    'LoRA','QLoRA','PEFT','XGBoost','LightGBM','RAG','Recommendation Systems',
    'Reranking','BM25','Hybrid Search','PyTorch','TensorFlow','Python','NLP',
]

def generate_reasoning(candidate, score, rank, score_breakdown):
    p   = candidate['profile']
    rs  = candidate['redrob_signals']
    yoe = p['years_of_experience']
    title   = p['current_title']
    company = p.get('current_company', '')
    bd      = score_breakdown

    # Pick best JD-relevant skill
    skill_names = {s['name'] for s in candidate.get('skills', [])}
    jd_skill = next((ps for ps in JD_PRIORITY_SKILLS if ps in skill_names), None)
    if not jd_skill:
        adv = [s['name'] for s in candidate.get('skills',[])
               if s['proficiency'] in ('advanced','expert')]
        jd_skill = adv[0] if adv else None

    # Primary strength
    must = bd.get('must_hits', 0)
    cq   = bd['components']['career_quality']
    if must == 4:    strength = 'hits all 4 JD must-haves'
    elif must == 3:  strength = 'hits 3/4 JD must-haves'
    elif jd_skill:   strength = f'{jd_skill} aligns with JD core requirements'
    elif cq > 0.80:  strength = 'strong product-company AI career trajectory'
    else:            strength = 'adjacent ML background, potential fit'

    # Primary concern
    nd    = rs.get('notice_period_days', 90)
    rrr   = rs.get('recruiter_response_rate', 1.0)
    open_w= rs.get('open_to_work_flag', False)
    concern = ''
    if nd > 90:          concern = f' Notice {nd}d is long.'
    elif nd > 60:        concern = f' Notice: {nd}d.'
    elif not open_w:     concern = ' Not marked open-to-work.'
    elif rrr < 0.25:     concern = ' Low recruiter response rate.'
    elif must == 0:      concern = ' No direct JD skill match found.'

    yoe_str = f'{yoe:.1f}yr'
    if rank <= 5:
        nd_note = f', {nd}d notice' if nd <= 30 else ''
        r = f'{yoe_str} {title} at {company} — {strength}. Open-to-work{nd_note}.'
    elif rank <= 20:
        r = f'{yoe_str} {title} ({strength}).{concern}'
    elif rank <= 50:
        r = f'{yoe_str} {title} — {strength}. {must}/4 must-haves matched.{concern}'
    else:
        r = f'{yoe_str} {title} — peripheral fit. {must}/4 JD must-haves.{concern}'

    return ' '.join(r.split())[:200]

# Uniqueness guarantee — call in src/ranker.py before writing CSV:
def ensure_unique_reasonings(results):
    seen = set()
    for r in results:
        base = r['reasoning']
        if base in seen:
            r['reasoning'] = (base[:180] + f' [#{r["rank"]}]')[:200]
        seen.add(r['reasoning'])
    return results
