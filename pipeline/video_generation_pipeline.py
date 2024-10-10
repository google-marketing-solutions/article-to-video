"""Pipeline for generating videos."""

import functools

from pipeline.video_generation_context import VideoGenerationContext
from pipeline.video_generation_step import VideoGenerationStep


class VideoGenerationPipeline:
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

  def add_steps(self, *steps: VideoGenerationStep):
    """Adds video generation steps in the video generation pipeline.

    This method initialized an instance of each step by providing it with the
    context object for the current generation.

    Args:
        *steps: Each individual step, to be executed in order.

    Returns:
        This object, to facilitate chaining calls.
    """
    self.steps = [step(self.context) for step in steps]
    return self

  def process(self, initial_value=None):
    """Generates the video by running each of the provided steps in order.

    Args:
        initial_value: Value to be provided as the "previous_step_results" for
          the first step in the pipeline

    Returns:
        Result from the last step executed.
    """
    return functools.reduce(lambda a, b: b(a), self.steps, initial_value)
