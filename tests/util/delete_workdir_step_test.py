import unittest
from unittest import mock

from pipeline import video_generation_context
from util import delete_workdir_step


class DeleteWorkdirStepTest(unittest.TestCase):

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

  @mock.patch("glob.glob")
  @mock.patch("os.remove")
  @mock.patch("os.rmdir")
  @mock.patch("os.path.exists")
  def test_delete_dir_correctly(self, path, rmdir, remove, glob):
    step = delete_workdir_step.DeleteWorkdirStep(self.context)
    path.return_value = True
    glob.return_value = ["a/b/c", "d/f/g"]
    step("")
    remove.assert_has_calls([mock.call("a/b/c"), mock.call("d/f/g")])
    rmdir.assert_called_once_with(
        "tests/util/output/0218e40f-d722-4391-8ef7-47bbdaa29200"
    )
