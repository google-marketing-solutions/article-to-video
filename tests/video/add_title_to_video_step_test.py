import os
import unittest

from pipeline import video_generation_context
from truth import truth
from video import add_title_to_video_step


class AddTitleToVideoStepTest(unittest.TestCase):

  _CONTEXT = video_generation_context.VideoGenerationContext(
      {
          "gcp_project": "my_gcp_project",
          "gcp_location": "us_west",
          "gcs_bucket_name": "my_bucket_name",
          "gcs_bucket_text_path": "my_gcs_bucket_text_path",
          "gcs_bucket_image_path": "my_gcs_bucket_image_path",
          "output_path": "tests/video/generated/add_title_to_video_step",
      },
      {},
      "0218e40f-d722-4391-8ef7-47bbdaa29200",
  )
  step = add_title_to_video_step.AddTitleToVideoStep(_CONTEXT)

  def test_runs_command_and_validates_golden(self):
    article_title = "Testing Title"
    video_path = "tests/video/goldens/7_withlogovideo.mp4"

    result = self.step((article_title, video_path))
    # Compare result with the golden file
    files_equal = True
    with (
        open("tests/video/goldens/7a_withtitlevideo.mp4", "rb") as golden_file,
        open(result, "rb") as output_file,
    ):
      while True:
        golden_chunk = golden_file.read(1000)
        output_chunk = output_file.read(1000)
        if not golden_chunk and not output_chunk:
          break
        if golden_chunk != output_chunk:
          files_equal = False
          break

    truth.AssertThat(files_equal).IsTrue()
    if os.path.exists(result):
      os.remove(result)
