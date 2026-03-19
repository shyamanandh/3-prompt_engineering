# app/services/llm.py

import os
# os module lets us read environment variables like GROQ_API_KEY

from groq import Groq
# Groq is the official SDK we installed via pip

from dotenv import load_dotenv
# load_dotenv reads our .env file and loads the variables into the environment

# Load the .env file so GROQ_API_KEY becomes available
load_dotenv()

# Create one Groq client instance that the whole app will use.
# os.environ.get("GROQ_API_KEY") reads the key from .env file.
# We create it once here at the top — not inside every function.
# This is more efficient and follows the singleton pattern.
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# This is the model we will use for all our prompts.
# Storing it as a constant means we only change it in one place
# if we ever want to switch models.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Maximum tokens the model can return in its response.
MAX_TOKENS = 1024


def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    # This function takes a ready prompt string and sends it to Groq.
    # It returns the model's response as a plain string.

    # prompt: str → the complete prompt we built using our templates
    # model: str → which Groq model to use, defaults to DEFAULT_MODEL
    # -> str → this function always returns a string

    # We wrap everything in try/except so errors are handled cleanly
    # instead of crashing the whole application
    try:
        # Send the prompt to Groq
        # messages is a list because LLMs expect a conversation format
        # role "user" means this is the human side of the conversation
        # content is the actual prompt text
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=MAX_TOKENS,
        )

        # Extract just the text from the response object
        # response.choices → list of possible responses (we always use first one)
        # .message.content → the actual text the model generated
        return response.choices[0].message.content

    except Exception as e:
        # If anything goes wrong, return a clear error message
        # instead of crashing the app
        raise RuntimeError(f"LLM call failed: {str(e)}")


def call_llm_with_system(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL
) -> str:
    # This function is for role prompting specifically.
    # It separates the system prompt (who the model is)
    # from the user message (what the user is asking).
    # This is the proper way to do role prompting.

    # system_prompt: str → defines the model's role and behavior
    # user_message: str → the actual user question or task
    # model: str → which model to use

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    # role "system" sets the model's identity and rules
                    # This is separate from the user message
                    "role": "system",
                    "content": system_prompt
                },
                {
                    # role "user" is the actual question or task
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=MAX_TOKENS,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise RuntimeError(f"LLM call failed: {str(e)}")


def count_tokens(text: str) -> int:
    # A simple token estimator for context window management.
    # Real tokenizers are complex, but this estimate is good enough
    # for basic context window management.

    # Rule of thumb: 1 token ≈ 4 characters in English text
    # We divide character count by 4 to estimate token count
    return len(text) // 4


def is_within_context_limit(text: str, limit: int = 7000) -> bool:
    # Checks if a prompt is within safe token limits.
    # We use 7000 as the limit (not 8192) to leave room
    # for the model's response tokens.

    # limit: int → maximum allowed tokens, default 7000
    # returns True if safe, False if too long

    estimated_tokens = count_tokens(text)
    return estimated_tokens <= limit


def trim_history(history: str, max_tokens: int = 3000) -> str:
    # This function trims conversation history if it gets too long.
    # We keep only the most recent part of the history
    # that fits within our token budget.

    # history: str → the full conversation history string
    # max_tokens: int → maximum tokens allowed for history

    # Calculate maximum characters based on token limit
    # 1 token ≈ 4 characters, so max chars = max_tokens * 4
    max_chars = max_tokens * 4

    # If history is within limit, return as is
    if len(history) <= max_chars:
        return history

    # If too long, keep only the most recent part
    # [-max_chars:] means take the last max_chars characters
    trimmed = history[-max_chars:]

    # Add a note so the model knows history was trimmed
    return f"[Earlier history trimmed]\n{trimmed}"