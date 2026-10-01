"""
test_phase7.py — summary_service unit tests (Google Gemini LLM)

Tests mock the Gemini SDK so no real API key or network is required.
"""
import os
from unittest.mock import patch, MagicMock
import summary_service


# ── helpers ──────────────────────────────────────────────────────────────────

SAMPLE_TRANSCRIPT = (
    "Today we discussed the water cycle. Water evaporates from oceans and lakes, "
    "rises as water vapor, condenses into clouds, and falls as precipitation. "
    "This cycle is essential for distributing fresh water across the planet. "
    "We also covered how deforestation disrupts the cycle by reducing evapotranspiration."
)

SAMPLE_SUMMARY = (
    "KEY POINTS:\n"
    "- Water evaporates from oceans and lakes and rises as vapor\n"
    "- Water vapor condenses into clouds and falls as precipitation\n"
    "- The cycle distributes fresh water globally\n"
    "- Deforestation disrupts the cycle by reducing evapotranspiration\n\n"
    "SUMMARY:\n"
    "The water cycle describes how water moves between Earth's surface and atmosphere "
    "through evaporation, condensation, and precipitation. Deforestation disrupts this "
    "essential process by reducing the evapotranspiration from vegetation."
)


def make_mock_response(text=None):
    """Build a fake GenerateContentResponse object."""
    mock_resp = MagicMock()
    mock_resp.text = text
    return mock_resp


# ── tests ─────────────────────────────────────────────────────────────────────

def test_summarize_success():
    """Happy path: Gemini returns a well-formed summary."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"), \
         patch("summary_service.genai.configure") as mock_configure, \
         patch("summary_service.genai.GenerativeModel") as mock_model_cls:

        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_model.generate_content.return_value = make_mock_response(text=SAMPLE_SUMMARY)

        result = summary_service.summarize(SAMPLE_TRANSCRIPT)

        assert result == SAMPLE_SUMMARY
        mock_configure.assert_called_once_with(api_key="test-key")
        mock_model.generate_content.assert_called_once()
        # Verify the transcript was included in the prompt
        call_args = mock_model.generate_content.call_args[0][0]
        assert SAMPLE_TRANSCRIPT.strip() in call_args
        print(f"test_summarize_success PASSED — summary length: {len(result)} chars")


def test_summarize_missing_api_key():
    """Missing GEMINI_API_KEY -> ValueError should be raised."""
    with patch("summary_service.GEMINI_API_KEY", None):
        raised = False
        try:
            summary_service.summarize(SAMPLE_TRANSCRIPT)
        except ValueError as e:
            raised = True
            print(f"test_summarize_missing_api_key PASSED — caught: {e}")
        assert raised, "Expected ValueError but none was raised"


def test_summarize_empty_transcript():
    """Empty transcript -> ValueError should be raised."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"):
        raised = False
        try:
            summary_service.summarize("")
        except ValueError as e:
            raised = True
            print(f"test_summarize_empty_transcript PASSED — caught: {e}")
        assert raised, "Expected ValueError but none was raised"


def test_summarize_whitespace_only_transcript():
    """Whitespace-only transcript -> ValueError should be raised."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"):
        raised = False
        try:
            summary_service.summarize("   \n\t  ")
        except ValueError as e:
            raised = True
            print(f"test_summarize_whitespace_only_transcript PASSED — caught: {e}")
        assert raised, "Expected ValueError but none was raised"


def test_summarize_api_exception():
    """Gemini SDK raises an exception -> RuntimeError should be raised."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"), \
         patch("summary_service.genai.configure"), \
         patch("summary_service.genai.GenerativeModel") as mock_model_cls:

        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("Connection refused")

        raised = False
        try:
            summary_service.summarize(SAMPLE_TRANSCRIPT)
        except RuntimeError as e:
            raised = True
            print(f"test_summarize_api_exception PASSED — caught: {e}")
        assert raised, "Expected RuntimeError but none was raised"


def test_summarize_empty_response():
    """Gemini returns empty text -> RuntimeError should be raised."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"), \
         patch("summary_service.genai.configure"), \
         patch("summary_service.genai.GenerativeModel") as mock_model_cls:

        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_model.generate_content.return_value = make_mock_response(text="")

        raised = False
        try:
            summary_service.summarize(SAMPLE_TRANSCRIPT)
        except RuntimeError as e:
            raised = True
            print(f"test_summarize_empty_response PASSED — caught: {e}")
        assert raised, "Expected RuntimeError but none was raised"


def test_summarize_prompt_contains_key_points_instruction():
    """Verify the prompt includes the KEY POINTS / SUMMARY structure instruction."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"), \
         patch("summary_service.genai.configure"), \
         patch("summary_service.genai.GenerativeModel") as mock_model_cls:

        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_model.generate_content.return_value = make_mock_response(text=SAMPLE_SUMMARY)

        summary_service.summarize(SAMPLE_TRANSCRIPT)

        prompt_sent = mock_model.generate_content.call_args[0][0]
        assert "KEY POINTS:" in prompt_sent
        assert "SUMMARY:" in prompt_sent
        print("test_summarize_prompt_contains_key_points_instruction PASSED")


def test_summarize_uses_configured_model():
    """Verify the model name from env var is passed to GenerativeModel."""
    with patch("summary_service.GEMINI_API_KEY", "test-key"), \
         patch("summary_service.GEMINI_MODEL", "gemini-1.5-pro"), \
         patch("summary_service.genai.configure"), \
         patch("summary_service.genai.GenerativeModel") as mock_model_cls:

        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_model.generate_content.return_value = make_mock_response(text=SAMPLE_SUMMARY)

        summary_service.summarize(SAMPLE_TRANSCRIPT)

        mock_model_cls.assert_called_once_with(model_name="gemini-1.5-pro")
        print("test_summarize_uses_configured_model PASSED")


if __name__ == "__main__":
    test_summarize_success()
    test_summarize_missing_api_key()
    test_summarize_empty_transcript()
    test_summarize_whitespace_only_transcript()
    test_summarize_api_exception()
    test_summarize_empty_response()
    test_summarize_prompt_contains_key_points_instruction()
    test_summarize_uses_configured_model()
    print("\nAll Phase 7 tests passed!")
