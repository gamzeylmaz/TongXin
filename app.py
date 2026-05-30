"""
WeCare — AI Stress Support for International Students
Streamlit demo app: multi-step check-in → phenotype classification → recommendations

Run locally : streamlit run app.py
Deploy free : streamlit.io/cloud (connect GitHub repo)
"""

import streamlit as st
import re

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UniCare",
    page_icon="💚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 1.2rem 2rem; max-width: 480px; margin: auto; }

/* Typography */
body, .stApp { font-family: -apple-system, "PingFang SC", "Helvetica Neue", sans-serif; }

/* Progress bar */
.progress-wrap { background: #eee; border-radius: 99px; height: 5px; margin-bottom: 1.5rem; }
.progress-fill  { background: #07C160; border-radius: 99px; height: 5px;
                  transition: width .4s ease; }

/* Cards */
.card {
    background: #fff; border-radius: 16px;
    box-shadow: 0 2px 16px rgba(0,0,0,.08);
    padding: 1.5rem; margin-bottom: 1rem;
}
.card-dark {
    background: #1a1a1a; border-radius: 16px;
    padding: 1.5rem; margin-bottom: 1rem; color: #fff;
}

/* Welcome hero */
.hero { text-align: center; padding: 2rem 0 1rem; }
.hero-icon { font-size: 4rem; margin-bottom: .5rem; }
.hero-title { font-size: 2rem; font-weight: 700; color: #07C160; margin: 0; }
.hero-sub   { color: #666; font-size: .95rem; margin-top: .4rem; line-height: 1.5; }

/* Section labels */
.section-label {
    font-size: .75rem; font-weight: 600; letter-spacing: .08em;
    color: #07C160; text-transform: uppercase; margin-bottom: .5rem;
}
.question-text {
    font-size: 1rem; color: #222; font-weight: 500;
    margin-bottom: .6rem; line-height: 1.4;
}

/* Likert row */
.likert-label {
    display: flex; justify-content: space-between;
    font-size: .72rem; color: #999; margin-top: -.3rem; margin-bottom: .8rem;
    padding: 0 .2rem;
}

/* Result phenotype card */
.phenotype-card {
    border-radius: 20px; padding: 1.8rem; text-align: center;
    margin-bottom: 1.2rem; color: #fff;
}
.phenotype-icon  { font-size: 3rem; margin-bottom: .4rem; }
.phenotype-title { font-size: 1.4rem; font-weight: 700; margin: 0 0 .3rem; }
.phenotype-sub   { font-size: .9rem; opacity: .9; }

/* Score bar */
.score-wrap { margin: 1rem 0; }
.score-bar-bg { background: #eee; border-radius: 99px; height: 10px; }
.score-bar-fill { border-radius: 99px; height: 10px; transition: width .6s ease; }
.score-labels { display: flex; justify-content: space-between;
                font-size: .72rem; color: #999; margin-top: .3rem; }

/* Recommendation card */
.rec-card {
    background: #f8fffe; border: 1.5px solid #07C160;
    border-radius: 12px; padding: 1rem 1.1rem; margin-bottom: .7rem;
    display: flex; align-items: flex-start; gap: .8rem;
}
.rec-icon  { font-size: 1.4rem; flex-shrink: 0; }
.rec-title { font-weight: 600; font-size: .92rem; color: #222; margin-bottom: .15rem; }
.rec-body  { font-size: .83rem; color: #555; line-height: 1.4; }

/* Alert card */
.alert-card {
    background: #fff3f3; border: 1.5px solid #E05C5C;
    border-radius: 12px; padding: 1rem 1.1rem; margin-bottom: .7rem;
}

/* WeChat-style green button */
div.stButton > button {
    background: #07C160; color: #fff; border: none;
    border-radius: 99px; padding: .75rem 2rem;
    font-size: 1rem; font-weight: 600; width: 100%;
    cursor: pointer; transition: background .2s;
}
div.stButton > button:hover { background: #06ad56; }

/* Secondary button */
.btn-secondary {
    background: #f0f0f0; color: #333; border: none;
    border-radius: 99px; padding: .65rem 1.5rem;
    font-size: .9rem; font-weight: 500; width: 100%;
    cursor: pointer; margin-top: .5rem;
}

/* Stat chip */
.stat-row { display: flex; gap: .7rem; margin-bottom: 1rem; flex-wrap: wrap; }
.stat-chip {
    background: #f0faf5; border: 1.5px solid #07C160;
    border-radius: 99px; padding: .35rem .9rem;
    font-size: .82rem; font-weight: 600; color: #07C160;
}

/* Stressor pills */
.pill-wrap { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .5rem; }
.pill {
    background: #f0faf5; border: 1.5px solid #07C160;
    border-radius: 99px; padding: .3rem .8rem;
    font-size: .82rem; color: #07C160; font-weight: 500;
}

/* Divider */
.divider { border: none; border-top: 1px solid #eee; margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────────────
for key, default in {
    "step": 0,
    "stressors": [],
    "sleep": "",
    "study_level": "",
    "likert": {},
    "freetext": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Phenotype Data ────────────────────────────────────────────────────────────
PHENOTYPE_META = {
    "Academic Overload": {
        "icon": "📚", "color": "#E05C5C",
        "tagline": "Crushed by deadlines and academic demands",
        "recs": [
            ("📅", "Smart Study Planner",
             "Break your biggest task into 3 daily micro-goals. Start with just 25 minutes."),
            ("☕", "Micro-Break Alert",
             "Set a timer every 50 minutes. Step away, breathe, reset — it restores focus."),
            ("🎯", "Procrastination Reset",
             "Open your work, set a 2-minute timer, and just start. Momentum builds itself."),
        ],
    },
    "Social Isolation": {
        "icon": "🤝", "color": "#5C8EE0",
        "tagline": "Feeling disconnected from people around you",
        "recs": [
            ("🗓️", "Campus Events Near You",
             "ISO is hosting events this week. Check the notice board or ask your advisor."),
            ("👥", "Peer Mentor Match",
             "Connect with an international student from your region. You're not alone here."),
            ("💬", "Open a Conversation",
             "Text one person today — even a 'how are you?' can break the cycle of isolation."),
        ],
    },
    "Language/Cultural Adaptation": {
        "icon": "🌏", "color": "#5CC4A0",
        "tagline": "Navigating a new language and cultural environment",
        "recs": [
            ("✍️", "Writing Center",
             "Tongji's writing support is available for emails, reports, and thesis drafts."),
            ("🗣️", "Language Exchange",
             "Find a language partner: you help them with your language, they help with Chinese."),
            ("📋", "Email Template",
             "Need to ask your professor for an extension? We have a ready-made template for you."),
        ],
    },
    "Admin/Uncertainty": {
        "icon": "📋", "color": "#E0A95C",
        "tagline": "Stressed about visa, finances, or future plans",
        "recs": [
            ("🏛️", "ISO Office Resources",
             "The International Student Office handles visa questions, extensions, and documents."),
            ("💰", "Financial Support",
             "Emergency funds and scholarship extensions may be available — ask ISO confidentially."),
            ("🔍", "Career Services",
             "Internship platforms and career counselling are open to international students."),
        ],
    },
    "Well-Regulated": {
        "icon": "✨", "color": "#8E5CE0",
        "tagline": "Managing well — keep up the good work",
        "recs": [
            ("🌱", "Keep Your Routine",
             "Your current habits are working. Protect your sleep and social time this week."),
            ("📓", "Reflective Check-in",
             "Take 5 minutes to note what's going well — it builds resilience for harder weeks."),
            ("🤸", "Preventive Wellness",
             "This is a good time to explore a campus activity before the semester peaks."),
        ],
    },
}

LIKERT_OPTIONS = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
LIKERT_MAP     = {o: i + 1 for i, o in enumerate(LIKERT_OPTIONS)}
REVERSE_MAP    = {o: 5 - i for i, o in enumerate(LIKERT_OPTIONS)}

QUESTIONS = [
    ("q9",  "I feel overwhelmed by my responsibilities.",           "stress"),
    ("q11", "I feel mentally exhausted.",                           "stress"),
    ("q12", "I have difficulty concentrating.",                     "stress"),
    ("q14", "I feel pressure due to deadlines or unfinished work.", "stress"),
    ("q15", "I feel anxious about upcoming tasks or events.",       "stress"),
    ("q16", "I feel supported by people around me.",                "protective"),
    ("q18", "I have enough time to rest and recover.",              "protective"),
]

STRESSOR_OPTIONS = [
    "Thesis / Research", "Coursework", "Exams",
    "Job / Internship", "Finances", "Relationships", "Health"
]

ACADEMIC_KW   = ["thesis","deadline","assignment","exam","research","paper","submit",
                 "exhausted","drained","overwhelmed","procrastinat","stuck","behind",
                 "too much","so much","loaded","pressure","busy","homework","class",
                 "coursework","studying","supervisor","report"]
ISOLATION_KW  = ["alone","lonely","no one","nobody","by myself","isolated","homesick",
                 "miss home","miss my family","no friends","don't know anyone","toll on mental",
                 "traumatized","no support","objectif","stared at","violated"]
CULTURAL_KW   = ["language","understand","communicate","chinese","mandarin","english",
                 "translation","culture shock","confused","different here","not used to",
                 "life here","exchange","lost in translation"]
ADMIN_KW      = ["visa","permit","immigration","documents","money","financial","afford",
                 "rent","tuition","scholarship","broke","salary","job","internship",
                 "career","future","worried about","uncertain","survive","regulation"]
POSITIVE_KW   = ["good","great","fine","alright","okay","well","enjoying","enjoy",
                 "happy","awesome","fulfilling","stable","better","improving","glad",
                 "so far so good","everything is good"]
ESCALATION_KW = ["can't go on","hopeless","no point","don't want to be here",
                 "want to die","suicid","harm myself","end it"]

def kw_score(text, kws):
    t = text.lower()
    return sum(1 for kw in kws if kw in t)

def classify(answers, stressors, freetext):
    lk = answers
    text = freetext or ""

    scores = {}
    for qid, _, kind in QUESTIONS:
        val = lk.get(qid, "Neutral")
        scores[qid] = LIKERT_MAP[val] if kind == "stress" else REVERSE_MAP[val]

    composite = sum(scores.values())  # 7–35 range; map to 10–50 equivalent
    composite_50 = round(composite / 35 * 50)

    q9  = scores["q9"]
    q11 = scores["q11"]
    q12 = scores["q12"]
    q14 = scores["q14"]
    q15 = scores["q15"]
    q16 = scores["q16"]  # already reverse-scored
    q18 = scores["q18"]  # already reverse-scored

    nlp_acad = kw_score(text, ACADEMIC_KW)
    nlp_iso  = kw_score(text, ISOLATION_KW)
    nlp_cult = kw_score(text, CULTURAL_KW)
    nlp_adm  = kw_score(text, ADMIN_KW)
    nlp_pos  = kw_score(text, POSITIVE_KW)
    txt_len  = len(text.split())

    has_acad_stressor = any(s in stressors for s in
                            ["Thesis / Research", "Coursework", "Exams"])
    has_adm_stressor  = any(s in stressors for s in
                            ["Job / Internship", "Finances"])

    phenotypes = []

    # Well-Regulated
    if composite <= 14 and nlp_pos >= 1 and nlp_iso == 0 and nlp_acad <= 1:
        return "Well-Regulated", composite_50, False

    # Academic Overload
    acad_likert = sum([q9 >= 4, q11 >= 4, q14 >= 4, q18 >= 4])
    if acad_likert >= 2 or (acad_likert >= 1 and nlp_acad >= 1) or \
       (has_acad_stressor and nlp_acad >= 1):
        phenotypes.append("Academic Overload")

    # Social Isolation
    if q16 >= 4 or nlp_iso >= 1:
        phenotypes.append("Social Isolation")

    # Admin/Uncertainty
    if (q15 >= 4 and has_adm_stressor) or nlp_adm >= 2:
        phenotypes.append("Admin/Uncertainty")

    # Language/Cultural
    if nlp_cult >= 1 or (q12 >= 4 and txt_len < 10 and txt_len > 0):
        phenotypes.append("Language/Cultural Adaptation")

    if not phenotypes:
        primary = "Well-Regulated" if composite <= 17 else "Academic Overload"
    else:
        primary = phenotypes[0]

    escalation = (
        any(kw in text.lower() for kw in ESCALATION_KW) or
        composite_50 >= 42
    )
    return primary, composite_50, escalation

# ── Progress Bar ──────────────────────────────────────────────────────────────
TOTAL_STEPS = 4  # 0=welcome, 1=context, 2=likert, 3=freetext, 4=results

def progress_bar(step):
    if step == 0:
        return
    pct = min(int((step / TOTAL_STEPS) * 100), 100)
    st.markdown(f"""
    <div class="progress-wrap">
      <div class="progress-fill" style="width:{pct}%"></div>
    </div>
    """, unsafe_allow_html=True)

# ── Step 0: Welcome ───────────────────────────────────────────────────────────
def render_welcome():
    st.markdown("""
    <div class="hero">
      <div class="hero-icon">💚</div>
      <p class="hero-title">UniCare</p>
      <p class="hero-sub">
        AI-powered stress support for<br>international students at Tongji University
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <div class="section-label">How it works</div>
      <p style="font-size:.9rem; color:#444; line-height:1.6; margin:0;">
        ① Answer a short check-in (2 min)<br>
        ② Our AI identifies your <b>stress phenotype</b><br>
        ③ Get personalised support recommendations
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stat-row">
      <div class="stat-chip">📊 30/33 open to use</div>
      <div class="stat-chip">🧪 Pilot study (n=33)</div>
      <div class="stat-chip">🔒 Anonymous</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Start Check-in →"):
        st.session_state.step = 1
        st.rerun()

# ── Step 1: Context ───────────────────────────────────────────────────────────
def render_context():
    progress_bar(1)
    st.markdown('<div class="section-label">Step 1 of 3 — Quick Context</div>',
                unsafe_allow_html=True)
    st.markdown("### What's been pressing on you lately?")

    stressors = st.multiselect(
        "Select all that apply:",
        STRESSOR_OPTIONS,
        default=st.session_state.stressors,
        label_visibility="collapsed"
    )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("### How much are you sleeping on weekdays?")
    sleep = st.radio(
        "Sleep:",
        ["Less than 5 hours", "5–6 hours", "6–7 hours", "7–8 hours", "More than 8 hours"],
        index=2,
        horizontal=False,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.step = 0
            st.rerun()
    with col2:
        if st.button("Next →"):
            st.session_state.stressors = stressors
            st.session_state.sleep = sleep
            st.session_state.step = 2
            st.rerun()

# ── Step 2: Likert Questions ──────────────────────────────────────────────────
def render_likert():
    progress_bar(2)
    st.markdown('<div class="section-label">Step 2 of 3 — How Are You Feeling?</div>',
                unsafe_allow_html=True)
    st.markdown("Rate how much you agree with each statement **this week**.")
    st.markdown("")

    answers = dict(st.session_state.likert)

    for qid, text, _ in QUESTIONS:
        st.markdown(f'<p class="question-text">{text}</p>', unsafe_allow_html=True)
        val = st.radio(
            label=qid,
            options=LIKERT_OPTIONS,
            index=LIKERT_OPTIONS.index(answers.get(qid, "Neutral")),
            horizontal=True,
            label_visibility="collapsed",
            key=f"radio_{qid}"
        )
        st.markdown("""
        <div class="likert-label">
          <span>Strongly Disagree</span><span>Strongly Agree</span>
        </div>
        """, unsafe_allow_html=True)
        answers[qid] = val

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.likert = answers
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Next →"):
            st.session_state.likert = answers
            st.session_state.step = 3
            st.rerun()

# ── Step 3: Free Text ─────────────────────────────────────────────────────────
def render_freetext():
    progress_bar(3)
    st.markdown('<div class="section-label">Step 3 of 3 — Quick Message</div>',
                unsafe_allow_html=True)
    st.markdown("### Text a close friend about your week.")
    st.markdown(
        '<p style="color:#888; font-size:.88rem;">1–3 sentences, casual language. '
        'This is analysed privately by the AI.</p>',
        unsafe_allow_html=True
    )

    text = st.text_area(
        label="message",
        value=st.session_state.freetext,
        placeholder='e.g. "This week was so tough, kinda drained. My thesis deadline is next week '
                    'and I haven\'t slept properly in days..."',
        height=130,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.freetext = text
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("See My Results →"):
            st.session_state.freetext = text
            st.session_state.step = 4
            st.rerun()

# ── Step 4: Results ───────────────────────────────────────────────────────────
def render_results():
    phenotype, composite_50, escalation = classify(
        st.session_state.likert,
        st.session_state.stressors,
        st.session_state.freetext
    )
    meta = PHENOTYPE_META[phenotype]

    # ── Phenotype card ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="phenotype-card" style="background: linear-gradient(135deg, {meta['color']}dd, {meta['color']}99);">
      <div class="phenotype-icon">{meta['icon']}</div>
      <p class="phenotype-title">{phenotype}</p>
      <p class="phenotype-sub">{meta['tagline']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stress score bar ──────────────────────────────────────────────────────
    pct = int((composite_50 - 10) / 40 * 100)
    bar_color = (
        "#5CC4A0" if composite_50 <= 25 else
        "#E0A95C" if composite_50 <= 36 else
        "#E05C5C"
    )
    level_label = (
        "Low" if composite_50 <= 25 else
        "Moderate" if composite_50 <= 36 else
        "High" if composite_50 <= 44 else
        "Very High"
    )
    st.markdown(f"""
    <div class="card">
      <div class="section-label">Stress Intensity — {level_label}</div>
      <div class="score-wrap">
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="width:{pct}%; background:{bar_color};"></div>
        </div>
        <div class="score-labels"><span>Low</span><span>Moderate</span><span>High</span></div>
      </div>
      <p style="font-size:.85rem; color:#555; margin:0;">
        Composite stress index: <b>{composite_50}/50</b>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Escalation alert ──────────────────────────────────────────────────────
    if escalation:
        st.markdown("""
        <div class="alert-card">
          <p style="font-weight:700; color:#E05C5C; margin:0 0 .3rem;">⚠️ We're concerned about you</p>
          <p style="font-size:.87rem; color:#444; margin:0; line-height:1.5;">
            Your check-in suggests you may be under significant strain.
            Please consider contacting the <b>International Student Office</b> or a counsellor.
            You don't have to handle this alone.
          </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Stressor summary ──────────────────────────────────────────────────────
    if st.session_state.stressors:
        pills = "".join(f'<span class="pill">{s}</span>'
                        for s in st.session_state.stressors)
        st.markdown(f"""
        <div style="margin-bottom:1rem;">
          <div class="section-label">Your Stressors</div>
          <div class="pill-wrap">{pills}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Free text echo ────────────────────────────────────────────────────────
    if st.session_state.freetext.strip():
        preview = st.session_state.freetext[:120]
        if len(st.session_state.freetext) > 120:
            preview += "…"
        st.markdown(f"""
        <div class="card" style="background:#fafafa;">
          <div class="section-label">AI read your message</div>
          <p style="font-size:.87rem; color:#555; font-style:italic; margin:0;">"{preview}"</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:.5rem;">Personalised for You</div>',
                unsafe_allow_html=True)
    for icon, title, body in meta["recs"]:
        st.markdown(f"""
        <div class="rec-card">
          <div class="rec-icon">{icon}</div>
          <div>
            <div class="rec-title">{title}</div>
            <div class="rec-body">{body}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── ISO contact ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="card" style="background:#f0faf5; border:1.5px solid #07C160;">
      <div style="display:flex; align-items:center; gap:.8rem;">
        <span style="font-size:1.6rem;">🏛️</span>
        <div>
          <div style="font-weight:600; font-size:.9rem; color:#222;">International Student Office Support</div>
          <div style="font-size:.82rem; color:#555;">
            For campus support resources, referral pathways, and next-step guidance
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer actions ────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'>", unsafe_allow_html=True)
    if st.button("🔄 New Check-in"):
        for key in ["step", "stressors", "sleep", "study_level", "likert", "freetext"]:
            st.session_state[key] = [] if key in ("stressors",) else \
                                    {} if key == "likert" else \
                                    0  if key == "step" else ""
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <p style="text-align:center; font-size:.75rem; color:#bbb; margin-top:1.5rem;">
      UniCare is a screening tool, not a clinical assessment.<br>
      Your data is anonymous and never shared.
    </p>
    """, unsafe_allow_html=True)

# ── Router ────────────────────────────────────────────────────────────────────
STEPS = {
    0: render_welcome,
    1: render_context,
    2: render_likert,
    3: render_freetext,
    4: render_results,
}

STEPS[st.session_state.step]()
