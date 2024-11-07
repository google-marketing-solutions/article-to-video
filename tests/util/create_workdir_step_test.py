import unittest
from unittest import mock

from pipeline import video_generation_context
from util import create_workdir_step


class CreateWorkdirStepTest(unittest.TestCase):

  context = video_generation_context.VideoGenerationContext(
      {
          "gcp_project": "my_gcp_project",
          "gcp_location": "us_west",
          "gcs_bucket_name": "my_bucket_name",
          "gcs_bucket_text_path": "text",
          "gcs_bucket_image_path": "images",
          "output_path": "tests/util/output",
      },
      {},
      "0218e40f-d722-4391-8ef7-47bbdaa29200",
  )

  def test_create_dir_correctly(self):
    step = create_workdir_step.CreateWorkdirStep(self.context)
    execute_ffmpeg_command = mock.MagicMock()
    step.execute_ffmpeg_command = execute_ffmpeg_command
    with mock.patch("os.makedirs") as m:
      step("")
      m.assert_called_once_with(
          "tests/util/output/0218e40f-d722-4391-8ef7-47bbdaa29200",
          exist_ok=True,
      )
