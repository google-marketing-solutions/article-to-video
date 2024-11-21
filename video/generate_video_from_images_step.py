"""Video generation pipeline step for generating the base video from images."""

import logging
from moviepy import editor as mpy
import numpy as np
import pipeline
import storyboarding
from video import effects
from video import video_generation_errors
from video.create_text_overlay_step import (create_text_overlay_video_clip)

_LOGO_MARGIN = 16  # pixels


class GenerateVideoFromImagesStep(pipeline.BaseStep):
  """Class that will stitch together the input images to generate base video."""

  def __init__(
      self,
      output_path: str,
      target_resolution: tuple[int, int] = (1280, 720),
      fps: int = 25,
  ):
    self._logger = logging.getLogger(self.__class__.__name__)
    self._output_path = output_path
    self._target_resolution = target_resolution
    self._fps = fps

  def create_scene(
      self, scene: storyboarding.Scene, duration: float
  ) -> mpy.ImageClip:
    """Creates a video clip for a single scene.

    Args:
      scene: The scene object containing image path, start time, and animation.
        duration: The duration of the clip.

    Returns:
      A MoviePy ImageClip representing the scene.
    """
    clip = (
        mpy.ImageClip(scene.image_path, duration=duration)
        .resize(width=self._target_resolution[0])
        .set_position("center")
        .set_fps(self._fps)
        .set_start(scene.start_time - 1)
    )
    animation_details = scene.animation.split("_")
    match animation_details[0]:
      case "zoom":
        return effects.zoom(
            clip,
            direction=animation_details[1],
            fast=True if animation_details[2] == "fast" else False,
        )
      case "slide":
        return effects.slide(clip, direction=animation_details[1])
      case "panto":
        w, h = clip.size
        target_bbox = np.float32(scene.focal_point) / 1000
        target = (
            w * (target_bbox[1] + target_bbox[3]) / 2,
            h * (target_bbox[0] + target_bbox[2]) / 2,
        )
        return effects.zoom_pan_to(
            clip,
            target=target,
            fast=True if animation_details[1] == "fast" else False,
        )
      case _:
        # No animation
        return clip

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
    number_of_scenes = len(storyboard.scenes)
    if number_of_scenes == 0:
      raise video_generation_errors.NoImagesFoundError()

    audio_clip = mpy.AudioFileClip(storyboard.main_audio_path)
    audio_file_length = audio_clip.duration

    self._logger.info("Generating video output_video_path from:")
    self._logger.info("\tWith %s s duration", audio_file_length)
    self._logger.info("\t%i scenes:", number_of_scenes)

    clips = []
    # Add the scenes
    for i, scene in enumerate(
        sorted(storyboard.scenes, key=lambda s: s.start_time)
    ):
      self._logger.info("\t-%s", scene.image_path)
      next_scene_start_time = (
          100_000_000
          if i < len(storyboard.scenes)
          else storyboard.scenes[i + 1].start_time
      )
      clip_end_time = min(next_scene_start_time, audio_file_length)
      if scene.start_time < clip_end_time:
        clips.append(
            self.create_scene(
                scene, duration=clip_end_time - scene.start_time + 1
            )
        )
      else:
        break

    # Add the TextOverlays
    video_width, video_height = self._target_resolution
    for text_overlay_obj in storyboard.text_overlays:
      text_overlay_video_clip = create_text_overlay_video_clip(
          video_width, video_height, text_overlay_obj
      )
      clips.append(text_overlay_video_clip)

    if storyboard.logo_path:
      clips.append(
          mpy.ImageClip(storyboard.logo_path, duration=audio_clip.duration)
          .resize(width=50)
          .set_pos(("right", "top"))
          .margin(right=_LOGO_MARGIN, top=_LOGO_MARGIN, opacity=0)
      )

    composite_video = mpy.CompositeVideoClip(
        clips, size=self._target_resolution
    ).set_audio(audio_clip)
    composite_video.write_videofile(self._output_path)

    audio_clip.close()
    composite_video.close()
    for clip in clips:
      clip.close()

    return self._output_path
