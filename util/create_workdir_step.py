"""Workdir creation pipeline step for generated files."""

import os
import pipeline


class CreateWorkdirStep(pipeline.VideoGenerationStep):
  """Pipeline step that creates the output folder for generated content."""

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir

  def __call__(self, previous_step_result: str) -> str:
    """Creates folder for generating content.

    Args:
        previous_step_result: result from the previous step in the pipeline

    Returns:
        Forwards result from previous step into the next one, as the workdir is
        already in the context.
    """
    self.logger.info(f"Creating output folder in {self.workdir}")
    os.makedirs(self.workdir, exist_ok=True)
    return previous_step_result
