"""Article summary generation pipeline step."""

import logging
import pipeline
from . import script_generation


class SummarizeTextStep(
    pipeline.BaseStep[str, script_generation.VoiceoverScript]
):
  """Pipeline step for script generation."""

  _OUTPUT_FILE = "1_script.json"

  def __init__(
      self, workdir: str, script_generator: script_generation.ScriptGenerator
  ):
    super().__init__()
    self._workdir = workdir
    self._script_generator = script_generator

    self._logger = logging.getLogger(self.__class__.__name__)

  def process(self, content: str) -> script_generation.VoiceoverScript:
    """Script generation step.

    Args:
        content: A string. Text of the article to be summarized.

    Returns:
        A VoiveoverScript.
    """
    output_path = f"{self._workdir}/{self._OUTPUT_FILE}"
    self._logger.info("Creating voiceover script from article text.")
    script = self._script_generator.generate(content, output_path)
    self._logger.info("Script saved to %s,", output_path)
    return script
