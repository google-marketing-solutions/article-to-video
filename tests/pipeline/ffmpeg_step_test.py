import subprocess
import unittest
from unittest import mock
from pipeline.ffmpeg_step import FfmpegStep
from truth.truth import AssertThat


class FfmpegStepTest(unittest.TestCase):

  class FakeFfmpegStep(FfmpegStep):

    def __call__(self, command: list[str]) -> str:
      return self.execute_ffmpeg_command(command)

  def test_executes_subprocess_with_command(self):
    execution_result = mock.MagicMock()
    execution_result.returncode = 0
    runner = mock.MagicMock(return_value=execution_result)
    ffmpeg_step = self.FakeFfmpegStep(None, runner)
    ffmpeg_step.execute_ffmpeg_command(["ffmpeg", "--help"])

    runner.assert_called_once_with(
        "ffmpeg --help",
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**9,
    )

  def test_raises_exception_when_command_fails(self):
    execution_result = mock.MagicMock()
    execution_result.returncode = 1
    runner = mock.MagicMock(return_value=execution_result)
    ffmpeg_step = self.FakeFfmpegStep(None, runner)

    with AssertThat(Exception).IsRaised():
      ffmpeg_step.execute_ffmpeg_command(["ffmpeg", "--help"])
