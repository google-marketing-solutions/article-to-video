import unittest
from unittest import mock

from pipeline import video_generation_context
from truth import truth
from video import add_logo_to_video_step


class AddLogoToVideoStepTest(unittest.TestCase):

  context = video_generation_context.VideoGenerationContext(
      {
          "gcp_project": "my_gcp_project",
          "gcp_location": "us_west",
          "gcs_bucket_name": "my_bucket_name",
          "gcs_bucket_text_path": "my_gcs_bucket_text_path",
          "gcs_bucket_image_path": "my_gcs_bucket_image_path",
          "output_path": "tests/video/generated/add_logo_to_video_step",
      },
      {},
      "0218e40f-d722-4391-8ef7-47bbdaa29200",
  )

  def test_overlays_logo_correctly(self):
    step = add_logo_to_video_step.AddLogoToVideoStep(self.context)
    execute_ffmpeg_command = mock.MagicMock()
    step.execute_ffmpeg_command = execute_ffmpeg_command
    with mock.patch("os.path.exists") as m:
      m.return_value = True
      step("/my/input/video.mp4")

    execute_ffmpeg_command.assert_called_once_with([
        "ffmpeg",
        "-i",
        "/my/input/video.mp4",
        "-i",
        "tests/video/generated/add_logo_to_video_step/0218e40f-d722-4391-8ef7-47bbdaa29200/favicon.ico",
        "-filter_complex",
        '"[1]scale=50:50,format=rgba,colorchannelmixer=aa=0.7[logo];[0][logo]overlay=x=W-w-32:y=18"',
        "-c:a",
        "copy",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-y",
        "tests/video/generated/add_logo_to_video_step/0218e40f-d722-4391-8ef7-47bbdaa29200/7_withlogovideo.mp4",
    ])

  def test_returns_original_video_if_logo_does_not_exist(self):
    step = add_logo_to_video_step.AddLogoToVideoStep(self.context)
    execute_ffmpeg_command = mock.MagicMock()
    step.execute_ffmpeg_command = execute_ffmpeg_command
    with mock.patch("os.path.exists") as m:
      m.return_value = False
      result = step("/my/input/video.mp4")
      truth.AssertThat(result).IsEqualTo("/my/input/video.mp4")
    execute_ffmpeg_command.assert_not_called()

  def test_runs_command_and_validates_golden(self):
    step = add_logo_to_video_step.AddLogoToVideoStep(self.context)

    result = step("tests/video/goldens/video.mp4")

    files_equal = True
    with open("tests/video/goldens/7_withlogovideo.mp4", "rb") as one:
      with open(result, "rb") as two:
        chunk = other = True
        while chunk or other:
          chunk = one.read(1000)
          other = two.read(1000)
          if chunk != other:
            files_equal = False

    truth.AssertThat(files_equal).IsTrue()
