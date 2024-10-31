"""Text generation pipeline step for fetching article text from GCP."""

import pipeline
import vertexai
from vertexai.generative_models import GenerativeModel


class GeminiClientStep(
    pipeline.video_generation_pipeline.VideoGenerationPipeline
):
  """A pipeline step for generating an article summary using the Gemini Generative Model.

  Attributes:
      _OUTPUT_FILE (str): The filename for the generated article summary.
  """

  _OUTPUT_FILE = "1_summary.txt"

  def __init__(
      self, context: pipeline.video_generation_context.VideoGenerationContext
  ):
    """Initializes the GeminiClientStep with the provided context.

    Args:
        context (VideoGenerationContext): The context object containing
          configurations such as work directory, GCP project, location, and
          language preferences.
    """
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location
    self.language = context.language

  def __call__(self, content: str) -> str:
    """Generates a summary of the provided article content using Gemini.

    Args:
        content (str): The text content of the article to be summarized.

    Returns:
        tuple: A tuple containing:
            - summary_text (str): The generated summary of the article.
            - ssml_output (str): The SSML-formatted text with embedded timing
            markers for TTS.
    """
    output_path = f"{self.workdir}/{self._OUTPUT_FILE}"
    self.logger.info(
        f"Summarizing article text with Gemini to {output_path}..."
    )

    # Initialize Vertex AI with GCP project settings
    vertexai.init(project=self.gcp_project, location=self.gcp_location)

    # Set configuration for content generation
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
    }

    # Generate content summary with Gemini Model
    model = GenerativeModel("gemini-1.5-pro-001")
    response = model.generate_content(
        "Summarize the content of the following article according to the rules:"
        " \n1. The summary must have between 300 and 600 words. \n2. The"
        " summary must not mention the author's name. \n3. The summary must"
        " start with a phrase that captures the attention of the audience and"
        " is related to the content of the article. \n4. The summary must end"
        " with a conclusion. \n5. In the case that the article has numbers of"
        " statistics, they should be mentioned in the summary. \n6. The summary"
        " must have more than two phrases. \n7. The summary must have less than"
        " six phrases. \n8. The language for the article and for response is "
        + self.language
        + "\nThe article to be summarized is as follows: \n"
        + content,
        generation_config=generation_config,
    )

    # Process the generated summary text
    summary_text = response.text.replace("*", "")

    # Create SSML output with markers every 6 words
    ssml_output = """<speak>\n\t<mark name="mark0"/>"""
    words = summary_text.split(" ")
    mark_tag_count = 0
    mark_tag_frequency = 6
    word_counter = 0
    for word in words:
      if word_counter == mark_tag_frequency:
        mark_tag_count += 1
        ssml_output += word.strip() + """<mark name="mark{}"/> """.format(
            mark_tag_count
        )
        word_counter = 0
        continue
      ssml_output += word + " "
      word_counter += 1
    ssml_output += """\n</speak>"""

    # Write the summary text to the output file
    with open(output_path, "w") as f:
      f.write(summary_text)

    return summary_text, ssml_output
