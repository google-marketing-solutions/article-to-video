import os
import unittest
from unittest import mock
import audio
from audio import subtitles_generation_step
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
            "gcp_project": "my_gcp_project",
            "gcp_location": "us_west",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/audio/generated",
        },
        request_params={},
        video_id="testvideoid",
    )

  def test_remove_end_punctuation_success(self):
    input_string = "'off-white'."
    expected = "off-white"
    self.assertEqual(
        subtitles_generation_step.SubtitlesGenerationStep.remove_end_punctuation(
            input_string
        ),
        expected,
    )


def test_get_similarity_score(self):
  word1 = "property's"
  word2 = "properties"
  word3 = "property"
  self.assertEqual(
      subtitles_generation_step.SubtitlesGenerationStep.get_similarity_score(
          word1, word2
      ),
      6 / 9,
  )
  self.assertEqual(
      subtitles_generation_step.SubtitlesGenerationStep.get_similarity_score(
          word1, word3
      ),
      6 / 8,
  )


@mock.patch.object(
    gcs_utils,
    "upload_to_gcs",
    return_value="gs://my_bucket_name/subtitles.srt",
)
@mock.patch.object(
    subtitles_generation_step.speech_v1.SpeechClient, "long_running_recognize"
)
def test_srt_file_output_success(self, mock_long_running_recognize, _):
  """Test that SRT file successfully written."""

  mock_long_running_recognize.return_value = {
      "results": [{
          "alternatives": [{
              "transcript": (
                  "Welcome, to todays news update. This is the sub title."
              ),
              "words": [
                  {
                      "start_time": "0:00:00",
                      "end_time": "0:00:00.500000",
                      "word": "Welcome,",
                  },
                  {
                      "start_time": "0:00:00.500000",
                      "end_time": "0:00:00.800000",
                      "word": "to",
                  },
                  {
                      "start_time": "0:00:00.800000",
                      "end_time": "0:00:00.900000",
                      "word": "todays",
                  },
                  {
                      "start_time": "0:00:00.900000",
                      "end_time": "0:00:01.400000",
                      "word": "news",
                  },
                  {
                      "start_time": "0:00:01.400000",
                      "end_time": "0:00:01.900000",
                      "word": "update.",
                  },
                  {
                      "start_time": "0:00:01.900000",
                      "end_time": "0:00:02.700000",
                      "word": "This",
                  },
                  {
                      "start_time": "0:00:02.700000",
                      "end_time": "0:00:03",
                      "word": "is",
                  },
                  {
                      "start_time": "0:00:03",
                      "end_time": "0:00:03.300000",
                      "word": "the",
                  },
                  {
                      "start_time": "0:00:03.300000",
                      "end_time": "0:00:03.800000",
                      "word": "sub",
                  },
                  {
                      "start_time": "0:00:03.800000",
                      "end_time": "0:00:04.200000",
                      "word": "title.",
                  },
              ],
          }]
      }]
  }
  transcript_text = "Welcome to today's news update. This is the subtitle."
  expected_subtitles = (
      "1\n"
      "00:00:00,000 --> 00:00:01.900\n"
      "Welcome to today's news update.\n"
      "2\n"
      "00:00:01.900 --> 00:00:04.200\n"
      "This is the subtitle.\n"
  )

  step = audio.subtitles_generation_step.SubtitlesGenerationStep(self.context)
  output_path = "tests/audio/generated/testvideoid/subtitles.srt"

  with mock.patch("builtins.open", mock.mock_open()) as mock_file:
    srt_file_path = step("gs://my_bucket_name/fake_audio.wav", transcript_text)
    mock_file.assert_called_once_with(output_path, "w")
    mock_file.return_value.write.assert_called_once_with(expected_subtitles)
    self.assertEqual(srt_file_path, "gs://my_bucket_name/subtitles.srt")


if __name__ == "__main__":
  unittest.main()
