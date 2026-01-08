import streamlit as st
import ui

from agents import ResumeAnalyzerAgent
from auth import (
    init_db,
    init_analysis_table,
    login_user,
    register_user,
    logout_user,
    is_authenticated,
    save_resume_analysis,
    get_user_history,
    delete_single_history,
    clear_user_history
)

# ---------- DATABASE INIT ----------
init_db()
init_analysis_table()

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Resume Analyzer",
    layout="wide"
)

# ---------- AUTH UI ----------
def auth_ui():
    st.title("Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if login_user(email, password):
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.divider()

    st.subheader("Register")
    reg_email = st.text_input("Register Email", key="reg_email")
    reg_pass = st.text_input("Register Password", type="password", key="reg_password")

    if st.button("Register"):
        ok, msg = register_user(reg_email, reg_pass)
        st.info(msg)

# ---------- AUTH GUARD ----------
if not is_authenticated():
    auth_ui()
    st.stop()

# ---------- ROLE REQUIREMENTS ----------
ROLE_REQUIREMENTS = {
    "Data Engineer": [ "Python", "SQL", "Apache Spark", "Hadoop", "Kafka", "ETL Pipelines", "Airflow", "BigQuery", "Redshift", "Data Warehousing", "Snowlakes", "Azure Data Factory", "GCP", "AWS Glue", "DBT" ], 

    "DevOps Engineer": [ "Docker", "Kubernetes", "CI/CD", "Jenkins", "Terraform", "Azure", "GCP", "Prometheus", "Grafana", "Hlem", "Linux", "Administartion", "Networking", "Site Reliability Engineering (SRE)" ],

    "AL/ML Engineer": [ "python", "Pytorch", "Tensorflow", "Machine Learning", "Deep Learning", "MLOps", "Scikit-learn", "NLP", "Computer Vision", "Reinforcement Learning" ],

    "Frontend Engineer": [ "React", "Javascript", "HTML", "CSS", "Vue", "Angular", "Typescript", "Next.js", "Bootstrap", "Tailwind CSS", "GraphQL", "Redux", "Web Assembly", "Three.js", "Performance Optimization" ],

    "backend Engineer": [ "Python", "Django", "Flask", "Node.js", "REST APIs", "GraphQL", "Redux", "Kubernetes", "Docker", "Microservices", "gRPC", "Spring Boot", "FastAPI", "SQL & NoSQL Databases", "Redis", "CI/CD", "Cloud Services", "Java" ], 

    "Full Stack Developer": [ "JavaScript", "TypeScript", "React", "Node.js", "Express.js", "MongoDB", "SQL", "HTML5", "CSS3", "RESTful APIS", "Git", "CI/CD", "Cloud Services", "Responsive Design", "Authentication & Authorization", "RESTful APIs" ],

    "Product Manager": [ "Product Strategy", "User Research", "Agile Methodology", "Roadmapping", "Market Analyst", "Stakeholder Management", "Data Analyst", "User Steroids", "Market Analysis", "Product Lifecycle", "A/B Testing", "KPI Definition", "Prioritization", "Competitive Analysis", "Customer Journey Mapping" ],

    "Data Scientist": [ "Python", "R", "SQL", "Machine Learning", "Statistics", "Data  Visualization", "Pandas", "Numpy", "Scikit-learn", "Jupyter", "Hypothesis Testing", "Experimental Design", "Feature Engineering", "Model Evaluation" ], 


}

# ---------- SESSION STATE ----------
if "resume_agent" not in st.session_state:
    st.session_state.resume_agent = None
if "resume_analyzed" not in st.session_state:
    st.session_state.resume_analyzed = False
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "selected_role" not in st.session_state:
    st.session_state.selected_role = None

# ---------- AGENT SETUP ----------
def setup_agent(config):
    if not config.get("API_KEY"):
        st.info("⬅️ Enter API key in sidebar")
        return None

    if st.session_state.resume_agent is None:
        st.session_state.resume_agent = ResumeAnalyzerAgent(config["API_KEY"])

    return st.session_state.resume_agent

# ---------- ANALYZE RESUME ----------
def analyze_resume(agent, resume_file, role, custom_jd):
    result = agent.analyze_resume(
        resume_file,
        role_requirements=ROLE_REQUIREMENTS[role],
        custom_jd=custom_jd
    )

    save_resume_analysis(
        st.session_state.get("user_email"),
        role,
        result
    )

    st.session_state.resume_analyzed = True
    st.session_state.analysis_results = result
    st.session_state.selected_role = role

# ---------- MAIN APP ----------
def main():
    ui.setup_page()
    ui.display_header()

    # ---------- SIDEBAR ----------
    config = ui.setup_sidebar()

    with st.sidebar:
        st.divider()
        st.write(f"👤 Logged in as: {st.session_state.get('user_email')}")
        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()

    agent = setup_agent(config)

    # ---------- TABS ----------
    tabs = ui.create_tabs()

    # ================= TAB 1: RESUME ANALYSIS =================
    with tabs[0]:
        role, custom_jd = ui.role_selection_section(ROLE_REQUIREMENTS)
        uploaded = ui.resume_upload_section()

        if st.button("Analyze Resume"):
            if not agent:
                st.warning("Enter API key first")
            elif not uploaded:
                st.warning("Upload resume")
            else:
                analyze_resume(agent, uploaded, role, custom_jd)

        if st.session_state.analysis_results:
            ui.display_analysis_results(st.session_state.analysis_results)

    # ================= TAB 2: RESUME Q&A =================
    with tabs[1]:
        ui.resume_qa_section(
            st.session_state.resume_analyzed,
            lambda q: st.session_state.resume_agent.ask_question(q)
            if st.session_state.resume_agent else "Analyze resume first."
        )

    # ================= TAB 3: INTERVIEW =================
    with tabs[2]:
        ui.interview_questions_section(
            st.session_state.resume_analyzed,
            lambda role, diff, count:
                st.session_state.resume_agent.generate_interview_questions(
                    role, diff, count
                ),
            st.session_state.selected_role
        )

        st.divider()
        st.subheader("🧪 Answer Evaluation")

        question = st.text_input("Interview Question")
        answer = st.text_area("Your Answer")

        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)

        if st.button("Evaluate Answer"):
            if not answer.strip():
                st.warning("Write an answer")
            else:
                result = st.session_state.resume_agent.evaluate_interview_answer(
                    question,
                    answer,
                    st.session_state.selected_role,
                    difficulty
                )

                st.metric("Score", f"{result['score']} / 10")
                st.success("Strengths")
                for s in result["strengths"]:
                    st.write(f"✔ {s}")

                st.error("Improvements")
                for m in result["missing"]:
                    st.write(f"✖ {m}")

                st.info("Improved Answer")
                st.write(result["improved_answer"])

    # ================= TAB 4: HISTORY =================
    with tabs[3]:
        st.subheader("📜 Resume Analysis History")

        if st.button("🗑️ Clear All History"):
            clear_user_history(st.session_state.get("user_email"))
            st.rerun()

        history = get_user_history(st.session_state.get("user_email"))

        if not history:
            st.info("No history found.")
        else:
            for h in history:
                with st.expander(f"{h['role']} | {h['created_at']}"):
                    st.metric("Overall Score", f"{h['overall_score']} / 100")
                    st.metric("ATS Score", f"{h['ats_score']} / 100")

                    st.write("**Strengths:**")
                    st.write(h["strengths"])

                    st.write("**Missing Skills:**")
                    st.write(h["missing_skills"])

                    if st.button(
                        "❌ Delete This Analysis",
                        key=f"delete_{h['id']}"
                    ):
                        delete_single_history(h["id"])
                        st.rerun()

# ---------- RUN ----------
if __name__ == "__main__":
    main()
