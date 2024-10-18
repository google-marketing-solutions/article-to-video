"""Video generation pipeline step for generating the base video from images."""

import glob
import math
import pipeline
from video import video_generation_errors


class GenerateVideoFromImagesStep(pipeline.FfmpegStep):
  """Class that will stitch together the input images to generate base video."""

  _OUTPUT_FILE: str = "5_mutedvideo.mp4"
  _FPS: int = 25
  _TARGET_RESOLUTION: str = "1280x720"

  def __init__(self, context: pipeline.VideoGenerationContext) -> None:
    super().__init__(context)
    self._workdir = context.workdir
    self._ken_burns = context.ken_burns

  def _get_audio_length(self, media_file: str) -> float:
    """Calculates a media file length.

    Args:
        media_file: A string of the media files path.

    Returns:
        A float with the length in seconds.
    """
    ffmpeg_command = [
        "ffprobe",
        "-i",
        media_file,
        "-show_entries",
        "format=duration",
        "-v",
        "quiet",
        "-of",
        'csv="p=0"',
    ]

    length_in_seconds = (
        self.execute_ffmpeg_command(ffmpeg_command)
        .replace("b", "")
        .replace("n", "")
        .replace("\\", "")
        .replace("'", "")
    )
    return float(length_in_seconds)

  def __call__(self, params: tuple[str, str]) -> str:
    """Creates a video concatenating different images taken as input.

    Args:
        params: Tuple containing the path of the source images to use in the
          video as well as the path of the audio to be used in the video.

    Returns:
        A string with the output file path.

    Raises:
        NoImagesFoundError: If the input path provided for the images contains
        no images.
    """
    (images_glob, input_audio_path) = params
    audio_file_length = self._get_audio_length(input_audio_path)
    number_of_images = len(glob.glob(images_glob))
    if number_of_images == 0:
      raise video_generation_errors.NoImagesFoundError()

    video_transition_effect = "fade"  # fade, slideright, circleopen, fadeblack
    output_video_path = f"{self._workdir}/{self._OUTPUT_FILE}"
    self.logger.info("Generating video output_video_path from:")
    self.logger.info(f"\t{number_of_images} images located at {images_glob}")
    self.logger.info(f"\tWith {audio_file_length}s duration.")

    each_image_duration = audio_file_length / number_of_images

    command = ["ffmpeg"]
    filter_complex_string = ""

    for i, image in enumerate(glob.glob(images_glob)):
      command.extend(["-i", image])  # Add each image as an input to the command

      if self._ken_burns:
        # Apply the Ken Burns effect (zoom, pan, fade)
        filter_complex_string += (
            f"[{i}:v]zoompan=z='min(zoom+0.0015,1.5)':d={math.floor(self._FPS * (each_image_duration+1))}:s={self._TARGET_RESOLUTION},"
            f"fade=t=out:st={each_image_duration}:d=1[v{i}];"
        )
      else:
        filter_complex_string += (
            f"[{i}:v]scale={self._TARGET_RESOLUTION},setsar=1[v{i}];"
        )

    # Apply transitions between images
    offset = each_image_duration - 1
    for i in range(number_of_images - 1):
      # Transition effect between image[i] and image[i+1]
      filter_complex_string += f"[v{i}][v{i+1}]xfade=transition={video_transition_effect}:duration=1:offset={offset}[v{i+1}];"
      offset += each_image_duration

    # Remove the trailing semicolon to avoid syntax errors
    filter_complex_string = filter_complex_string.rstrip(";")

    command.extend([
        "-filter_complex",
        f'"{filter_complex_string}"',
        "-map",
        f"[v{number_of_images - 1}]",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(self._FPS),
        "-y",
        output_video_path,
    ])

    self.execute_ffmpeg_command(command)
    return (output_video_path, input_audio_path)
