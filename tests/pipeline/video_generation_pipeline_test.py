import unittest
from pipeline.video_generation_pipeline import VideoGenerationPipeline
from pipeline.video_generation_step import VideoGenerationStep
from truth.truth import AssertThat


class VideoGenerationPipelineTest(unittest.TestCase):

  class FakeStepAddTwo(VideoGenerationStep):

    def __call__(self, previous_step_results):
      return previous_step_results + 2

  class FakeStepSplitIntoTuple(VideoGenerationStep):

    def __call__(self, previous_step_results):
      return previous_step_results, previous_step_results

  class FakeStepAddTogether(VideoGenerationStep):

    def __call__(self, previous_step_results):
      return previous_step_results[0] + previous_step_results[1]

  def test_steps_are_executed_in_order(self):
    result = (
        VideoGenerationPipeline(None)
        .add_steps(
            self.FakeStepAddTwo,
            self.FakeStepSplitIntoTuple,
            self.FakeStepAddTogether,
        )
        .process(1)
    )
    AssertThat(result).IsEqualTo(6)
