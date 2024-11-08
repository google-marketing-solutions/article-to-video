"""Article summary generation pipeline step."""

import textwrap

import pipeline
import vertexai
from vertexai import generative_models


class SummarizeTextStep(pipeline.VideoGenerationStep):
  """Pipeline step for article summary generation."""
  _OUTPUT_FILE = "1_summary.txt"

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location
    self.language = context.language

  def __call__(self, content: str) -> str:
    """Article summarization.

    Args:
        content: A string. Text of the article to be summarized.

    Returns:
        A string with the article summary
    """
    output_path = f"{self.workdir}/{self._OUTPUT_FILE}"
    self.logger.info(
        f"Summarizing article text with Gemini to {output_path}..."
    )
    vertexai.init(project=self.gcp_project, location=self.gcp_location)
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
    }
    model = generative_models.GenerativeModel("gemini-1.5-pro-001")
    response = model.generate_content(
        textwrap.dedent(
            """Summarize the content of the following article according to the rules:
        1. The summary must have between 300 and 600 words.
        2. The summary must not mention the author's name.
        3. The summary must start with a phrase that captures the attention of the audience  and is related to the content of the article.
        4. The summary must end with a conclusion.
        5. In the case that the article has numbers of statistics, they should be mentioned in the summary.
        6. The summary must have more than two phrases.
        7. The summary must have less than six phrases.
        8. The language for the article and for response is """
            + self.language
            + """
        The article to be summarized is as follows:
        """
            + content
        ),
        generation_config=generation_config,
    )
    summary_text = response.text
    summary_text = summary_text.replace("*", "")
    with open(output_path, "w") as f:
      f.write(summary_text)
    return summary_text
