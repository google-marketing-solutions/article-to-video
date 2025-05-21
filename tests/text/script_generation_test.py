import unittest
from unittest import mock
import text
from vertexai import generative_models as genai

_MULTI_VOICE_SCRIPT_JSON = """
{
  "language": "en-US",
  "default_voice": "en-US-Studio-O",
  "speakers": [
    {
    "persona": "Lead Anchor",
    "voice": "en-US-Studio-O"
    },
    {
    "persona": "Second Anchor",
    "voice": "en-US-Studio-Q"
    }
  ],
  "statements": [
    {
    "voice": "en-US-Studio-O",
    "text": "first statement"
    },
    {
    "voice": "en-US-Studio-Q",
    "text": "second statement"
    }
  ],
  "text": "first statement second statement"
}
"""

_MULTI_VOICE_SCRIPT_WITH_INVALID_VOICE_JSON = """
{
  "language": "en-US",
  "default_voice": "en-US-Studio-O",
  "speakers": [
    {
    "persona": "Lead Anchor",
    "voice": "en-US-Studio-O"
    },
    {
    "persona": "Second Anchor",
    "voice": "en-US-Studio-Q"
    }
  ],
  "statements": [
    {
    "voice": "en-US-Studio-O",
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

    self.assertEqual(
        script,
        text.VoiceoverScript(
            language="en-US",
            default_voice="en-US-Studio-O",
            speakers=[
                text.VoiceoverSpeaker(
                    persona="Lead Anchor", voice="en-US-Studio-O"
                ),
                text.VoiceoverSpeaker(
                    persona="Second Anchor", voice="en-US-Studio-Q"
                ),
            ],
            statements=[
                text.VoiceoverStatement(
                    voice="en-US-Studio-O", text="first statement"
                ),
                text.VoiceoverStatement(
                    voice="en-US-Studio-Q", text="second statement"
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

    self.assertEqual(
        script,
        text.VoiceoverScript(
            language="en-US",
            default_voice="en-US-Studio-O",
            speakers=[
                text.VoiceoverSpeaker(
                    persona="Lead Anchor", voice="en-US-Studio-O"
                ),
                text.VoiceoverSpeaker(
                    persona="Second Anchor", voice="en-US-Studio-Q"
                ),
            ],
            statements=[
                text.VoiceoverStatement(
                    voice="en-US-Studio-O", text="first statement"
                ),
                text.VoiceoverStatement(  # Voice should be corrected to default
                    voice="en-US-Studio-O",
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

    mock_llm.generate_content.assert_called_once_with(
        "Take this article and give me a script of news anchors narrating"
        " the\nmain points in this article in the form of a news flash.\nThe"
        " speaker(s) should briefly introduce the topic(s) in less than"
        " 15\nseconds before diving in; however, they shouldn't introduce"
        " themselves,\nor say things like welcome back, or now to story, or we"
        " are taking\nyou to... as the output of this will be consumed"
        " independently in a\nnews page. Also don't make mention to a time of"
        " day (like 'good evening'\nor 'good morning' If there are multiple"
        " speakers,\none person should be the main anchor who gives the\nmain"
        " points, while the other anchor makes complementary points.\nIt should"
        " not be a dialog, rather, the speaker(s) should both should\naim to"
        " convey the same news content. If there are multiple speakers\nthey"
        " should take turns when talking and the switch over should be\nvery"
        " natural while sounding professional. Add some enthusiasm\nbut"
        " maintain professionalism.\n\nOutput:\n- Identify the speaker(s). For"
        " each speaker, describe their persona, and\nchoose a voice. Valid"
        " voices are: en-US-Studio-O, en-US-Studio-Q.\n- Write the script. For"
        " each statement, identify the speaker by their\nvoice and write the"
        " statement in a way befitting of their assigned\npersona.\n- Include"
        " the complete, combined, transcipt of the narration. Each\nspeaker's"
        " turn should start a new paragraph.\n- Generate the script in the"
        " language: en-US.\n\nAdditional instructions:\n- Don't add quotes or"
        " slashes within the output.\n\n\nThis is the article:\nsource_text\n",
        generation_config=mock.ANY,
    )


if __name__ == "__main__":
  unittest.main()
