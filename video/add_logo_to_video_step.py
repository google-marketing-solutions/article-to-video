"""Video generation pipeline step for adding publisher logo to video."""

import os
import pipeline


class AddLogoToVideoStep(pipeline.FfmpegStep):
  """Class responsible for adding the publisher logo overlay to the video."""

  _OUTPUT_FILE: str = "7_withlogovideo.mp4"

  def __init__(self, context: pipeline.VideoGenerationContext) -> None:
    super().__init__(context)
    self._workdir = context.workdir

  def __call__(self, video_path: str) -> str:
    """Overlays the publisher logo to the provided video.

    Args:
        video_path: Url of the last generated video on top of which to overlay
          the logo.

    Returns:
        The path of the generated video.
    """
    output_path = f"{self._workdir}/{self._OUTPUT_FILE}"
    logo = f"{self._workdir}/favicon.ico"

    if not os.path.exists(logo):
      self.logger.warning(
          f"Logo file {logo} does not exist. Skipping logo overlay step."
      )
      return (
          video_path  # Return the original video path if the logo doesn't exist
      )

    self.logger.info(
        f"Adding logo {logo} to {video_path} and writing to {output_path}..."
    )

    ffmpeg_command = [
        "ffmpeg",
        "-i",
        video_path,
        "-i",
        logo,
        "-filter_complex",
        (
            '"[1]scale=50:50,format=rgba,colorchannelmixer=aa=0.7[logo];'
            '[0][logo]overlay=x=W-w-32:y=18"'
        ),
        "-c:a",
        "copy",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-y",
        output_path,
    ]
    self.execute_ffmpeg_command(ffmpeg_command)
    return output_path
