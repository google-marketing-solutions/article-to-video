"""Abstract representation of a step in the video generation pipeline."""

import logging
from pipeline.video_generation_context import VideoGenerationContext


class VideoGenerationStep:
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

  def process(self, initial_value=None):
    # Ideally, the process function would be implemented here, but the original
    # implementation overrides __call__ directly so doing it this way ensures
    # backwards compatibility with previously created steps.
    self.__call__(initial_value)
