import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import time
import tempfile
from src.ranker import run_ranking
from src.scorer import score_candidate
from src.honeypot import detect_honeypot

def render_radar_chart(score_breakdown, candidate_id):
    categories = ['Skill Match','Career Quality','Role Fit','Engagement','Education']
    values = [
        score_breakdown['components'].get('skill_match',0),
        score_breakdown['components'].get('career_quality',0),
        score_breakdown['components'].get('role_fit',0),
        score_breakdown['components'].get('engagement',0),
        score_breakdown['components'].get('education',0),
    ]
    values_c = values + [values[0]]
    cats_c   = categories + [categories[0]]
    fig = go.Figure(go.Scatterpolar(
        r=values_c, theta=cats_c, fill='toself',
        fillcolor='rgba(225,29,72,0.15)',
        line=dict(color='#f59e0b',width=2),
        name=candidate_id
    ))
    fig.update_layout(
        polar=dict(bgcolor='#000000',
            radialaxis=dict(visible=True,range=[0,1],tickfont=dict(color='#71717A'),
                gridcolor='#2a2a2a',linecolor='#2a2a2a'),
            angularaxis=dict(tickfont=dict(color='#E4E4E7',size=11),
                gridcolor='#2a2a2a',linecolor='#2a2a2a')),
        paper_bgcolor='#000000',plot_bgcolor='#000000',
        font=dict(color='#E4E4E7'),showlegend=False,
        margin=dict(l=40,r=40,t=20,b=20),height=240)
    return fig

# 1. PAGE CONFIG
st.set_page_config(
    page_title='Redrob Ranker | AI Candidate Intelligence',
    page_icon='🧠',
    layout='wide',
    initial_sidebar_state='expanded'
)

# 2. CUSTOM CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* Main layout background and fonts */
    .stApp {
        background-color: #000000;
        color: #E4E4E7;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .block-container {
        padding-top: 3.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    [data-testid="stSidebar"], [data-testid="stSidebarContainer"], div.stSidebar {
        min-width: 380px !important;
        max-width: 380px !important;
        width: 380px !important;
    }
    [data-testid="stSidebar"] > div {
        min-width: 380px !important;
        padding-top: 2rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 3.5rem !important;
    }

    /* Responsive — mobile */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        [data-testid="stSidebar"], [data-testid="stSidebarContainer"], div.stSidebar {
            min-width: unset !important;
            max-width: unset !important;
            width: unset !important;
        }
    }

    /* Desktop — sidebar offset for footer */
    @media (min-width: 769px) {
        .footer-bar {
            left: 380px !important;
        }
    }

    /* Tabs cut off on mobile */
    div[data-testid="stHorizontalBlock"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
    }
    [data-testid="stTabs"] [role="tablist"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        scrollbar-width: none !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #2a2a2a;
    }
    [data-testid="stSidebarUserContent"] {
        padding: 20px 24px !important;
    }
    [data-testid="stSidebar"] [data-testid="element-container"] {
        margin-bottom: 8px !important;
    }

    /* Hide default menu and footer but keep the header collapse toggle button visible */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
    }
    div[data-testid="stHeaderDecoration"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        color: #f59e0b !important;
        background-color: #000000 !important;
        border-radius: 8px !important;
        border: 1px solid #2a2a2a !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="collapsedControl"] button {
        color: #f59e0b !important;
    }
    [data-testid="collapsedControl"]:hover {
        border-color: #f59e0b !important;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.4) !important;
    }

    /* Gold theme global accents */
    ::selection {
        background: #f59e0b40;
        color: #ffffff;
    }
    ::-webkit-scrollbar {
        width: 4px;
        background: #000000;
    }
    ::-webkit-scrollbar-thumb {
        background: #f59e0b;
        border-radius: 2px;
    }
    hr {
        border-color: #2a2a2a !important;
    }

    /* Style the tabs to have a dark theme with red accents */
    button[data-baseweb="tab"] {
        color: #71717A !important;
        background-color: transparent !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #fbbf24 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #f59e0b !important;
        border-bottom: 2px solid #f59e0b !important;
    }

    /* Streamlit primary button styling */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #fbbf24, #f59e0b) !important;
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* Streamlit download button styling */
    div.stDownloadButton > button {
        background-color: #000000 !important;
        color: #E4E4E7 !important;
        border: 1px solid #f59e0b !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        transition: all 0.3s ease !important;
        padding: 10px 20px !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #f59e0b !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3) !important;
    }

    /* Custom File Uploader */
    div[data-testid="stFileUploader"] {
        border: 1px dashed rgba(245, 158, 11, 0.3) !important;
        background-color: #000000 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #f59e0b !important;
        background-color: #0d0d0d !important;
    }

    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        color: #f59e0b !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #A1A1AA !important;
        font-size: 14px !important;
    }

    /* Custom Card styling with red hover border and subtle shadow */
    .candidate-card {
        background-color: #000000;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #2a2a2a;
        border-left: 5px solid #f59e0b;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    .candidate-card:hover {
        border-color: #f59e0b;
        box-shadow: 0 10px 30px rgba(245, 158, 11, 0.15);
        transform: translateY(-2px);
    }

    /* Custom Info & Warn styling override */
    div.stAlert {
        background-color: #000000 !important;
        border: 1px solid #2a2a2a !important;
        color: #E4E4E7 !important;
        border-radius: 8px !important;
    }

    /* Progress bar customization */
    div[data-testid="stProgress"] > div > div > div > div {
        background-color: #f59e0b !important;
    }

    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 6px;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
        font-family: 'Space Grotesk', sans-serif;
    }

    .badge-otw {
        background-color: rgba(245, 158, 11, 0.08);
        color: #bae6fd;
        border: 1px solid rgba(245, 158, 11, 0.25);
    }

    .badge-verified {
        background-color: rgba(24, 24, 27, 0.8);
        color: #E4E4E7;
        border: 1px solid rgba(63, 63, 70, 0.6);
    }

    .badge-urgent {
        background-color: rgba(245, 158, 11, 0.25);
        color: #bae6fd;
        border: 1px solid rgba(245, 158, 11, 0.5);
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #f59e0b;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
        animation: pulse 1.5s infinite;
        margin-right: 8px;
        vertical-align: middle;
    }

    @keyframes pulse {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
        }
        70% {
            transform: scale(1);
            box-shadow: 0 0 0 6px rgba(245, 158, 11, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
        }
    }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR
st.sidebar.markdown("""
<div style='padding: 8px 16px 8px 16px; margin-bottom: 0px;'>
    <div style='display: flex; align-items: center; margin-bottom: 2px;'>
        <span class='pulse-dot'></span>
        <span style='font-size: 22px; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif; letter-spacing: -0.5px;'>REDROB <span style='color: #f59e0b;'>RANK</span></span>
    </div>
    <div style='font-size: 12px; color: #71717A; font-family: "Plus Jakarta Sans", sans-serif;'>AI Candidate Discovery Core</div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader(
    "Upload candidates dataset", 
    type=["jsonl", "json", "gz"], 
    help="Accepts candidates.jsonl, candidates.json, or candidates.jsonl.gz"
)

# Try loading cached results or pre-computed submission.csv if they exist
results = []
metrics = {}

@st.cache_data
def process_data(file_path):
    t0 = time.time()
    res, metrics = run_ranking(file_path, top_k=100, return_metrics=True)
    elapsed = time.time() - t0
    
    pool_size = metrics['pool_size']
    cand_sec = pool_size / elapsed if elapsed > 0 else 0
    
    metrics['elapsed'] = elapsed
    metrics['cand_sec'] = cand_sec
    return res, metrics

run_pressed = st.sidebar.button("Run Ranking", width="stretch", type="primary")

if uploaded_file is not None:
    # Save file to temp path
    suffix = ".jsonl.gz" if uploaded_file.name.endswith(".gz") else (".json" if uploaded_file.name.endswith(".json") else ".jsonl")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
        
    if run_pressed:
        with st.spinner("Processing candidate profiles... (takes ~90 seconds)"):
            try:
                results, metrics = process_data(tmp_path)
                st.session_state['results'] = results
                st.session_state['metrics'] = metrics
                st.sidebar.success("Ranking Completed!")
            except Exception as e:
                st.sidebar.error(f"Error during execution: {e}")
            finally:
                os.remove(tmp_path)
else:
    # Check if we have pre-computed results in the local workspace or can fall back
    default_candidates_path = r"[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    from rank import find_candidates_file
    try:
        candidates_file_to_use = find_candidates_file(default_candidates_path)
    except SystemExit:
        candidates_file_to_use = None

    if candidates_file_to_use and run_pressed:
        with st.spinner("Running ranking on local workspace dataset..."):
            results, metrics = process_data(candidates_file_to_use)
            st.session_state['results'] = results
            st.session_state['metrics'] = metrics
            st.sidebar.success("Local Ranking Completed!")

# Retrieve session results
if 'results' in st.session_state:
    results = st.session_state['results']
    metrics = st.session_state['metrics']

# Display stats in sidebar if available
if metrics:
    st.sidebar.divider()
    st.sidebar.markdown(f"### Performance metrics")
    st.sidebar.metric("Total Pool Size", f"{metrics['pool_size']:,}")
    st.sidebar.metric("Time Taken", f"{metrics['elapsed']:.1f} s")
    st.sidebar.metric("Speed", f"{int(metrics['cand_sec']):,} candidates/sec")

# 4. MAIN AREA - HERO BANNER
st.markdown("""
<div style='background-color: #0d0d0d; border: 1px solid #2a2a2a; border-left: 3px solid #f59e0b; padding: 25px 30px; border-radius: 12px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;'>
    <div>
        <h1 style='margin: 0; color: #ffffff; font-family: "Space Grotesk", sans-serif; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;'>
            REDROB <span style='color: #f59e0b;'>RANKER</span>
        </h1>
        <p style='margin: 5px 0 0 0; color: #6b7280; font-size: 14px; font-family: "Plus Jakarta Sans", sans-serif;'>
            Advanced Neural & Behavioral Candidate Intelligence Dashboard
        </p>
    </div>
    <div style='display: flex; flex-wrap: wrap; gap: 8px;'>
        <div style='background-color: rgba(245, 158, 11, 0.08); border: 1px solid #f59e0b30; padding: 8px 16px; border-radius: 8px; text-align: center;'>
            <div style='font-size: 10px; text-transform: uppercase; color: #f59e0b; font-weight: 700; letter-spacing: 0.5px;'>Processing Core</div>
            <div style='font-size: 14px; color: #FFFFFF; font-weight: 600; font-family: "Space Grotesk", sans-serif;'>CPU / O(K) Heap</div>
        </div>
        <div style='background-color: rgba(245, 158, 11, 0.08); border: 1px solid #f59e0b30; padding: 8px 16px; border-radius: 8px; text-align: center;'>
            <div style='font-size: 10px; text-transform: uppercase; color: #f59e0b; font-weight: 700; letter-spacing: 0.5px;'>Model Precision</div>
            <div style='font-size: 14px; color: #FFFFFF; font-weight: 600; font-family: "Space Grotesk", sans-serif;'>4 Decimals</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Ranked Shortlist", 
    "📊 Score Analytics", 
    "🔍 Candidate Deep Dive", 
    "⚙️ System Info"
])

if not results:
    with tab1:
        st.markdown("""
        <div style='background-color: #0d0d0d; border: 1px solid #f59e0b20; border-left: 3px solid #f59e0b; padding: 16px 20px; border-radius: 8px; margin-bottom: 25px;'>
            <div style='color: #d1d5db; font-size: 14px; font-family: "Plus Jakarta Sans", sans-serif; line-height: 1.5;'>
                No upload needed — just click Run Ranking to start instantly.<br><br>
                The system auto-detects the local dataset. Upload a file only to rank a different dataset.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display scoring summary as card
        st.markdown("""
        <div style='background-color: #0d0d0d; border-radius: 12px; padding: 25px; border-left: 5px solid #f59e0b; border: 1px solid #2a2a2a; box-shadow: 0 4px 20px #f59e0b40;'>
            <h3 style='color: #f59e0b; margin-top: 0; font-family: "Space Grotesk", sans-serif; font-weight: 700;'>Redrob Ranker Intelligence Layer</h3>
            <ul style='line-height: 1.6; color: #d1d5db; font-family: "Plus Jakarta Sans", sans-serif;'>
                <li><strong style='color: #f59e0b;'>5-Component Hybrid Scorer:</strong> Evaluates every candidate across skill match, career quality, role fit, engagement signals, and education — weighted precisely for this role.</li>
                <li><strong style='color: #f59e0b;'>Semantic Career Reading:</strong> Reads full career history descriptions — not just skill tags — to find candidates who built recommendation systems, retrieval engines, or vector search pipelines even without exact JD keywords.</li>
                <li><strong style='color: #f59e0b;'>O(K) Heap Engine:</strong> Processes 100,000 candidates in under 60 seconds using a min-heap memory model — no GPU, no embeddings, no network calls required.</li>
                <li><strong style='color: #f59e0b;'>Honeypot Shield:</strong> Detects falsified profiles using 5 behavioural heuristics — impossible skill timelines, perfect engagement scores, and expert-level claims with zero evidence.</li>
                <li><strong style='color: #f59e0b;'>Availability Intelligence:</strong> Applies a dynamic multiplier based on open-to-work status, response rate, and activity recency — so only genuinely reachable candidates surface at the top.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
else:
    # ─── TAB 1: SHORTLIST ────────────────────────────────────────────────
    with tab1:
        st.subheader("Shortlisted Candidates (Top-100)")
        
        # Styled Pandas dataframe configuration
        df_shortlist = pd.DataFrame([
            {
                "Rank": r['rank'],
                "Candidate ID": r['candidate_id'],
                "Score": r['score'],
                "Current Title": r['profile'].get('current_title', 'N/A'),
                "Company": r['profile'].get('current_company', 'N/A'),
                "YOE": r['profile'].get('years_of_experience', 0.0),
                "Location": r['profile'].get('location', 'N/A'),
                "Reasoning": r['reasoning']
            } for r in results
        ])
        
        st.dataframe(
            df_shortlist,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    help="Candidate Score (0.0 to 1.0)",
                    format="%.4f",
                    min_value=0.0,
                    max_value=1.0,
                )
            },
            hide_index=True,
            width="stretch"
        )
        
        # Generate CSV data in-memory
        import io
        import csv
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
        for r in results:
            writer.writerow([
                r['candidate_id'],
                r['rank'],
                f"{r['score']:.4f}",
                r['reasoning']
            ])
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="Generate & Download atharvamorkar04_3026.csv",
            data=csv_data,
            file_name="atharvamorkar04_3026.csv",
            mime="text/csv",
            width="stretch"
        )
        
        st.write("---")
        st.subheader("Individual Candidate Breakdowns")
        
        # Individual expanders for deep breakdowns
        for r in results:
            rank = r['rank']
            cid = r['candidate_id']
            title = r['profile'].get('current_title', 'AI Engineer')
            company = r['profile'].get('current_company', 'Startup')
            score = r['score']
            
            # Select border color depending on rank tier
            if rank <= 10:
                tier_color = "#f59e0b"  # bright crimson red
            elif rank <= 30:
                tier_color = "#d97706"  # medium rose red
            elif rank <= 60:
                tier_color = "#92400e"  # deep burgundy
            else:
                tier_color = "#52525B"  # dark steel grey
                
            header_text = f"Rank {rank} | {cid} — {title} at {company} (Score: {score:.4f})"
            
            with st.expander(header_text):
                # Render badges
                s = r['signals']
                otw = s.get('open_to_work_flag', False)
                verified = s.get('verified_email', False) and s.get('verified_phone', False)
                notice = s.get('notice_period_days', 90)
                
                badges_html = ""
                if otw:
                    badges_html += "<span class='badge badge-otw'>Open to Work</span>"
                if verified:
                    badges_html += "<span class='badge badge-verified'>Verified Email/Phone</span>"
                if notice <= 30:
                    badges_html += f"<span class='badge badge-urgent'>Quick Joiner ({notice}d notice)</span>"
                else:
                    badges_html += f"<span class='badge badge-otw'>{notice}d notice</span>"
                    
                st.markdown(badges_html, unsafe_allow_html=True)
                
                sb = r['score_breakdown']
                
                col1, col2 = st.columns([3, 2])
                with col1:
                    col_radar, col_scores = st.columns([1,1])
                    with col_radar:
                        st.markdown('**Fit Profile**')
                        st.plotly_chart(render_radar_chart(sb, cid), use_container_width=True, key=f"radar_{cid}")
                    with col_scores:
                        st.markdown('**Component Scores**')
                        categories_map = {
                            'skill_match': 'Skill Match',
                            'career_quality': 'Career Quality',
                            'role_fit': 'Role Fit',
                            'engagement': 'Engagement',
                            'education': 'Education'
                        }
                        for comp, display_name in categories_map.items():
                            val = sb['components'].get(comp, 0.0)
                            st.metric(display_name, f'{val:.2f}')
                            st.progress(float(val))
                with col2:
                    st.markdown(f"**Reasoning Explanation:**")
                    st.info(r['reasoning'])
                    
                    st.write(f"**Experience:** {r['profile'].get('years_of_experience', 0.0)} YoE | **Availability Mult:** {sb.get('availability_multiplier', 1.0):.2f}")
                    if sb.get('disqualification_penalty', 0.0) > 0:
                        st.warning(f"⚠️ Disqualification Penalty applied: -{sb['disqualification_penalty']:.2f}")
                    if sb.get('honeypot_penalty', 0.0) > 0:
                        st.error(f"🚨 Honeypot Penalty applied: -{sb['honeypot_penalty']:.2f}")

    # ─── TAB 2: SCORE ANALYTICS ──────────────────────────────────────────
    with tab2:
        st.subheader("Interactive Shortlist Analysis")
        
        # 1. Score Distribution
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### Score Distribution (Top-100 vs Pool Sample)")
            if 'sample_scores' in metrics:
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=metrics['sample_scores'],
                    name='Full Pool Sample',
                    marker_color='#3F3F46',
                    opacity=0.6,
                    nbinsx=15
                ))
                fig.add_trace(go.Histogram(
                    x=[r['score'] for r in results],
                    name='Top 100 Shortlist',
                    marker_color='#f59e0b',
                    opacity=0.8,
                    nbinsx=10
                ))
                fig.update_layout(
                    barmode='overlay',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#F4F4F5'),
                    xaxis_title="Normalized Score",
                    yaxis_title="Count",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='#18181B'),
                    margin=dict(l=40, r=40, t=30, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
                
        # 2. Experience distribution
        with col2:
            st.markdown("### Experience Distribution (Top-100)")
            yoes = [r['profile'].get('years_of_experience', 0.0) for r in results]
            fig = px.histogram(
                x=yoes,
                nbins=10,
                color_discrete_sequence=['#d97706']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#F4F4F5'),
                xaxis_title="Years of Experience (YoE)",
                yaxis_title="Count",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#18181B'),
                margin=dict(l=40, r=40, t=30, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        col3, col4 = st.columns([1, 1])
        # 3. Component contributions (stacked bar of top 10 candidates)
        with col3:
            st.markdown("### Component Scores (Top-10 Candidates)")
            top_10 = results[:10]
            cids = [r['candidate_id'] for r in top_10]
            
            skills_c = [r['score_breakdown'].get('skill_match_score', 0) * 0.30 for r in top_10]
            career_c = [r['score_breakdown'].get('career_quality_score', 0) * 0.25 for r in top_10]
            role_c = [r['score_breakdown'].get('role_fit_score', 0) * 0.20 for r in top_10]
            engagement_c = [r['score_breakdown'].get('engagement_signal_score', 0) * 0.15 for r in top_10]
            edu_c = [r['score_breakdown'].get('education_score', 0) * 0.10 for r in top_10]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=cids, y=skills_c, name='Skill Match (30%)', marker_color='#f59e0b'))
            fig.add_trace(go.Bar(x=cids, y=career_c, name='Career Quality (25%)', marker_color='#d97706'))
            fig.add_trace(go.Bar(x=cids, y=role_c, name='Role Fit (20%)', marker_color='#92400e'))
            fig.add_trace(go.Bar(x=cids, y=engagement_c, name='Engagement (15%)', marker_color='#92400e'))
            fig.add_trace(go.Bar(x=cids, y=edu_c, name='Education (10%)', marker_color='#3F3F46'))
            
            fig.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#F4F4F5'),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#18181B'),
                margin=dict(l=40, r=40, t=30, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # 4. Top skills frequency in top 100
        with col4:
            st.markdown("### Top Skills in Shortlist")
            skills_count = {}
            for r in results:
                for s in r['skills']:
                    name = s.get('name', '').lower().strip()
                    if name:
                        skills_count[name] = skills_count.get(name, 0) + 1
            sorted_skills = sorted(skills_count.items(), key=lambda x: -x[1])[:20]
            
            fig = px.bar(
                x=[s[1] for s in sorted_skills],
                y=[s[0] for s in sorted_skills],
                orientation='h',
                color_discrete_sequence=['#f59e0b']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#F4F4F5'),
                xaxis_title="Count",
                yaxis_title="Skill Name",
                yaxis=dict(autorange="reversed"),
                xaxis=dict(showgrid=True, gridcolor='#18181B'),
                margin=dict(l=40, r=40, t=30, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # 5. Location Heatmap (Text-based city table)
        st.markdown("### Geographic Distribution (Top-100 Cities)")
        cities = {}
        for r in results:
            loc = r['profile'].get('location', 'Unknown').lower().split(',')[0].strip()
            cities[loc] = cities.get(loc, 0) + 1
        sorted_cities = sorted(cities.items(), key=lambda x: -x[1])
        
        cols = st.columns(min(len(sorted_cities), 6))
        for idx, (city, count) in enumerate(sorted_cities[:6]):
            with cols[idx]:
                st.metric(city.title(), f"{count} candidates")

    # ─── TAB 3: CANDIDATE DEEP DIVE ──────────────────────────────────────
    with tab3:
        st.subheader("Search and Audit Profiles")
        
        search_query = st.text_input("Search Candidate ID or current title (e.g. CAND_0007411, ML Engineer):", "")
        
        matching_candidates = []
        if search_query:
            q = search_query.lower()
            matching_candidates = [
                r for r in results 
                if q in r['candidate_id'].lower() or q in r['profile'].get('current_title', '').lower()
            ]
        else:
            matching_candidates = results[:3] # Show top 3 by default
            
        if not matching_candidates:
            st.warning("No candidate matching search query found.")
        else:
            selected_cid = st.selectbox(
                "Select a candidate to inspect:", 
                [c['candidate_id'] for c in matching_candidates]
            )
            
            cand = next(c for c in results if c['candidate_id'] == selected_cid)
            
            c_col1, c_col2 = st.columns([2, 1])
            with c_col1:
                st.markdown(f"## Candidate {cand['candidate_id']} Profile Details")
                st.markdown(f"**Current Role:** `{cand['profile'].get('current_title', 'N/A')}` at `{cand['profile'].get('current_company', 'N/A')}`")
                st.markdown(f"**Location:** {cand['profile'].get('location', 'N/A')} ({cand['profile'].get('country', 'N/A')})")
                st.markdown(f"**Experience:** {cand['profile'].get('years_of_experience', 0.0)} Years of Experience")
                
                # Career history timeline
                st.markdown("### Career History")
                for job in cand['career_history']:
                    st.markdown(f"""
                    **{job.get('title', 'N/A')}** at **{job.get('company', 'N/A')}**
                    *Duration:* {job.get('start_date', 'N/A')} to {job.get('end_date', 'N/A')} ({job.get('duration_months', 0)} months)
                    
                    {job.get('description', '')}
                    """)
                    st.divider()
                    
                # Education History
                st.markdown("### Education")
                for edu in cand['education']:
                    st.markdown(f"""
                    **{edu.get('degree', 'N/A')}** — {edu.get('field_of_study', 'N/A')} (Tier: `{edu.get('tier', 'unknown')}`)
                    *Institution:* {edu.get('school', 'N/A')} | *Graduated:* {edu.get('end_year', 'N/A')}
                    """)
                    
            with c_col2:
                st.markdown("### Audit Dashboard")
                st.metric("Final Rank", f"#{cand['rank']}")
                st.metric("Final Score", f"{cand['score']:.4f}")
                
                # Side-by-side score vs top 10 average
                top_10_avg = np.mean([c['score'] for c in results[:10]])
                
                fig = go.Figure()
                fig.add_trace(go.Indicator(
                    mode="gauge+number+delta",
                    value=cand['score'],
                    delta={'reference': top_10_avg, 'position': "top", 'relative': False, 'valueformat': '.4f'},
                    title={'text': "Score compared to Top-10 Avg"},
                    gauge={
                        'axis': {'range': [0, 1]},
                        'bar': {'color': "#f59e0b"},
                        'steps': [
                            {'range': [0, top_10_avg], 'color': "rgba(245, 158, 11, 0.1)"}
                        ],
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F4F4F5'))
                st.plotly_chart(fig, use_container_width=True)
                
                # Skills matrices
                st.markdown("### Skills Matrix")
                for s in cand['skills']:
                    prof = s.get('proficiency', '').upper()
                    st.write(f"- **{s.get('name')}**: `{prof}` ({s.get('duration_months', 0)}mo, {s.get('endorsements', 0)} endorsements)")
                    
                # Reasonings and penalties
                st.markdown("### Decision Explainer")
                st.info(cand['reasoning'])

    # ─── TAB 4: SYSTEM INFO ─────────────────────────────────────────────
    with tab4:
        st.subheader("System Architecture and Diagnostics")
        
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            st.markdown("""
            ### Scoring Algorithm Formula
            The system implements a rigid 5-component scoring index:
            ```
            raw_score = (
                0.30 * skill_match_score       +
                0.25 * career_quality_score    +
                0.20 * role_fit_score          +
                0.15 * engagement_signal_score +
                0.10 * education_score
            ) - disqualification_penalty - honeypot_penalty
            
            final_score = clip(raw_score * availability_multiplier, 0, 1)
            ```
            ### Weights Summary
            - **Skills Match (30%)**: Checks for embedding, vector DB, production Python, and evaluation keywords.
            - **Career Quality (25%)**: Penalizes IT Services, awards startup product DNA and ideal YOE range (5–9 yr).
            - **Role Fit (20%)**: Checks current title alignment, Indian geo proximity, notice period, and preferred work mode.
            - **Engagement Signals (15%)**: Assesses profile completeness, response rates, GitHub activity, and active frequency.
            - **Education (10%)**: Rates university tier and awards CS/STEM majors.
            """)
            
        with col_s2:
            st.markdown("### Honeypot Diagnostics")
            if metrics:
                st.metric("Estimated Honeypot Accounts Flagged", f"{metrics['est_honeypots']}")
                st.write("""
                **Active Shields:**
                1. *Company age paradox*: tenure > 48 months at fictitious companies.
                2. *Skill experience density*: sum of skill durations exceeds 14x YOE.
                3. *Expert proficiency anomalies*: expert skills with 0 months claimed.
                4. *Engagement paradox*: perfect 100% profiles across recruiter metrics.
                5. *Advanced low-duration*: >3 advanced skills with <3 months experience.
                6. *Expert low endorsement*: >5 expert skills with 0 endorsements.
                """)
            else:
                st.write("No metrics computed yet. Run ranking to inspect honeypot counts.")
                
        st.markdown('---')
        st.markdown('### Honeypot Detection Audit')

        honeypot_flagged  = metrics.get('honeypot_list', []) if metrics else []
        honeypot_in_top100= [r for r in results[:100] if r.get('honeypot_penalty',0) > 0] if results else []

        c1,c2,c3 = st.columns(3)
        c1.metric('Total Flagged', len(honeypot_flagged))
        c2.metric('In Top-100', len(honeypot_in_top100),
            delta='RISK' if len(honeypot_in_top100)>5 else 'Safe',
            delta_color='inverse')
        c3.metric('Disqualification Threshold','10')

        if honeypot_flagged:
            with st.expander(f'View {len(honeypot_flagged)} flagged candidates'):
                st.markdown('Detection criteria (any 2+ flags = honeypot):')
                st.markdown('- H1: Company tenure > 48 months at fictitious companies')
                st.markdown('- H2: Total skill duration months > YoE x 14 (impossible density)')
                st.markdown('- H3: proficiency=expert with duration_months=0')
                st.markdown('- H4: All engagement signals exactly 1.0 (suspiciously perfect)')
                st.markdown('- H5: >3 advanced/expert skills with duration < 3 months')
                st.markdown('- H6: >5 expert skills with zero endorsements')
                st.markdown('- H7: Last active date is prior to signup date (temporal anomaly)')
                st.dataframe(pd.DataFrame(honeypot_flagged)
                    [['candidate_id','final_score','current_title','honeypot_penalty']],
                    width="stretch")
        else:
            st.success('No honeypots detected in this candidate pool.')

st.markdown("""
<div class='footer-bar' style='position:fixed;bottom:0;left:0;right:0;
            background:#000000;
            border-top:1px solid #2a2a2a;
            padding:10px 24px;
            display:flex;
            flex-wrap:wrap;
            justify-content:space-between;
            align-items:center;
            gap:4px;
            z-index:999;'>
    <div style='color:#6b7280;font-size:11px;letter-spacing:1px;'>
        Built for
        <span style='color:#f59e0b;font-weight:600;'>
        Redrob × Hack2Skill</span>
        <span style='color:#6b7280;'> — India RUNS Data & AI Challenge</span>
    </div>
    <div style='color:#6b7280;font-size:11px;'>
        Developed by
        <span style='color:#ffffff;font-weight:600;'>Atharva Morkar</span>
    </div>
</div>
""", unsafe_allow_html=True)


