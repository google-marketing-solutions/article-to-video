"""Video generation pipeline step for converting narration voiceovers from .mp3 to .wav format."""

import pipeline


class ConvertMp3ToWavStep(pipeline.FfmpegStep):
  """Uses ffmpeg to convert the given mp3 file to wav."""

  _OUTPUT_FILE = "3_readaloud.wav"

  def __init__(self, context: pipeline.VideoGenerationContext) -> None:
    super().__init__(context)
    self.workdir = context.workdir

  def __call__(self, input_mp3_file: str) -> str:
    """Converts the mp3 audio file to wav.

    Args:
        input_mp3_file: Path of the file to be converted.

    Returns:
        The path of the wav file.
    """
    output_path = f"{self.workdir}/{self._OUTPUT_FILE}"
    self.logger.info(f"Converting {input_mp3_file} to {output_path}...")
    ffmpeg_command = ["ffmpeg", "-y", "-i", input_mp3_file, output_path]
    self.execute_ffmpeg_command(ffmpeg_command)
    return output_path
