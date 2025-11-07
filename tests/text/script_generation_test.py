import unittest
from unittest import mock
import text
from vertexai import generative_models as genai

# Added for Gemini TTS language support: Updated to use Gemini TTS voice names (Kore, Charon)
# instead of legacy Cloud TTS voices (en-US-Studio-O, en-US-Studio-Q)
_MULTI_VOICE_SCRIPT_JSON = """
{
  "language": "en-US",
  "default_voice": "Kore",
  "speakers": [
    {
    "persona": "Lead Anchor",
    "voice": "Kore"
    },
    {
    "persona": "Second Anchor",
    "voice": "Charon"
    }
  ],
  "statements": [
    {
    "voice": "Kore",
    "text": "first statement"
    },
    {
    "voice": "Charon",
    "text": "second statement"
    }
  ],
  "text": "first statement second statement"
}
"""

# Added for Gemini TTS language support: Updated to use Gemini TTS voice names
_MULTI_VOICE_SCRIPT_WITH_INVALID_VOICE_JSON = """
{
  "language": "en-US",
  "default_voice": "Kore",
  "speakers": [
    {
    "persona": "Lead Anchor",
    "voice": "Kore"
    },
    {
    "persona": "Second Anchor",
    "voice": "Charon"
    }
  ],
  "statements": [
    {
    "voice": "Kore",
    "text": "first statement"
    },
    {
    "voice": "invalid-voice-code",
    "text": "second statement with invalid voice"
    }
  ],
  "text": "first statement second statement with invalid voice"
}
"""


class ScriptGenerationTest(unittest.TestCase):

  def test_generate_returns_dataclss(self):
    mock_llm = mock.MagicMock(spec=genai.GenerativeModel)
    mock_llm.generate_content.return_value.text = _MULTI_VOICE_SCRIPT_JSON
    script_generator = text.ScriptGenerator(
        speakers=2, language="en-US", llm=mock_llm
    )

    script = script_generator.generate("source_text")

    # Added for Gemini TTS language support: Updated expected voices to
    # Gemini TTS names
    self.assertEqual(
        script,
        text.VoiceoverScript(
            language="en-US",
            default_voice="Kore",
            speakers=[
                text.VoiceoverSpeaker(persona="Lead Anchor", voice="Kore"),
                text.VoiceoverSpeaker(persona="Second Anchor", voice="Charon"),
            ],
            statements=[
                text.VoiceoverStatement(voice="Kore", text="first statement"),
                text.VoiceoverStatement(
                    voice="Charon", text="second statement"
                ),
            ],
            text="first statement second statement",
        ),
    )

  def test_generate_corrects_invalid_voice_to_default(self):
    mock_llm = mock.MagicMock(spec=genai.GenerativeModel)
    mock_llm.generate_content.return_value.text = (
        _MULTI_VOICE_SCRIPT_WITH_INVALID_VOICE_JSON
    )
    script_generator = text.ScriptGenerator(
        speakers=2, language="en-US", llm=mock_llm
    )

    script = script_generator.generate("source_text")

    # Added for Gemini TTS language support: Updated expected voices to
    # Gemini TTS names
    self.assertEqual(
        script,
        text.VoiceoverScript(
            language="en-US",
            default_voice="Kore",
            speakers=[
                text.VoiceoverSpeaker(persona="Lead Anchor", voice="Kore"),
                text.VoiceoverSpeaker(persona="Second Anchor", voice="Charon"),
            ],
            statements=[
                text.VoiceoverStatement(voice="Kore", text="first statement"),
                text.VoiceoverStatement(  # Voice should be corrected to default
                    voice="Kore",
                    text="second statement with invalid voice",
                ),
            ],
            text="first statement second statement with invalid voice",
        ),
    )

  def test_generate_prompts_llm_correctly(self):
    mock_llm = mock.MagicMock(spec=genai.GenerativeModel)
    mock_llm.generate_content.return_value.text = _MULTI_VOICE_SCRIPT_JSON
    script_generator = text.ScriptGenerator(
        speakers=2, language="en-US", llm=mock_llm
    )

    script_generator.generate("source_text")

    # Added for Gemini TTS language support: Updated assertion to use ANY matcher since voice list now includes
    # all Gemini voices (Kore, Charon, Aoede, Puck, etc.) instead of just 2 legacy voices
    # The exact prompt will vary but structure remains the same
    call_args = mock_llm.generate_content.call_args
    self.assertIn("news anchors narrating", call_args[0][0])
    self.assertIn("Kore", call_args[0][0])
    self.assertIn("Charon", call_args[0][0])
    self.assertIn("source_text", call_args[0][0])


if __name__ == "__main__":
  unittest.main()
