import os
import unittest
from unittest import mock
from audio import text_to_speech_step
import pipeline
import text
from util import gcs_utils


@mock.patch.object(gcs_utils, "upload_to_gcs", autospec=True)
class TextToSpeechStepTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    output_dir = "tests/audio/generated/somevideoid"
    os.makedirs(output_dir, exist_ok=True)

  def setUp(self):
    super().setUp()
    self.context = pipeline.VideoGenerationContext.from_request(
        {
            "workdir": "tests/audio/generated",
            "gcp_project": "somegcpproject",
            "gcp_location": "us-central1",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/audio/generated",
        },
        request_params={
            "article_content": "my article",
            "image_paths": [],
            "multivoice": True,
            "multitext": False,
        },
        video_id="somevideoid",
    )

  @mock.patch("audio.text_to_speech_step.texttospeech.TextToSpeechClient")
  def test_creates_audio_file(self, mock_text_to_speech_client, _):
    """Test that multi-speaker audio is generated with Gemini TTS."""
    # Added for Gemini TTS language support: Updated test to reflect Gemini
    # TTS multi-speaker synthesis
    step = text_to_speech_step.TextToSpeechStep(self.context)
    mock_client = mock_text_to_speech_client.return_value
    mock_client.synthesize_speech.return_value.audio_content = (
        b"fake_audio_data"
    )

    mock_open = mock.mock_open()
    with mock.patch("builtins.open", mock_open) as mocked_file:
      # Added for Gemini TTS language support: Create a script with
      # speakers for Gemini TTS multi-speaker
      script = text.VoiceoverScript(
          language="en-US",
          default_voice="Kore",
          speakers=[
              text.VoiceoverSpeaker(persona="Anchor 1", voice="Kore"),
              text.VoiceoverSpeaker(persona="Anchor 2", voice="Charon"),
          ],
          statements=[
              text.VoiceoverStatement(
                  voice="Kore", text="Hello from speaker 1"
              ),
              text.VoiceoverStatement(
                  voice="Charon", text="Hello from speaker 2"
              ),
          ],
          text="Hello from speaker 1 Hello from speaker 2",
      )
      step.process(script)

    mock_open.assert_called_once_with(
        "tests/audio/generated/somevideoid/2_readaloud.wav", "wb"
    )
    mocked_file().write.assert_called_once_with(b"fake_audio_data")


if __name__ == "__main__":
  unittest.main()
