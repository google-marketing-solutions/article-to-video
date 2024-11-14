import os
import unittest
from unittest import mock
import audio
from audio import subtitles_generation_step
import pipeline
from util.errors import GeminiError


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
            "gcp_project": "my_gcp_project",
            "gcp_location": "us_west",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/audio/generated",
        },
        request_params={},
        video_id="somevideoid",
    )

  @mock.patch.object(subtitles_generation_step.vertexai, "init")
  @mock.patch.object(subtitles_generation_step, "GenerativeModel")
  def test_invalid_srt_format_throws_error(self, mock_generative_model, _):
    """Test that GeminiError is raised when model response is invalid."""

    subtitles = (
        "This file is not valid.\n"
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "This is the first subtitle.\n"
    )

    mock_model = mock_generative_model()
    mock_model.generate_content.return_value.text = subtitles
    summary_text = "This file is not valid."
    audio_path = "audio_link_gcs"
    step = audio.subtitles_generation_step.SubtitlesGenerationStep(self.context)

    with self.assertRaises(GeminiError):
      step((audio_path, summary_text))

  @mock.patch.object(subtitles_generation_step.vertexai, "init")
  @mock.patch.object(subtitles_generation_step, "GenerativeModel")
  def test_srt_file_output_success(self, mock_generative_model, _):
    """Test that SRT file successfully written."""

    subtitles = (
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "This is the first subtitle.\n"
        "2\n"
        "00:00:20,000 --> 00:00:04,400\n"
        "This is the second subtitle."
    )

    mock_model = mock_generative_model()
    mock_model.generate_content.return_value.text = subtitles
    summary_text = "This is an example."
    audio_path = "audio_link_gcs"
    step = audio.subtitles_generation_step.SubtitlesGenerationStep(self.context)
    output_path = "tests/audio/generated/somevideoid/subtitles.srt"

    with mock.patch("builtins.open", mock.mock_open()) as mocked_file:
      srt_text = step((audio_path, summary_text))
      mocked_file.assert_any_call(output_path, "w")
      self.assertEqual(
          srt_text[1], "tests/audio/generated/somevideoid/subtitles.srt"
      )


if __name__ == "__main__":
  unittest.main()
