"""Pipeline for generating videos."""

from pipeline import base
from pipeline.video_generation_context import VideoGenerationContext
from pipeline.video_generation_step import VideoGenerationStep
from typing_extensions import Self


class VideoGenerationPipeline(base.Pipeline):
  """Pipeline for generating videos.

  Typical usage would be:
      VideoGenerationPipeline(context).add_steps(GenerationStep1,
      GenerationStep2, GenerationStep3).process(initial_value)
  """

  def __init__(self, context: VideoGenerationContext):
    """Creates instance of the video generation pipeline.

    Args:
        context: General video generation settings, shared among all the video
          generation steps.
    """
    self.context = context
    self.steps: list[VideoGenerationStep] = []

  def add_steps(self, *steps: VideoGenerationStep) -> Self:
    """Adds video generation steps in the video generation pipeline.

    This method initialized an instance of each step by providing it with the
    context object for the current generation.

    Args:
        *steps: Each individual step, to be executed in order.

    Returns:
        This object, to facilitate chaining calls.
    """
    self.steps.extend([step(self.context) for step in steps])
    return self
