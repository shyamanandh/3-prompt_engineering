# app/middleware/injection.py

import re
# re is Python's built-in regular expressions module
# We use it to scan text for suspicious patterns

# This is our list of known injection attack patterns.
# Each item is a pattern we look for in user input.
# If any pattern matches, we block the request.
INJECTION_PATTERNS = [
    # Attempts to override instructions
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",

    # Attempts to change the model's role or identity
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a\s+)?different",
    r"pretend\s+you\s+are",
    r"your\s+new\s+role\s+is",

    # Attempts to reveal system prompts
    r"reveal\s+your\s+(system\s+)?prompt",
    r"show\s+me\s+your\s+(system\s+)?prompt",
    r"what\s+are\s+your\s+instructions",
    r"repeat\s+your\s+instructions",

    # Attempts to bypass rules
    r"ignore\s+your\s+rules",
    r"bypass\s+your\s+(rules|restrictions|guidelines)",
    r"override\s+your\s+(rules|restrictions|guidelines)",

    # DAN and jailbreak attempts
    r"do\s+anything\s+now",
    r"jailbreak",
    r"dan\s+mode",
]


def detect_injection(user_input: str) -> dict:
    # This function scans user input for injection patterns.
    # It returns a dictionary with:
    # - is_safe: True if input is clean, False if suspicious
    # - reason: what pattern was detected (if any)
    # - cleaned_input: the original input (we log but do not modify)

    # Convert to lowercase for case-insensitive matching
    # Someone typing "IGNORE ALL INSTRUCTIONS" should still be caught
    input_lower = user_input.lower()

    # Loop through every pattern in our list
    for pattern in INJECTION_PATTERNS:
        # re.search looks for the pattern anywhere in the text
        # If it finds a match, the input is suspicious
        if re.search(pattern, input_lower):
            return {
                "is_safe": False,
                "reason": f"Potential injection detected: pattern '{pattern}' matched",
                "cleaned_input": user_input
            }

    # If no patterns matched, the input is safe
    return {
        "is_safe": True,
        "reason": None,
        "cleaned_input": user_input
    }


def validate_input_length(user_input: str, max_length: int = 2000) -> dict:
    # This function checks if user input is within acceptable length.
    # Very long inputs can be used to overwhelm the context window
    # or hide injection attacks inside walls of text.

    # max_length: int → maximum characters allowed, default 2000

    if len(user_input) > max_length:
        return {
            "is_valid": False,
            "reason": f"Input too long. Maximum {max_length} characters allowed. "
                     f"You sent {len(user_input)} characters."
        }

    # Empty input is also invalid
    if len(user_input.strip()) == 0:
        return {
            "is_valid": False,
            "reason": "Input cannot be empty."
        }

    return {
        "is_valid": True,
        "reason": None
    }


def sanitize_input(user_input: str) -> str:
    # This function does basic cleaning of user input.
    # It does not remove content — just strips extra whitespace
    # and removes null bytes that could cause issues.

    # Strip leading and trailing whitespace
    cleaned = user_input.strip()

    # Remove null bytes — these can sometimes be used in attacks
    # \x00 is the null byte character
    cleaned = cleaned.replace("\x00", "")

    return cleaned


def run_all_checks(user_input: str) -> dict:
    # This is the main function your routes will call.
    # It runs ALL checks in the correct order and returns
    # one final result dictionary.

    # Step 1 — Sanitize first (clean the input)
    cleaned = sanitize_input(user_input)

    # Step 2 — Check length (reject if too long or empty)
    length_check = validate_input_length(cleaned)
    if not length_check["is_valid"]:
        return {
            "is_safe": False,
            "reason": length_check["reason"],
            "cleaned_input": cleaned
        }

    # Step 3 — Check for injection patterns
    injection_check = detect_injection(cleaned)
    if not injection_check["is_safe"]:
        return {
            "is_safe": False,
            "reason": injection_check["reason"],
            "cleaned_input": cleaned
        }

    # All checks passed — input is safe to send to LLM
    return {
        "is_safe": True,
        "reason": None,
        "cleaned_input": cleaned
    }