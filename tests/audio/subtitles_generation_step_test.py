import datetime
import os
import unittest
from unittest import mock

import audio
from audio import subtitles_generation_step
from google.cloud import speech_v1
import pipeline
from util import gcs_utils


class SubtitlesGenerationStepTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    output_dir = "tests/audio/generated/somevideoid"
    os.makedirs(output_dir, exist_ok=True)

  def setUp(self):
    super().setUp()
    self.context = pipeline.VideoGenerationContext.from_request(
        {
            "gcp_project": "my_gcp_project",
            "gcp_location": "us_west",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/audio/generated",
        },
        request_params={"article_content": "my article", "image_paths": []},
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
  @mock.patch("audio.subtitles_generation_step.speech_v1.SpeechClient")
  @mock.patch("builtins.open", new_callable=mock.mock_open)
  def test_srt_file_output_success(
      self, mock_open_file, mock_speech_client_class, mock_upload_to_gcs
  ):
    """Test that SRT file successfully written."""

    mock_word_info = []
    words_data = [
        {
            "start_time": {"seconds": 0, "nanos": 0},
            "end_time": {"seconds": 0, "nanos": 500000000},
            "word": "Welcome,",
        },
        {
            "start_time": {"seconds": 0, "nanos": 500000000},
            "end_time": {"seconds": 0, "nanos": 800000000},
            "word": "to",
        },
        {
            "start_time": {"seconds": 0, "nanos": 800000000},
            "end_time": {"seconds": 0, "nanos": 900000000},
            "word": "todays",
        },
        {
            "start_time": {"seconds": 0, "nanos": 900000000},
            "end_time": {"seconds": 1, "nanos": 400000000},
            "word": "news",
        },
        {
            "start_time": {"seconds": 1, "nanos": 400000000},
            "end_time": {"seconds": 1, "nanos": 900000000},
            "word": "update.",
        },
        {
            "start_time": {"seconds": 1, "nanos": 900000000},
            "end_time": {"seconds": 2, "nanos": 700000000},
            "word": "This",
        },
        {
            "start_time": {"seconds": 2, "nanos": 700000000},
            "end_time": {"seconds": 3, "nanos": 0},
            "word": "is",
        },
        {
            "start_time": {"seconds": 3, "nanos": 0},
            "end_time": {"seconds": 3, "nanos": 300000000},
            "word": "the",
        },
        {
            "start_time": {"seconds": 3, "nanos": 300000000},
            "end_time": {"seconds": 3, "nanos": 800000000},
            "word": "sub",
        },
        {
            "start_time": {"seconds": 3, "nanos": 800000000},
            "end_time": {"seconds": 4, "nanos": 200000000},
            "word": "title.",
        },
    ]
    for data in words_data:
      word_info = speech_v1.types.WordInfo()

      # Calculate total seconds (including nanoseconds fraction) for
      # start time
      start_total_seconds = data["start_time"]["seconds"] + (
          data["start_time"]["nanos"] / 1_000_000_000.0
      )
      word_info.start_time = datetime.timedelta(seconds=start_total_seconds)

      # Calculate total seconds (including nanoseconds fraction) for end
      # time
      end_total_seconds = data["end_time"]["seconds"] + (
          data["end_time"]["nanos"] / 1_000_000_000.0
      )
      word_info.end_time = datetime.timedelta(seconds=end_total_seconds)

      word_info.word = data["word"]
      mock_word_info.append(word_info)

    mock_result = mock.Mock()
    mock_alternative = mock.Mock()
    mock_alternative.transcript = (
        "Welcome, to todays news update. This is the sub title."
    )
    mock_alternative.words = mock_word_info
    mock_result.alternatives = [mock_alternative]

    mock_operation = mock.Mock()
    mock_operation.result.return_value.results = [mock_result]
    mock_client = mock_speech_client_class.return_value
    mock_client.long_running_recognize.return_value = mock_operation

    transcript_text = "Welcome to today's news update. This is the subtitle."
    expected_subtitles = (
        "1\n"
        "00:00:00,000 --> 00:00:01,900\n"
        " Welcome to today's news update.\n"
        "\n"
        "2\n"
        "00:00:01,900 --> 00:00:04,200\n"
        " This is the subtitle.\n"
        "\n"
    )

    step = audio.subtitles_generation_step.SubtitlesGenerationStep(self.context)
    srt_file_path = step(
        ("gs://my_bucket_name/fake_audio.wav", transcript_text)
    )

    expected_calls = [
        mock.call("tests/audio/generated/testvideoid/subtitles_plain.txt", "w"),
        mock.call("tests/audio/generated/testvideoid/3_subtitles.srt", "w"),
    ]
    mock_open_file.assert_has_calls(expected_calls, any_order=True)

    srt_file_handle = mock_open_file()
    srt_file_handle.writelines.assert_called()
    call_args, _ = srt_file_handle.writelines.call_args
    written_content = "".join(list(call_args[0]))
    self.assertEqual(written_content, expected_subtitles)

    mock_upload_to_gcs.assert_called_once_with(
        "tests/audio/generated/testvideoid/3_subtitles.srt",
        "my_bucket_name",
        "testvideoid/3_subtitles.srt",
        gcp_project="my_gcp_project",
    )

    self.assertEqual(
        srt_file_path, "tests/audio/generated/testvideoid/3_subtitles.srt"
    )


if __name__ == "__main__":
  unittest.main()
