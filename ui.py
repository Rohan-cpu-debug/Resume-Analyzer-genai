import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Resume Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- PAGE SETUP ----------
def setup_page():
    st.markdown("""
        <style>
        html, body, [class*="css"] {
            background-color: #ffffff !important;
            color: #000000 !important;
        }

        .card {
            background: #ffffff !important;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #ddd;
        }

        .header-card {
            background-color: #0e1117 !important;
            padding: 26px;
            border-radius: 14px;
            border: 1px solid #222;
            text-align: center;
            margin-bottom: 18px;
        }

        .header-card h1 { color: #ffffff !important; }
        .header-card p { color: #cccccc !important; }

        div[data-testid="metric-container"] {
            background-color: #ffffff !important;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)


def display_header():
    st.markdown("""
    <div class="header-card">
        <h1>Euron Recruitment Agent</h1>
        <p>Resume Analyzer & Interview Prep</p>
    </div>
    """, unsafe_allow_html=True)


# ---------- SIDEBAR ----------
def setup_sidebar():
    with st.sidebar:
        api_key = st.text_input("API Key", type="password")
    return {"API_KEY": api_key}


# ---------- ROLE SELECTION ----------
def role_selection_section(role_requirements):
    role = st.selectbox("Select role", list(role_requirements.keys()))
    custom_jd = st.file_uploader("Optional JD", type=["pdf", "txt"])
    return role, custom_jd


# ---------- RESUME UPLOAD ----------
def resume_upload_section():
    return st.file_uploader("Upload Resume (PDF)", type=["pdf"])


# ---------- SCORE PIE ----------
def create_score_pie_chart(score):
    fig, ax = plt.subplots()
    ax.pie([score, 100 - score], labels=["Score", "Remaining"], autopct="%1.0f%%")
    return fig


# ---------- ANALYSIS RESULT ----------
def display_analysis_results(result):
    if not result:
        return

    st.subheader("📊 Resume Evaluation Summary")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric("Overall Resume Score", f"{result['overall_score']} / 100")
        st.pyplot(create_score_pie_chart(result["overall_score"]))

    with col2:
        st.metric("ATS Compatibility Score", f"{result['ats_score']} / 100")
        st.write(
            f"🔑 Keyword Match: "
            f"**{result['ats_keywords_matched']} / {result['ats_total_keywords']}**"
        )

        for feedback in result.get("ats_feedback", []):
            st.info(feedback)

        st.divider()
        st.subheader("📌 Section-wise Breakdown")

        breakdown = result.get("score_breakdown", {})

        st.progress(breakdown.get("skill_match", 0) / 40)
        st.caption(f"Skill Match: {breakdown.get('skill_match', 0)} / 40")

        st.progress(breakdown.get("critical_skills", 0) / 30)
        st.caption(f"Critical Skills: {breakdown.get('critical_skills', 0)} / 30")

        st.progress(breakdown.get("experience_relevance", 0) / 20)
        st.caption(f"Experience Relevance: {breakdown.get('experience_relevance', 0)} / 20")

        st.progress(breakdown.get("resume_structure", 0) / 10)
        st.caption(f"Resume Structure: {breakdown.get('resume_structure', 0)} / 10")

    st.divider()
    st.subheader("✔ Strengths")
    st.write(result.get("strengths", []))

    st.subheader("❌ Missing Skills")
    st.write(result.get("missing_skills", []))


# ---------- RESUME IMPROVEMENT (NEW – SAFE ADDITION) ----------
def resume_improvement_section(has_resume, analysis_result):
    if not has_resume or not analysis_result:
        st.warning("Please analyze your resume first.")
        return

    st.subheader("🚀 Resume Improvement Guide")

    score = analysis_result["overall_score"]

    if score >= 80:
        st.success("Your resume is strong. Minor optimizations can improve ATS ranking.")
    elif score >= 60:
        st.warning("Your resume is decent but needs improvement.")
    else:
        st.error("Your resume needs significant improvement.")

    st.divider()
    st.subheader("❌ Missing Skills to Add")
    missing = analysis_result.get("missing_skills", [])
    if missing:
        for skill in missing:
            st.write(f"• Add experience or projects related to **{skill}**")
    else:
        st.write("No critical skills missing 🎉")

    st.divider()
    st.subheader("🛠 Improvement Checklist")

    st.checkbox("Add missing role-specific skills")
    st.checkbox("Include measurable achievements (numbers, impact)")
    st.checkbox("Improve project descriptions with tools & outcomes")
    st.checkbox("Optimize keywords for ATS")
    st.checkbox("Keep resume length between 1–2 pages")

    st.divider()
    st.subheader("📌 ATS Optimization Tips")
    st.write("""
    • Use standard headings (Skills, Experience, Projects, Education)  
    • Avoid tables and graphics  
    • Match keywords exactly from the job description  
    • Use simple fonts (Calibri, Arial, Times New Roman)  
    """)


# ---------- RESUME Q&A ----------
def resume_qa_section(has_resume, ask_fn):
    if not has_resume:
        st.warning("Please analyze the resume first.")
        return

    st.subheader(" Resume Q&A")

    questions = [
        "Give a short summary of my resume",
        "What are my key skills?",
        "Which skills match the selected role?",
        "What experience do I have?",
        "Do I have internship experience?",
        "What projects are mentioned?",
        "What is my educational background?",
        "What technologies do I know?",
        "What are my strengths?",
        "What skills are missing for this role?",
        "How suitable is my resume for the role?",
        "Does my resume mention certifications?",
        "What should I improve in my resume?"
    ]

    cols = st.columns(2)
    for i, q in enumerate(questions):
        if cols[i % 2].button(q, key=f"qa_btn_{i}"):
            st.write(ask_fn(q))


# ---------- INTERVIEW QUESTIONS ----------
def interview_questions_section(has_resume, gen_fn, role=None):
    if not has_resume:
        st.warning("Please analyze the resume first.")
        return

    st.subheader(" Interview Questions")

    difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)
    count = st.slider("Number of Questions", 3, 10, 5)

    if st.button("Generate Interview Questions"):
        questions = gen_fn(role, difficulty, count)
        for i, q in enumerate(questions, 1):
            st.write(f"**Q{i}.** {q}")

    st.divider()
    if st.button("🧑‍💼 HR Questions"):
        hr_questions = [
            "Tell me about yourself",
            "Why should we hire you?",
            "What are your strengths?",
            "What is your weakness?",
            "Why this company?",
            "Where do you see yourself in 5 years?",
            "Describe a challenge you faced",
            "Tell me about your project",
            "How do you handle pressure?",
            "Do you have any questions for us?"
        ]
        for i, q in enumerate(hr_questions, 1):
            st.write(f"**Q{i}.** {q}")

# ---------- TABS ----------

# ---------- TABS ----------
def create_tabs():
    return st.tabs([
        "Resume Analysis",
        "Resume Q&A",
        "Interview Questions",
        "History"
    ])

