import unittest
from pipeline.video_generation_pipeline import VideoGenerationPipeline
from pipeline.video_generation_step import VideoGenerationStep
from truth.truth import AssertThat


class VideoGenerationPipelineTest(unittest.TestCase):

  class FakeStepAddTwo(VideoGenerationStep):

    def __call__(self, previous_step_results):
      return previous_step_results + 2

  class FakeStepMultiplyByFour(VideoGenerationStep):

    def __call__(self, previous_step_results):
      return previous_step_results * 4

  def test_steps_are_executed_in_order(self):
    result = (
        VideoGenerationPipeline(None)
        .add_steps(self.FakeStepAddTwo, self.FakeStepMultiplyByFour)
        .process(1)
    )

    AssertThat(result).IsEqualTo(12)
