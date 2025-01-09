import os
import unittest
from unittest import mock
from audio import text_to_speech_step
import pipeline
from util import gcs_utils


class TextToSpeechStepTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    output_dir = "tests/audio/generated/somevideoid"
    os.makedirs(output_dir, exist_ok=True)

  def setUp(self):
    super().setUp()
    self.context = pipeline.VideoGenerationContext(
        {
            "workdir": "tests/audio/generated",
            "gcp_project": "somegcpproject",
            "gcp_location": "us-central1",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/audio/generated",
            "multivoice": True,
        },
        request_params={},
        video_id="somevideoid",
    )

  @mock.patch("audio.text_to_speech_step.texttospeech.TextToSpeechClient")
  def test_generate_single_voice_creates_audio_file(
      self, mock_text_to_speech_client
  ):
    """Test that single-voice audio is generated and saved correctly."""
    step = text_to_speech_step.TextToSpeechStep(self.context)
    summary_text = "Hello world"
    mock_client = mock_text_to_speech_client.return_value
    mock_client.synthesize_speech.return_value.audio_content = (
        b"fake_audio_data"
    )
    with mock.patch("builtins.open", mock.mock_open()) as mocked_file:
      audio_path = step.generate_single_voice(summary_text)

    mocked_file.assert_called_once_with(
        "tests/audio/generated/somevideoid/2_readaloud.mp3", "wb"
    )
    mocked_file().write.assert_called_once_with(b"fake_audio_data")
    self.assertEqual(
        audio_path, "tests/audio/generated/somevideoid/2_readaloud.mp3"
    )

  @mock.patch("audio.text_to_speech_step.texttospeech.TextToSpeechClient")
  def test_generate_multivoice_audio_creates_audio_file(
      self, mock_text_to_speech_client
  ):
    """Test that multi-voice audio is generated and saved correctly."""
    step = text_to_speech_step.TextToSpeechStep(self.context)
    multivoice_transcript = {
        "narration": [
            {"name": "Anchor 1", "statement": "Hello"},
            {"name": "Anchor 2", "statement": "world"},
        ]
    }
    mock_client = mock_text_to_speech_client.return_value
    mock_client.synthesize_speech.return_value.audio_content = (
        b"fake_audio_data"
    )
    with mock.patch("builtins.open", mock.mock_open()) as mocked_file:
      audio_path = step.generate_multivoice_audio(multivoice_transcript)

    mocked_file.assert_called_once_with(
        "tests/audio/generated/somevideoid/2_readaloud.mp3", "wb"
    )
    mocked_file().write.assert_called_once_with(b"fake_audio_data")
    self.assertEqual(
        audio_path, "tests/audio/generated/somevideoid/2_readaloud.mp3"
    )


if __name__ == "__main__":
  unittest.main()
