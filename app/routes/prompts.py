# app/routes/prompts.py

from fastapi import APIRouter, HTTPException
# APIRouter → creates a router to group all our endpoints
# HTTPException → used to return proper error responses

from pydantic import BaseModel
# BaseModel → used to define the shape of request body data
# Pydantic validates incoming data automatically

from app.prompts.templates import get_prompt, list_templates
# get_prompt → builds a ready prompt from a template
# list_templates → returns list of all available templates

from app.services.llm import (
    call_llm,
    call_llm_with_system,
    count_tokens,
    is_within_context_limit,
    trim_history
)
# Importing all functions we need from our LLM service

from app.middleware.injection import run_all_checks
# run_all_checks → runs all injection defense checks on user input

# Create the router instance
# All endpoints in this file are part of this router
router = APIRouter()


# ── REQUEST MODELS ────────────────────────────────────────────
# These classes define what data each endpoint expects.
# Pydantic automatically validates incoming JSON against these.

class TextInput(BaseModel):
    # Used by endpoints that need a simple text input
    text: str

class QuestionInput(BaseModel):
    # Used by endpoints that need a question
    question: str

class TaskInput(BaseModel):
    # Used by role prompting endpoint
    task: str

class AnalysisInput(BaseModel):
    # Used by the reusable template endpoint
    role: str
    domain: str
    input: str

class ConversationInput(BaseModel):
    # Used by context window management endpoint
    history: str
    user_message: str

class SafeInput(BaseModel):
    # Used by injection defense endpoint
    user_input: str


# ── 1. LIST ALL TEMPLATES ─────────────────────────────────────
@router.get("/templates")
def get_all_templates():
    # Returns all available prompt template names
    # Useful to see what is available without reading the code
    return {
        "available_templates": list_templates(),
        "total": len(list_templates())
    }


# ── 2. ZERO SHOT ──────────────────────────────────────────────
@router.post("/zero-shot")
def zero_shot(data: TextInput):
    # Demonstrates zero shot prompting
    # No examples — just a clear instruction

    # Step 1 — Run injection checks on user input
    safety = run_all_checks(data.text)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    # Step 2 — Build the prompt using template v1
    prompt = get_prompt("zero_shot_v1", text=safety["cleaned_input"])

    # Step 3 — Send to Groq and get response
    response = call_llm(prompt)

    # Step 4 — Return result with metadata
    return {
        "technique": "Zero Shot Prompting",
        "version": "v1",
        "input": data.text,
        "prompt_sent": prompt,
        "response": response
    }


# ── 3. FEW SHOT ───────────────────────────────────────────────
@router.post("/few-shot")
def few_shot(data: TextInput):
    # Demonstrates few shot prompting
    # 3 examples shown before the actual question

    safety = run_all_checks(data.text)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    prompt = get_prompt("few_shot_v1", text=safety["cleaned_input"])
    response = call_llm(prompt)

    return {
        "technique": "Few Shot Prompting",
        "version": "v1",
        "input": data.text,
        "prompt_sent": prompt,
        "response": response
    }


# ── 4. CHAIN OF THOUGHT ───────────────────────────────────────
@router.post("/chain-of-thought")
def chain_of_thought(data: QuestionInput):
    # Demonstrates chain of thought prompting
    # Forces model to think step by step before answering

    safety = run_all_checks(data.question)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    prompt = get_prompt(
        "chain_of_thought_v1",
        question=safety["cleaned_input"]
    )
    response = call_llm(prompt)

    return {
        "technique": "Chain of Thought",
        "version": "v1",
        "input": data.question,
        "prompt_sent": prompt,
        "response": response
    }


# ── 5. STRUCTURED OUTPUT ──────────────────────────────────────
@router.post("/structured-output")
def structured_output(data: TextInput):
    # Demonstrates structured output prompting
    # Model returns JSON that our code can parse

    safety = run_all_checks(data.text)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    prompt = get_prompt(
        "structured_output_v1",
        text=safety["cleaned_input"]
    )
    response = call_llm(prompt)

    # Try to parse the response as JSON
    # If model followed instructions, it should be valid JSON
    import json
    try:
        parsed = json.loads(response)
        return {
            "technique": "Structured Output Prompting",
            "version": "v1",
            "input": data.text,
            "prompt_sent": prompt,
            "response_raw": response,
            "response_parsed": parsed,
            "parsing_success": True
        }
    except json.JSONDecodeError:
        # If parsing fails, return raw response with a flag
        return {
            "technique": "Structured Output Prompting",
            "version": "v1",
            "input": data.text,
            "prompt_sent": prompt,
            "response_raw": response,
            "response_parsed": None,
            "parsing_success": False
        }


# ── 6. ROLE PROMPTING ─────────────────────────────────────────
@router.post("/role-prompt")
def role_prompt(data: TaskInput):
    # Demonstrates role prompting
    # System prompt sets the model identity
    # User message is the actual task

    safety = run_all_checks(data.task)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    # For role prompting we use call_llm_with_system
    # which properly separates system and user messages
    system = """You are a senior B2B SaaS sales strategist with 15 years
of experience in Go-To-Market strategy. You are direct,
data-driven, and avoid fluff."""

    response = call_llm_with_system(
        system_prompt=system,
        user_message=safety["cleaned_input"]
    )

    return {
        "technique": "Role Prompting",
        "version": "v1",
        "system_prompt": system,
        "input": data.task,
        "response": response
    }


# ── 7. NEGATIVE PROMPTING ─────────────────────────────────────
@router.post("/negative-prompt")
def negative_prompt(data: QuestionInput):
    # Demonstrates negative prompting
    # Explicitly tells model what NOT to do

    safety = run_all_checks(data.question)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    prompt = get_prompt(
        "negative_prompt_v1",
        question=safety["cleaned_input"]
    )
    response = call_llm(prompt)

    return {
        "technique": "Negative Prompting",
        "version": "v1",
        "input": data.question,
        "prompt_sent": prompt,
        "response": response
    }


# ── 8. REUSABLE TEMPLATE ──────────────────────────────────────
@router.post("/template-demo")
def template_demo(data: AnalysisInput):
    # Demonstrates prompt template reusability
    # Same template structure, different role and domain

    safety = run_all_checks(data.input)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    prompt = get_prompt(
        "reusable_analysis_v1",
        role=data.role,
        domain=data.domain,
        input=safety["cleaned_input"]
    )
    response = call_llm(prompt)

    return {
        "technique": "Prompt Templates",
        "version": "v1",
        "role_used": data.role,
        "domain_used": data.domain,
        "input": data.input,
        "prompt_sent": prompt,
        "response": response
    }


# ── 9. CONTEXT WINDOW MANAGEMENT ─────────────────────────────
@router.post("/context-managed")
def context_managed(data: ConversationInput):
    # Demonstrates context window management
    # Trims history if it gets too long before sending to LLM

    safety = run_all_checks(data.user_message)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    # Trim history if it exceeds token budget
    trimmed_history = trim_history(data.history)

    # Build the prompt with trimmed history
    prompt = get_prompt(
        "context_managed_v1",
        history=trimmed_history,
        user_message=safety["cleaned_input"]
    )

    # Check if final prompt is within context limit
    within_limit = is_within_context_limit(prompt)
    token_estimate = count_tokens(prompt)

    if not within_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt too long even after trimming. "
                   f"Estimated tokens: {token_estimate}"
        )

    response = call_llm(prompt)

    return {
        "technique": "Context Window Management",
        "version": "v1",
        "history_trimmed": trimmed_history != data.history,
        "estimated_tokens": token_estimate,
        "within_limit": within_limit,
        "response": response
    }


# ── 10. PROMPT VERSIONING ─────────────────────────────────────
@router.post("/version-compare")
def version_compare(data: TextInput):
    # Demonstrates prompt versioning
    # Runs the same input through v1 and v2 of zero shot prompt
    # So you can compare how version changes affect output

    safety = run_all_checks(data.text)
    if not safety["is_safe"]:
        raise HTTPException(status_code=400, detail=safety["reason"])

    # Run through version 1
    prompt_v1 = get_prompt("zero_shot_v1", text=safety["cleaned_input"])
    response_v1 = call_llm(prompt_v1)

    # Run through version 2
    prompt_v2 = get_prompt("zero_shot_v2", text=safety["cleaned_input"])
    response_v2 = call_llm(prompt_v2)

    return {
        "technique": "Prompt Versioning",
        "input": data.text,
        "v1": {
            "prompt_sent": prompt_v1,
            "response": response_v1
        },
        "v2": {
            "prompt_sent": prompt_v2,
            "response": response_v2
        },
        "comparison_note": "v2 adds role + stricter rules to improve consistency"
    }


# ── 11. INJECTION DEFENSE ─────────────────────────────────────
@router.post("/injection-safe")
def injection_safe(data: SafeInput):
    # Demonstrates injection defense
    # Shows what happens when safe vs malicious input is sent

    # Run all security checks
    safety = run_all_checks(data.user_input)

    # If unsafe — block it and explain why
    if not safety["is_safe"]:
        return {
            "technique": "Prompt Injection Defense",
            "input": data.user_input,
            "blocked": True,
            "reason": safety["reason"],
            "response": None,
            "message": "Request blocked by injection defense middleware"
        }

    # If safe — send to hardened prompt
    prompt = get_prompt(
        "injection_safe_v1",
        user_input=safety["cleaned_input"]
    )
    response = call_llm(prompt)

    return {
        "technique": "Prompt Injection Defense",
        "input": data.user_input,
        "blocked": False,
        "reason": None,
        "response": response,
        "message": "Input passed all security checks"
    }