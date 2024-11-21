import os
import tempfile
import textwrap
import unittest
from unittest import mock

import pipeline
import text
import vertexai
import vertexai.generative_models


class SummarizeTextStepTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.workdir = tempfile.TemporaryDirectory()
    os.makedirs(self.workdir.name + "/somearticleid", exist_ok=True)

    self.context = pipeline.VideoGenerationContext(
        {
            "gcp_project": "somegcpproject",
            "gcp_location": "us-central1",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": self.workdir.name,
            "language": "en",
        },
        request_params={},
        video_id="somearticleid",
    )

  def tearDown(self):
    self.workdir.cleanup()
    return super().tearDown()

  @mock.patch.object(
      vertexai.generative_models, "GenerativeModel", autospec=True
  )
  def test_summarize_article_for_single_voice(self, mock_generative_model):
    self.context.multivoice = False
    step = text.summarize_text_step.SummarizeTextStep(self.context)
    mock_generative_model.return_value.generate_content.return_value.text = (
        "article summary"
    )

    self.assertEqual(
        step("some article content"),
        "article summary",
    )

  @mock.patch.object(
      vertexai.generative_models, "GenerativeModel", autospec=True
  )
  def test_summarize_article_for_single_voice_prompt(
      self, mock_generative_model
  ):
    self.context.multivoice = False
    step = text.summarize_text_step.SummarizeTextStep(self.context)
    mock_generative_model.return_value.generate_content.return_value.text = (
        "article summary"
    )

    step("some article content")

    mock_generative_model.return_value.generate_content.assert_called_once_with(
        textwrap.dedent("""\
        Summarize the content of the following article according to these rules:
        1. The summary must have between 300 and 600 words.
        2. The summary must not mention the author's name.
        3. The summary must start with a phrase that captures the attention of
           the audience  and is related to the content of the article.
        4. The summary must end with a conclusion.
        5. In the case that the article has numbers of statistics, they should
           be mentioned in the summary.
        6. The summary must have more than two phrases.
        7. The summary must have less than six phrases.
        8. The language for the article and for response is en-US

        The article to be summarized is as follows:
        some article content
      """),
        generation_config=mock.ANY,
    )

  def test_return_article_for_multivoice(self):
    self.context.multivoice = True
    step = text.summarize_text_step.SummarizeTextStep(self.context)

    self.assertEqual(
        step("some article content"),
        "some article content",
    )

  def test_creates_file_with_return_value(self):
    """Test that article summary is generated and saved correctly."""
    self.context.multivoice = True
    step = text.summarize_text_step.SummarizeTextStep(self.context)

    output_path = self.workdir.name + "/somearticleid/1_summary.txt"

    with mock.patch("builtins.open", mock.mock_open()) as mocked_file:
      step("some article content")

    mocked_file.assert_any_call(output_path, "w", encoding="utf-8")
    mocked_file.return_value.write.assert_called_once_with(
        "some article content"
    )


if __name__ == "__main__":
  unittest.main()
