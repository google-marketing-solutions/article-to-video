"""Workdir removal pipeline step for generated files."""

import glob
import os
import pipeline


class DeleteWorkdirStep(pipeline.VideoGenerationStep):
  """Pipeline step that removes the output folder for generated content."""

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir

  def __call__(self, previous_step_result: str) -> str:
    """Removes the workdir folder.

    Args:
        previous_step_result: result from the previous step in the pipeline

    Returns:
        Forwards result from previous step into the next one, as the workdir is
        already in the context.
    """
    self.logger.info(f"Removing temporary files in {self.workdir}/*")
    if os.path.exists(self.workdir):
      for filename in glob.glob(f"{self.workdir}/*"):
        os.remove(filename)
      os.rmdir(self.workdir)
      return previous_step_result
