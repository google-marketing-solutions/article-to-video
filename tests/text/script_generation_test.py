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

  def test_generate_prompts_llm_correctly(self):
    mock_llm = mock.MagicMock(spec=genai.GenerativeModel)
    mock_llm.generate_content.return_value.text = _MULTI_VOICE_SCRIPT_JSON
    script_generator = text.ScriptGenerator(
        speakers=2, language="en-US", llm=mock_llm
    )

    script_generator.generate("source_text")

    mock_llm.generate_content.assert_called_once_with(
        "Take this article and give me a script of news anchors narrating the"
        " main\npoints in the article in the form of a news flash. The"
        " speaker(s) should\nbriefly introduce the topic before diving in;"
        " however, they shouldn't\nintroduce themselves, or say things like"
        " welcome back, or now to story, or\nwe are taking you to... as the"
        " output of this will be consumed\nindependently in a news page. If"
        " there are multiple speakers, one person\nshould be the main anchor"
        " who gives the main points, while the other\nanchor makes"
        " complementary points. It should not be a dialog, rather,"
        " the\nspeaker(s) should both should aim to convey the same news"
        " content. If\nthere are multiple speakers they should take turns when"
        " talking and the\nswitch over should be very natural while sounding"
        " professional. Add some\nenthusiasm but maintain"
        " professionalism.\n\nOutput:\n- Identify the speaker(s). For each"
        " speaker, describe their persona, and\nchoose a voice.\n- Write the"
        " script. For each statement, identify the speaker by their\nvoice and"
        " write the statement in a way befitting of their assigned\npersona.\n-"
        " Include the complete, combined, transcipt of the narration."
        " Each\nspeaker's turn should start a new paragraph.\n- Generate the"
        " script in the language: en-US.\n\nAdditional instructions:\n- Don't"
        " add quotes or slashes within the output.\n\nThis is the"
        " article:\nsource_text\n",
        generation_config=mock.ANY,
    )


if __name__ == "__main__":
  unittest.main()
