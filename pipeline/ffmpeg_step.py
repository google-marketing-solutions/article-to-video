"""Defines abstract class to be used by steps that use FFMPEG."""

import subprocess

from pipeline.video_generation_context import VideoGenerationContext
from pipeline.video_generation_error import VideoGenerationError
from pipeline.video_generation_step import VideoGenerationStep


class FfmpegStep(VideoGenerationStep):
  """Base class to be used by the steps that rely on ffmpeg to do the video generation."""

  def __init__(self, context: VideoGenerationContext, runner=subprocess.run):
    super().__init__(context)
    self.runner = runner

  def _execute_ffmpeg_command(self, command: list[str]) -> str:
    """Executes a ffmpeg command as a subprocess.

    Args:
      command: String containing the ffmpeg command to be executed.

    Returns:
      String with the stdout by the ffmpeg client.

    Raises:
      VideoGenerationError: If the FFMPEG command was unsuccessful.
    """
    ffmpeg_command_txt = " ".join(command)
    pipe = self.runner(
        ffmpeg_command_txt,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**9,
    )

    if pipe.returncode != 0:
      self.logger.error("Error executing ffmpeg:")
      self.logger.error("\t%s", ffmpeg_command_txt)
      self.logger.error(str(pipe.stderr))
      raise VideoGenerationError("FFMPEG errored out.")

    return str(pipe.stdout)
