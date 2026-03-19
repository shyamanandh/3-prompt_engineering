# Component 03 — Prompt Engineering API

Part of the 15-component AI System Engineering journey.

## What this component covers

1. Zero Shot Prompting
2. Few Shot Prompting
3. Chain of Thought
4. Structured Output Prompting
5. Role Prompting
6. Negative Prompting
7. Prompt Templates
8. Context Window Management
9. Prompt Versioning
10. Prompt Injection Defense

## Tech Stack

- Python 3.13
- FastAPI
- Groq LLM (llama-3.3-70b-versatile)
- Uvicorn

## How to run

1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate.bat`
4. Install packages: `pip install -r requirements.txt`
5. Add your Groq API key to `.env` file: `GROQ_API_KEY=your_key`
6. Run server: `uvicorn app.main:app --reload`
7. Visit: `http://127.0.0.1:8000/docs`

## Previous Components

- Component 01 — FastAPI + Docker
- Component 02 — Groq LLM + Streaming