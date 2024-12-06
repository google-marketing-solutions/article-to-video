import unittest
from unittest import mock
from google.cloud import language_v2
from text import sentiment_analysis_step


class SentimentAnalyzerStepTest(unittest.TestCase):

  @mock.patch.object(language_v2, "LanguageServiceClient", autospec=True)
  def test_returns_negative_sentiment_analysis(self, mock_client):
    mock_client_instance = mock_client.return_value

    sentiment = language_v2.Sentiment(magnitude=1.95, score=-0.86)
    mock_response = mock.Mock(document_sentiment=sentiment)
    mock_client_instance.analyze_sentiment.return_value = mock_response

    step = sentiment_analysis_step.SentimentAnalyzerStep(
        client=mock_client_instance
    )
    content = (
        "This article is very mean and mad. No one likes what it is saying."
    )
    analysis = step.process(content)
    expected_response = "background_music/mild_very_negative.mp3"
    self.assertEqual(analysis, expected_response)

  if __name__ == "__main__":
    unittest.main()
