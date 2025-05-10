"""Text generation pipeline step for determining sentiment of the article summary."""

import enum
import logging
from google.cloud import language_v2


class Sentiment(enum.Enum):
  VERY_NEGATIVE = (1,)
  NEGATIVE = (2,)
  NEUTRAL = (3,)
  POSITIVE = (4,)
  VERY_POSITIVE = 5


class Intensity(enum.Enum):
  MILD = (1,)
  MEDIUM = (2,)
  INTENSE = 3


class SentimentAnalyzerStep:
  """A pipeline step that determines the sentiment of the article summary."""

  def __init__(self, client=None):
    super().__init__()
    self.client = client or language_v2.LanguageServiceClient()
    self.logger = logging.getLogger(self.__class__.__name__)

  def process(self, content: str) -> str:
    """Summary sentiment analysis.

    Args:
        content: The article summary text.

    Returns:
        An output path for the background music file.
    """
    type_ = language_v2.Document.Type.PLAIN_TEXT
    document = {"type_": type_, "content": content}

    self.logger.info("Analysing sentiment on article summary...")
    response = self.client.analyze_sentiment(request={"document": document})
    analysis = response.document_sentiment

    sentiment = Sentiment.NEUTRAL
    intensity = Intensity.MILD
    match analysis.score:
      case score if score >= 0.75:
        sentiment = Sentiment.VERY_POSITIVE
      case score if score >= 0.25:
        sentiment = Sentiment.POSITIVE
      case score if score >= -0.25:
        sentiment = Sentiment.NEUTRAL
      case score if score >= -0.75:
        sentiment = Sentiment.NEGATIVE
      case _:
        sentiment = Sentiment.VERY_NEGATIVE

    match analysis.magnitude:
      case magnitude if magnitude >= 4:
        intensity = Intensity.INTENSE
      case magnitude if magnitude >= 2:
        intensity = Intensity.MEDIUM
      case _:
        intensity = Intensity.MILD

    result = f"{intensity.name.lower()}_{sentiment.name.lower()}"
    self.logger.info(
        "\tScore: %s Magnitude: %s -> %s",
        analysis.score,
        analysis.magnitude,
        result,
    )

    output_path = f"background_music/{result}.mp3"

    return str(output_path)
