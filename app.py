import os
import uuid

import streamlit as st
from dotenv import load_dotenv

from career_agent import CAREER_OPTIONS, career_agent, run_career_agent

load_dotenv()

st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 CareerCompass AI – Career Advisor Agent")
st.caption("LangGraph project using Conditional Routing + Iterative Retry Loop")

with st.sidebar:
    st.header("Project Requirements")
    st.success("TypedDict State")
    st.success("Conditional Edges")
    st.success("Iterative Loop")
    st.success("Tool Usage: DuckDuckGo Search")
    st.success("MemorySaver with thread_id")
    st.success("Pydantic Structured Output")
    st.divider()
    st.markdown("**Workflow Type:** Conditional + Iterative")
    st.markdown("**Routes:** " + ", ".join(CAREER_OPTIONS))

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"student_{uuid.uuid4().hex[:8]}"

if "example" not in st.session_state:
    st.session_state.example = "AI Engineer Example"

examples = {
    "AI Engineer Example": {
        "name": "Faiza",
        "education": "BS Computer Science",
        "interests": "Machine Learning, AI agents, LangGraph, automation",
        "skills": "Python, SQL, basic FastAPI, GitHub",
    },
    "Cyber Security Example": {
        "name": "Ali",
        "education": "BS Software Engineering",
        "interests": "Cyber security, ethical hacking, Linux, networking, malware analysis",
        "skills": "Linux basics, Python basics, networking fundamentals",
    },
    "Web Developer Example": {
        "name": "Sara",
        "education": "BS IT",
        "interests": "Websites, MERN stack, frontend and backend development",
        "skills": "HTML, CSS, JavaScript basics, Git",
    },
}

selected_example = st.selectbox("Quick demo input", list(examples.keys()))
example = examples[selected_example]

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Name", value=example["name"])
    education = st.text_input("Education", value=example["education"])
with col2:
    interests = st.text_area("Interests", value=example["interests"], height=120)
    skills = st.text_area("Current Skills", value=example["skills"], height=120)

thread_id = st.text_input("Memory thread_id", value=st.session_state.thread_id)

api_key_available = bool(os.getenv("GROQ_API_KEY"))
if not api_key_available:
    st.warning("Add your GROQ_API_KEY in the .env file before running the agent.")

if st.button("Generate Career Roadmap", type="primary"):
    if not all([name.strip(), education.strip(), interests.strip(), skills.strip()]):
        st.error("Please fill all fields first.")
    elif not api_key_available:
        st.error("GROQ_API_KEY missing. Create a .env file and add your API key.")
    else:
        with st.spinner("CareerCompass AI is analyzing profile, routing career path, researching, and improving the roadmap..."):
            result = run_career_agent(
                name=name,
                education=education,
                interests=interests,
                skills=skills,
                thread_id=thread_id,
            )

        st.success("Roadmap generated successfully!")

        m1, m2, m3 = st.columns(3)
        m1.metric("Recommended Career", result.get("career_path", "N/A"))
        m2.metric("Roadmap Quality", result.get("quality_score", "N/A"))
        m3.metric("Attempts", result.get("retry_count", "N/A"))

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Profile",
            "Skills",
            "Research Tool",
            "Roadmap",
            "Evaluation",
            "Final Summary",
        ])

        with tab1:
            st.subheader("Profile Summary")
            st.write(result.get("profile_summary", ""))
            st.subheader("Career Decision Reason")
            st.write(result.get("career_reason", ""))

        with tab2:
            st.subheader("Strengths and Missing Skills")
            for item in result.get("missing_skills", []):
                st.write(item)

        with tab3:
            st.subheader("Web Search Tool Output")
            st.write(result.get("research", ""))

        with tab4:
            st.subheader("12-Week Career Roadmap")
            st.markdown(result.get("roadmap", ""))

        with tab5:
            st.subheader("Roadmap Evaluation")
            st.write("**Feedback:**", result.get("feedback", ""))

        with tab6:
            st.subheader("Final Summary")
            st.write(result.get("final_summary", ""))

st.divider()
st.caption("Run command: streamlit run app.py")
