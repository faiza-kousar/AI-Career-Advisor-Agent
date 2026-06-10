"""
CareerCompass AI - LangGraph Career Advisor Agent
Workflow type: Conditional + Iterative

This module builds a LangGraph agent that:
1. Analyzes a student profile
2. Assesses missing skills
3. Classifies a suitable career path
4. Routes to a specialist career node
5. Uses a web search tool for latest roadmap context
6. Generates a roadmap
7. Evaluates roadmap quality with Pydantic structured output
8. Retries roadmap generation until quality is good or retry limit is reached
"""

from __future__ import annotations

import os
from typing import List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

load_dotenv()

def get_llm():
    """Get LLM instance with proper configuration."""
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

llm = get_llm()

CAREER_OPTIONS = [
    "AI Engineer",
    "Cyber Security",
    "Data Scientist",
    "Web Developer",
    "Cloud Engineer",
]

MAX_RETRIES = 3


# -----------------------------
# Pydantic Structured Outputs
# -----------------------------
class CareerDecision(BaseModel):
    career_path: Literal[
        "AI Engineer",
        "Cyber Security",
        "Data Scientist",
        "Web Developer",
        "Cloud Engineer",
    ] = Field(description="The single best career path for the student.")
    reason: str = Field(description="Short reason for choosing this career path.")


class RoadmapReview(BaseModel):
    score: int = Field(ge=1, le=10, description="Roadmap quality score from 1 to 10.")
    good: bool = Field(description="True if the roadmap is good enough for the student.")
    feedback: str = Field(description="Specific feedback to improve the roadmap.")


# -----------------------------
# TypedDict State Management
# total=False allows app/notebook to pass only the initial input fields.
# -----------------------------
class CareerState(TypedDict, total=False):
    name: str
    education: str
    interests: str
    skills: str
    profile_summary: str
    strengths: List[str]
    missing_skills: List[str]
    career_path: str
    career_reason: str
    specialist_advice: str
    research: str
    roadmap: str
    quality_score: int
    feedback: str
    retry_count: int
    final_summary: str




search_tool = DuckDuckGoSearchRun()


# -----------------------------
# Node 1: Profile Analyzer
# -----------------------------
def profile_analyzer_node(state: CareerState) -> CareerState:
    llm = get_llm()
    prompt = f"""
You are CareerCompass AI, a helpful career advisor for Pakistani university students.
Analyze the student profile in simple English.

Name: {state.get('name', '')}
Education: {state.get('education', '')}
Interests: {state.get('interests', '')}
Skills: {state.get('skills', '')}

Return a concise profile summary covering background, interests, skill level, and career direction.
"""
    response = llm.invoke(prompt)
    return {"profile_summary": response.content}


# -----------------------------
# Node 2: Skill Assessment
# -----------------------------
def skill_assessment_node(state: CareerState) -> CareerState:
    llm = get_llm()
    prompt = f"""
Student profile summary:
{state.get('profile_summary', '')}

Current skills:
{state.get('skills', '')}

Identify:
1. 3 strengths
2. 5 missing skills the student should learn next

Return the answer as clear bullet points.
"""
    response = llm.invoke(prompt)
    # We keep a readable string inside a list to satisfy the state field and simplify display.
    return {
        "strengths": [response.content],
        "missing_skills": [response.content],
    }


# -----------------------------
# Node 3: Career Classifier using Pydantic structured output
# -----------------------------
def career_classifier_node(state: CareerState) -> CareerState:
    llm = get_llm()
    structured_llm = llm.with_structured_output(CareerDecision)
    result = structured_llm.invoke(
        f"""
Choose exactly ONE best career path for this student.

Allowed options:
- AI Engineer
- Cyber Security
- Data Scientist
- Web Developer
- Cloud Engineer

Education: {state.get('education', '')}
Interests: {state.get('interests', '')}
Skills: {state.get('skills', '')}
Profile Summary: {state.get('profile_summary', '')}
Missing Skills: {state.get('missing_skills', [])}

Decision rule:
- If interests mention AI, ML, LLM, automation, choose AI Engineer.
- If interests mention hacking, security, malware, networking, choose Cyber Security.
- If interests mention data, analytics, statistics, choose Data Scientist.
- If interests mention websites, MERN, frontend, backend, choose Web Developer.
- If interests mention DevOps, AWS, cloud, servers, choose Cloud Engineer.
"""
    )
    return {
        "career_path": result.career_path,
        "career_reason": result.reason,
    }


# -----------------------------
# Specialist Career Nodes
# -----------------------------
def ai_engineer_node(state: CareerState) -> CareerState:
    return {
        "career_path": "AI Engineer",
        "specialist_advice": "Focus on Python, machine learning, LLM apps, LangChain/LangGraph, vector databases, APIs, and deployment.",
    }


def cybersecurity_node(state: CareerState) -> CareerState:
    return {
        "career_path": "Cyber Security",
        "specialist_advice": "Focus on networking, Linux, web security, OWASP Top 10, Python scripting, SIEM basics, and ethical lab practice.",
    }


def data_science_node(state: CareerState) -> CareerState:
    return {
        "career_path": "Data Scientist",
        "specialist_advice": "Focus on Python, SQL, statistics, pandas, visualization, machine learning, notebooks, and portfolio projects.",
    }


def web_developer_node(state: CareerState) -> CareerState:
    return {
        "career_path": "Web Developer",
        "specialist_advice": "Focus on HTML, CSS, JavaScript, React, Node.js, databases, REST APIs, authentication, and deployment.",
    }


def cloud_engineer_node(state: CareerState) -> CareerState:
    return {
        "career_path": "Cloud Engineer",
        "specialist_advice": "Focus on Linux, networking, AWS/Azure basics, Docker, CI/CD, Terraform, monitoring, and cloud projects.",
    }


# -----------------------------
# Tool Node: Web Research
# -----------------------------
def research_node(state: CareerState) -> CareerState:
    career = state.get("career_path", "technology")
    try:
        result = search_tool.invoke(f"latest {career} roadmap skills 2026 beginner to job ready")
    except Exception as exc:
        result = (
            "Web search tool was called but could not fetch live results. "
            f"Reason: {exc}. Continue using general career roadmap knowledge."
        )
    return {"research": result}


# -----------------------------
# Roadmap Generator
# -----------------------------
def roadmap_generator_node(state: CareerState) -> CareerState:
    llm = get_llm()
    retry_count = int(state.get("retry_count", 0)) + 1
    prompt = f"""
Create a practical 12-week career roadmap for this student.

Student Name: {state.get('name', '')}
Education: {state.get('education', '')}
Interests: {state.get('interests', '')}
Current Skills: {state.get('skills', '')}
Career Path: {state.get('career_path', '')}
Career Reason: {state.get('career_reason', '')}
Specialist Advice: {state.get('specialist_advice', '')}
Missing Skills: {state.get('missing_skills', [])}
Research Notes from Web Tool: {state.get('research', '')}
Previous Feedback if retrying: {state.get('feedback', '')}
Attempt Number: {retry_count}

Roadmap requirements:
- Use simple English.
- Include Roman Urdu explanation after important points.
- Divide into Week 1-2, Week 3-4, Week 5-8, Week 9-12.
- Include tools to learn, mini projects, portfolio tasks, and interview preparation.
- Include a daily routine for a student with 2-3 hours per day.
- Make it realistic for a beginner/intermediate student.
"""
    response = llm.invoke(prompt)
    return {
        "roadmap": response.content,
        "retry_count": retry_count,
    }


# -----------------------------
# Roadmap Evaluator with structured output
# -----------------------------
# -----------------------------
# Roadmap Evaluator with Pydantic Structured Output
# -----------------------------
def roadmap_evaluator_node(state: CareerState) -> CareerState:
    llm = get_llm()

    structured_llm = llm.with_structured_output(RoadmapReview)

    result = structured_llm.invoke(
        f"""
Evaluate this career roadmap strictly.

Career Path: {state.get('career_path', '')}
Student Skills: {state.get('skills', '')}

Roadmap:
{state.get('roadmap', '')}

Evaluation Rules:
- Score from 1 to 10
- Only give 9 or 10 if roadmap is excellent
- Check if roadmap includes:
  * Weekly learning plan
  * Practical projects
  * Portfolio building
  * Interview preparation
  * Realistic beginner progression
- Give constructive feedback if improvements are needed
"""
    )

    return {
        "quality_score": result.score,
        "feedback": result.feedback,
    }

# -----------------------------
# Final Summary Node
# -----------------------------
def final_summary_node(state: CareerState) -> CareerState:
    llm = get_llm()
    response = llm.invoke(
        f"""
Write a short final summary for the student.

Name: {state.get('name', '')}
Recommended Career: {state.get('career_path', '')}
Quality Score: {state.get('quality_score', '')}
Roadmap Feedback: {state.get('feedback', '')}

Include encouragement and the first 3 actions the student should take this week.
Use simple English with a little Roman Urdu.
"""
    )
    return {"final_summary": response.content}


# -----------------------------
# Routing Functions
# -----------------------------
def route_career(state: CareerState) -> str:
    career = state.get("career_path", "")
    if career == "AI Engineer":
        return "ai"
    if career == "Cyber Security":
        return "cyber"
    if career == "Data Scientist":
        return "data"
    if career == "Web Developer":
        return "web"
    return "cloud"


# -----------------------------
# Evaluation Routing
# -----------------------------
def evaluate_route(state: CareerState) -> str:
    score = int(state.get("quality_score", 0))
    retries = int(state.get("retry_count", 0))

    print(f"Score: {score}, Attempts: {retries}")

    # Require a stricter score to finish
    if score >= 9:
        return "final"

    # Stop after max retries
    if retries >= MAX_RETRIES:
        return "final"

    return "retry"


# -----------------------------
# Build and Compile Graph
# -----------------------------
def build_graph():
    graph = StateGraph(CareerState)

    graph.add_node("profile", profile_analyzer_node)
    graph.add_node("skill", skill_assessment_node)
    graph.add_node("career", career_classifier_node)
    graph.add_node("ai", ai_engineer_node)
    graph.add_node("cyber", cybersecurity_node)
    graph.add_node("data", data_science_node)
    graph.add_node("web", web_developer_node)
    graph.add_node("cloud", cloud_engineer_node)
    graph.add_node("research", research_node)
    graph.add_node("roadmap", roadmap_generator_node)
    graph.add_node("evaluate", roadmap_evaluator_node)
    graph.add_node("final", final_summary_node)

    graph.add_edge(START, "profile")
    graph.add_edge("profile", "skill")
    graph.add_edge("skill", "career")

    graph.add_conditional_edges(
        "career",
        route_career,
        {
            "ai": "ai",
            "cyber": "cyber",
            "data": "data",
            "web": "web",
            "cloud": "cloud",
        },
    )

    graph.add_edge("ai", "research")
    graph.add_edge("cyber", "research")
    graph.add_edge("data", "research")
    graph.add_edge("web", "research")
    graph.add_edge("cloud", "research")

    graph.add_edge("research", "roadmap")
    graph.add_edge("roadmap", "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        evaluate_route,
        {
            "final": "final",
            "retry": "roadmap",
        },
    )

    graph.add_edge("final", END)
    return graph


memory = MemorySaver()
career_agent = build_graph().compile(checkpointer=memory)


def run_career_agent(
    name: str,
    education: str,
    interests: str,
    skills: str,
    thread_id: str = "student_1",
) -> CareerState:
    """Convenience function used by Streamlit and notebook."""
    initial_state: CareerState = {
        "name": name,
        "education": education,
        "interests": interests,
        "skills": skills,
        "retry_count": 0,
    }
    config = {"configurable": {"thread_id": thread_id}}
    return career_agent.invoke(initial_state, config=config)
