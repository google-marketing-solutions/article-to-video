"""Abstract representation of a step in the video generation pipeline."""

import abc
import logging
from pipeline.video_generation_context import VideoGenerationContext


class VideoGenerationStep(abc.ABC):
  """Abstract representation of a step in the video generation pipeline.

  This class is supposed to be used as a base class for all the intermediate
  steps in the generation of the final video file.
  """

  def __init__(self, context: VideoGenerationContext):
    """Creates instance of the current step.

    Args:
        context: General video generation settings, shared among all the video
          generation steps.
    """
    self.logger = logging.getLogger(self.__class__.__name__)
    self.context = context

  @abc.abstractmethod
  def __call__(self, previous_step_results):
    """Executes the current step in the pipeline.

    Args:
        previous_step_results: Usually the path of the generated file from
          previous step, but can be a tuple of values, depending on how many
          previous steps results the current step depends on.
    """
    pass
