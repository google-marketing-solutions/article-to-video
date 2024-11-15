"""Video generation pipeline step for generating the base video from images."""

import logging
from typing import TypedDict
from moviepy import editor as mpy
import pipeline
import storyboarding
from video import video_generation_errors
from video.create_text_overlay_step import (create_text_overlay_video_clip)


class Visual(TypedDict):
  file_name: str
  start_time: float


class GenerateVideoFromImagesStep(pipeline.BaseStep):
  """Class that will stitch together the input images to generate base video."""

  def __init__(
      self,
      output_path: str,
      target_resolution: tuple[int, int] = (1280, 720),
      fps: int = 25,
      ken_burns: bool = True,
  ):
    self._logger = logging.getLogger(self.__class__.__name__)
    self._output_path = output_path
    self._target_resolution = target_resolution
    self._fps = fps
    self._ken_burns = ken_burns

  def process(self, storyboard: storyboarding.Storyboard) -> str:
    """Creates a video concatenating different images and text taken as input.

    Args:
        storyboard: The storyboard on which to base the generation.

    Returns:
        A string with the output file path.

    Raises:
        NoImagesFoundError: If the input path provided for the images contains
        no images.
    """
    number_of_images = len(storyboard.scenes)
    if number_of_images == 0:
      raise video_generation_errors.NoImagesFoundError()

    audio_clip = mpy.AudioFileClip(storyboard.main_audio_path)
    audio_file_length = audio_clip.duration

    self._logger.info("Generating video output_video_path from:")
    self._logger.info("\t%i images:", number_of_images)
    for scene in storyboard.scenes:
      self._logger.info("\t-%s", scene.background_image_path)
    self._logger.info("\tWith %s s duration", audio_file_length)

    clips = []
    # Add the scenes
    for i, scene in enumerate(storyboard.scenes):
      clip_end_time = (
          audio_file_length
          if i + 1 == len(storyboard.scenes)
          else storyboard.scenes[i + 1].start_time
      )
      clip = (
          mpy.ImageClip(
              scene.background_image_path,
              duration=clip_end_time - scene.start_time + 1,
          )
          .resize(width=self._target_resolution[0])
          .set_fps(self._fps)
          .set_start(scene.start_time - 1)
      )
      if self._ken_burns:
        # Apply the Ken Burns effect (zoom, pan, fade)
        clip = clip.resize(lambda t: min(1 + 0.0375 * t, 1.5)).crossfadein(1.0)

      clips.append(clip)
    # Add the text overlays
    video_width, video_height = self._target_resolution
    for text_overlay_obj in storyboard.text_overlays:
      text_overlay_video_clip = create_text_overlay_video_clip(
          video_width, video_height, text_overlay_obj
      )
      clips.append(text_overlay_video_clip)

    composite_video = mpy.CompositeVideoClip(
        clips, size=self._target_resolution
    ).set_audio(audio_clip)
    composite_video.write_videofile(self._output_path)

    audio_clip.close()
    composite_video.close()
    for clip in clips:
      clip.close()

    return self._output_path
