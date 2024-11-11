import unittest
from unittest import mock
from google.cloud import language_v2
import pipeline
from text import sentiment_analysis_step


class SentimentAnalyzerStepTest(unittest.TestCase):

  @classmethod
  def setUp(cls):
    super().setUp(cls)
    cls.context = pipeline.VideoGenerationContext(
        {
            "workdir": "tests/text/generated",
            "gcp_project": "somegcpproject",
            "gcp_location": "us-central1",
            "gcs_bucket_name": "my_bucket_name",
            "gcs_bucket_text_path": "my_gcs_bucket_text_path",
            "gcs_bucket_image_path": "my_gcs_bucket_image_path",
            "output_path": "tests/text/generated",
        },
        request_params={},
        video_id="somevideoid",
    )

  @mock.patch.object(language_v2, "AnalyzeSentimentRequest", autospec=True)
  def test_returns_negative_sentiment_analysis(self, mock_analyze_sentiment):
    step = sentiment_analysis_step.SentimentAnalyzerStep(self.context)
    content = (
        "This article is very mean and mad. No one likes what it is saying."
    )
    sentiment = {"magnitude": -0.86, "score": 1.95}
    mock_response = mock.Mock()
    mock_response.json.return_value.document_sentiment = sentiment
    mock_analyze_sentiment.return_value = mock_response
    analysis = step(content)
    self.assertEqual(analysis, "mild_very_negative")

  if __name__ == "__main__":
    unittest.main()
