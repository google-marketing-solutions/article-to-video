import os
import unittest
from unittest import mock

from pipeline import video_generation_context
import srt
from text import generate_subtitles_step


class GenerateSubtitlesStepTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    output_dir = "tests/text/generated/subtitles/some_video_id"
    os.makedirs(output_dir, exist_ok=True)

  context = video_generation_context(
      {
          "workdir": "tests/text/generated/subtitles/some_video_id",
          "gcp_project": "my_gcp_project",
          "gcp_location": "us_west",
          "gcs_bucket_name": "my_bucket_name",
          "gcs_bucket_text_path": "my_gcs_bucket_text_path",
          "gcs_bucket_image_path": "my_gcs_bucket_image_path",
          "output_path": "tests/text/generated/subtitles",
      },
      request_params={},
      video_id="some_video_id",
  )

  def test_generates_srt_file_correctly(self):
    """Test that the SRT file is generated correctly from SSML output and timepoints."""

    step = generate_subtitles_step.GenerateSubtitlesStep(self.context)
    mock_timepoints = [
        mock.Mock(time_seconds=0),
        mock.Mock(time_seconds=2),
        mock.Mock(time_seconds=4),
    ]

    ssml_output = (
        '<speak><mark name="mark0"/>Hello<mark name="mark1"/>world<mark'
        ' name="mark2"/>test</speak>'
    )

    execute_open = mock.mock_open()

    with mock.patch("builtins.open", execute_open, create=True):
      step._generate_subs(
          "tests/text/generated/subtitles/some_video_id/4_subtitles.srt",
          ssml_output,
          3,
          mock_timepoints,
      )

    execute_open.assert_called_once_with(
        "tests/text/generated/subtitles/some_video_id/4_subtitles.srt", "w"
    )
    written_data = execute_open().write.call_args[0][0]
    subtitles = list(srt.parse(written_data))

    self.assertEqual(len(subtitles), 3)
    self.assertEqual(subtitles[0].content, '<mark name="mark0"/>Hello')
    self.assertEqual(subtitles[1].content, '<mark name="mark1"/>world')
    self.assertEqual(subtitles[2].content, '<mark name="mark2"/>test')

  def test_returns_correct_output_path(self):
    """Test that the output path for the SRT file is returned correctly."""

    step = generate_subtitles_step.GenerateSubtitlesStep(self.context)
    mock_timepoints = [
        mock.Mock(time_seconds=0),
        mock.Mock(time_seconds=2),
        mock.Mock(time_seconds=4),
    ]

    ssml_output = (
        '<speak><mark name="mark0"/>Hello<mark name="mark1"/>world<mark'
        ' name="mark2"/>test</speak>'
    )

    with mock.patch("builtins.open", mock.mock_open(), create=True):
      output_path = step((ssml_output, 3, mock_timepoints))

    self.assertEqual(
        output_path,
        "tests/text/generated/subtitles/some_video_id/4_subtitles.srt",
    )


if __name__ == "__main__":
  unittest.main()
