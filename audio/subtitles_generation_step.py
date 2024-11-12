"""Subtitles generation pipeline step."""

import re
from typing import Tuple
import pipeline
from util.errors import GeminiError
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.generative_models import Part


class SubtitlesGenerationStep(pipeline.VideoGenerationStep):
  """Pipeline step for generating SRT file based on text and audio file."""

  _OUTPUT_SRT_FILE = "subtitles.srt"

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location

  def __call__(self, audio_and_transcript: Tuple[str, str]) -> str:
    """Generate subtitles SRT file based on audio and transcript text.

    Args:
        audio_and_transcript: Tuple that contains(audio_file_path, transcript
          text)

    Returns:
        File path for the generated SRT file.
    """

    vertexai.init(project=self.gcp_project, location=self.gcp_location)

    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.8,
        "top_k": 20,
    }

    model = GenerativeModel("gemini-1.5-pro-001")
    prompt = (
        "I have an audio speech and a text file that I need transcribed into an"
        " SRT file. The text file contains the audio transcript. Please process"
        " both files and create an SRT file. Please output the SRT content"
        " only, do not include additional words.\nHere are the key"
        " requirements: \n1. Exact Transcription: The SRT file should perfectly"
        " match the text file content, including any errors or inconsistencies"
        " present in the text.\n2. Accurate Timestamps: Accurately timestamp"
        " each phrase or sentence in the SRT file to match the speech.\n3. SRT"
        " Formatting:\n - Use standard SRT format (correct numbering of"
        " subtitles, timestamps as HH:MM:SS,mmm).\n - Begin a new subtitle line"
        " whenever there's a new paragraph in the text file. If a line is too"
        " long, break into multiple lines.\n4. Punctuation and Capitalization:"
        " Maintain the punctuation and capitalization from the text file."
    )

    audio_file = Part.from_uri(audio_and_transcript[0], mime_type="audio/mpeg")
    contents = [audio_file, audio_and_transcript[1], prompt]
    response = model.generate_content(
        contents, generation_config=generation_config
    )

    if not self.is_srt_format(response.text):
      self.logger.error("Response from Gemini is:" + response.text)
      raise GeminiError("Gemini did not generate a proper SRT file.")

    output_path = f"{self.workdir}/{self._OUTPUT_SRT_FILE}"
    self.logger.error(f"Writing Gemini response to {output_path}...")
    with open(output_path, "w") as f:
      f.write(response.text)
    self.logger.info(f"Writing Gemini response to {output_path}...")
    return audio_and_transcript[0], output_path

  def is_srt_format(self, srt_content: str) -> bool:
    """Checks if the given text is in SRT (SubRip Subtitle) format.

    Args:
        srt_content: The text to validate.

    Returns:
        bool: True if the text is in SRT format, False otherwise.
    """

    # Sequence number (e.g., 1): \d+\s*
    # Time span (e.g., 00:00:20,000 --> 00:00:24,400)
    # \d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\s*
    # One or more lines of subtitle text: (?:.+\n)*
    # Optional line break at the end: \n?
    pattern = r"""\d+\s*\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\s*\n(?:.+)*\n?"""
    matches = re.findall(pattern, srt_content)
    return bool(matches) and len("".join(matches)) == len(srt_content.strip())
