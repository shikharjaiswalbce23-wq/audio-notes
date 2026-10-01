import os
import requests
from dotenv import load_dotenv

load_dotenv()

GNANI_API_KEY = os.getenv("GNANI_API_KEY")
GNANI_API_URL = os.getenv("GNANI_API_URL", "https://api.vachana.ai/stt/v3")
GNANI_LANGUAGE_CODE = os.getenv("GNANI_LANGUAGE_CODE", "en-IN")


def transcribe(audio_path: str, language_code: str = None, format: str = "transcribe") -> str:
    """
    Send an audio file to the Gnani.ai (Vachana) STT REST API and return
    the transcript text.

    API reference: https://docs.gnani.ai/api/STT/speech-to-text

    Args:
        audio_path:     Absolute path to the local audio file to transcribe.
        language_code:  BCP-47 code, e.g. "en-IN", "hi-IN". Falls back to
                        the GNANI_LANGUAGE_CODE env var (default "en-IN").
        format:         "verbatim" (raw spoken form) or "transcribe" (enables
                        Inverse Text Normalization — ITN). Defaults to
                        "transcribe" for cleaner output.

    Returns:
        The transcript as a plain string.

    Raises:
        ValueError:     If GNANI_API_KEY is not configured.
        RuntimeError:   If the API call fails or returns a non-200 response.
    """
    if not GNANI_API_KEY:
        raise ValueError("GNANI_API_KEY environment variable is not set.")

    lang = language_code or GNANI_LANGUAGE_CODE

    with open(audio_path, "rb") as f:
        filename = os.path.basename(audio_path)
        files = {"audio_file": (filename, f)}
        headers = {"X-API-Key-ID": GNANI_API_KEY}
        data = {
            "language_code": lang,
            "format": format,
        }

        response = requests.post(
            GNANI_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=300,  # 5-minute timeout for long audio
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Gnani.ai STT API error {response.status_code}: {response.text}"
        )

    body = response.json()

    # Expected response: { "success": true, "transcript": "...", ... }
    if not body.get("success"):
        error_info = body.get("error", {})
        raise RuntimeError(
            f"Gnani.ai STT API returned failure: {error_info.get('message', body)}"
        )

    transcript = body.get("transcript")
    if transcript is None:
        raise RuntimeError(
            f"Gnani.ai STT API returned unexpected response format: {body}"
        )

    return transcript
