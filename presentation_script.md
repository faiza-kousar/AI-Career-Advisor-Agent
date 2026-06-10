# 5-Minute Presentation Script

## Member 1: 0:00 – 1:00 Problem & Idea
Assalam o Alaikum. Our project is CareerCompass AI, a career advisor agent for students. Many students know basic skills like Python, SQL, or web development, but they are confused about which career path to choose and what to learn next. CareerCompass AI analyzes education, interests, and skills, then recommends one career path and creates a 12-week roadmap.

## Member 2: 1:00 – 2:30 Architecture
Our workflow type is Conditional + Iterative. First, the profile analyzer summarizes the student profile. Then skill assessment identifies missing skills. Career classifier uses Pydantic structured output to select one career path. Conditional edges route the graph to AI Engineer, Cyber Security, Data Scientist, Web Developer, or Cloud Engineer. Then the research node uses DuckDuckGo web search. Roadmap generator creates a 12-week plan. Roadmap evaluator scores the plan. If score is less than 8, the graph loops back and regenerates the roadmap. MemorySaver stores the run using thread_id.

## Member 3: 2:30 – 4:30 Live Demo
Now we run the Streamlit app. First input uses AI interests like machine learning and LangGraph, so the agent routes to AI Engineer. Second input uses security interests like ethical hacking and networking, so it routes to Cyber Security. We show that the same graph gives different branches based on state. We also show quality score and retry count.

## Any Member: 4:30 – 5:00 Q/A
Challenges were controlling LLM output, preventing infinite loops, and handling web-search failure. Future work includes resume upload, LinkedIn integration, job market APIs, and personalized progress tracking.
