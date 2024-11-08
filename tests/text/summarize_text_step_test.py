import os
import unittest
from unittest import mock
import pipeline
import text


class SummarizeTextStepTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    output_dir = "tests/summaries/generated/somearticleid"
    os.makedirs(output_dir, exist_ok=True)

  def setUp(self):
    super().setUp()
    self.context = pipeline.VideoGenerationContext(
        {
            "workdir": "tests/summaries/generated",
            "gcp_project": "somegcpproject",
            "gcp_location": "us-central1",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/summaries/generated",
            "language": "en",
        },
        request_params={},
        video_id="somearticleid",
    )

  @mock.patch("text.summarize_text_step.vertexai.init")
  @mock.patch("text.summarize_text_step.GenerativeModel")
  def test_generate_summary_creates_summary_file(
      self, mock_generative_model
  ):
    """Test that article summary is generated and saved correctly."""
    step = text.summarize_text_step.SummarizeTextStep(self.context)
    article_content = (
        "This is a sample article with some statistics like 50% increase and 10"
        " million dollars."
    )

    mock_model = mock_generative_model.return_value
    mock_model.generate_content.return_value.text = (
        "This is a summary that captures attention. It discusses the article's"
        " main points. It mentions important statistics like 50% increase and"
        " 10 million dollars. Finally, it concludes the article's relevance."
    )

    output_path = "tests/summaries/generated/somearticleid/1_summary.txt"

    with mock.patch("builtins.open", mock.mock_open()) as mocked_file:
      summary_text = step(article_content)

    mocked_file.assert_any_call(output_path, "w")

    handle = mocked_file()
    handle.write.assert_called_once_with(
        "This is a summary that captures attention. It discusses the article's"
        " main points. It mentions important statistics like 50% increase and"
        " 10 million dollars. Finally, it concludes the article's relevance."
    )

    self.assertEqual(
        summary_text,
        "This is a summary that captures attention. It discusses the article's"
        " main points. It mentions important statistics like 50% increase and"
        " 10 million dollars. Finally, it concludes the article's relevance.",
    )


if __name__ == "__main__":
  unittest.main()
