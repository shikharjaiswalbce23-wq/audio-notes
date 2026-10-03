"""
summary_service.py — LLM Summarization via Google Gemini API

Responsible for:
  - Sending a transcript to the Gemini LLM
  - Receiving a structured, human-readable summary
  - Raising clear errors so the worker can set FAILED with a helpful message

Environment variables required:
  GEMINI_API_KEY   — Your Google AI Studio API key
                     Get one at: https://aistudio.google.com/app/apikey

Optional:
  GEMINI_MODEL     — Model name (default: gemini-1.5-flash)
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# ── Summarization prompt ──────────────────────────────────────────────────────
#
# Design decisions:
#   1. We ask for structured output (key points + summary paragraph) so the
#      frontend can display both sections clearly.
#   2. We tell the model the source is an audio transcript — this helps it
#      handle filler words and informal speech gracefully.
#   3. We explicitly ask it NOT to add information not in the transcript —
#      this prevents hallucinations.
#   4. Plain text output (no markdown) keeps frontend rendering simple.
#
SUMMARIZATION_PROMPT_TEMPLATE = """You are an expert note-taker. You have been given a transcript from an audio recording.

Your task is to produce a concise, structured summary. Follow these rules:
1. Only use information that is present in the transcript — do NOT add outside knowledge.
2. Ignore filler words (um, uh, like) and transcript artifacts.
3. Write in clear, professional English.
4. Output format must be exactly:

KEY POINTS:
- [First key point]
- [Second key point]
- [Add as many as needed, minimum 3]

SUMMARY:
[A 2-4 sentence paragraph capturing the main idea and important details.]

Transcript:
{transcript}"""


def summarize(transcript: str) -> str:
    """
    Send a transcript to the Gemini LLM and return a structured summary.

    Args:
        transcript: The full plain-text transcript from Gnan.ai ASR.

    Returns:
        A structured summary string in the format:
            KEY POINTS:
            - ...

            SUMMARY:
            ...

    Raises:
        ValueError:   If GEMINI_API_KEY is not configured or transcript is empty.
        RuntimeError: If the Gemini API call fails or returns an empty response.
    """
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a free key at https://aistudio.google.com/app/apikey"
        )

    if not transcript or not transcript.strip():
        raise ValueError("Cannot summarize an empty transcript.")

    # Configure the SDK with the API key
    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel(model_name=GEMINI_MODEL)

    prompt = SUMMARIZATION_PROMPT_TEMPLATE.format(transcript=transcript.strip())

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    # Validate the response
    if not response or not response.text:
        raise RuntimeError(
            "Gemini API returned an empty response. "
            "This may be due to content filtering or a transient error."
        )

    summary = response.text.strip()

    if not summary:
        raise RuntimeError("Gemini API returned a blank summary.")

    return summary
