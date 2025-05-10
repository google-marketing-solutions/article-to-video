"""Video generation pipeline step for generating the base video from images."""

import logging
from audio import create_final_audio_step
from moviepy import editor as mpy
from moviepy.video.tools import subtitles as mpy_subtitles
import numpy as np
import storyboarding
from video import effects
from video import video_generation_errors
from video.create_text_overlay_step import (create_text_overlay_video_clip)

_LOGO_MARGIN = 16  # pixels


class GenerateVideoFromImagesStep:
  """Class that will stitch together the input images to generate base video."""

  def __init__(
      self,
      output_audio_path: str,
      output_video_path: str,
      burn_in_subtitles: bool = False,
      target_resolution: tuple[int, int] = (1280, 720),
      fps: int = 25,
  ):
    self._logger = logging.getLogger(self.__class__.__name__)
    self._output_audio_path = output_audio_path
    self._output_video_path = output_video_path
    self._target_resolution = target_resolution
    self._fps = fps
    self._burn_in_subtitles = burn_in_subtitles

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
        .set_start(max(scene.start_time_seconds - 1, 0))
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

    final_audio_step = create_final_audio_step.CreateFinalAudioStep(
        self._output_audio_path
    )
    self._logger.info("Generating final audio")
    audio_clip_path = final_audio_step.process(storyboard)
    audio_clip = mpy.AudioFileClip(audio_clip_path)
    audio_file_length = audio_clip.duration

    self._logger.info("Generating video output_video_path from:")
    self._logger.info("\tWith %s s duration", audio_file_length)
    self._logger.info("\t%i scenes:", number_of_scenes)

    clips = []
    # Add the scenes
    ordered_scenes = sorted(storyboard.scenes, key=lambda s: s.start_time)
    for i, scene in enumerate(ordered_scenes):
      self._logger.info("\t-%s", scene.image_path)
      next_scene_start_time = (
          100_000_000
          if i + 1 >= len(storyboard.scenes)
          else storyboard.scenes[i + 1].start_time_seconds
      )
      clip_end_time = min(next_scene_start_time, audio_file_length)
      if scene.start_time_seconds < clip_end_time:
        clips.append(
            self.create_scene(
                scene, duration=clip_end_time - scene.start_time_seconds + 1
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
          .set_position(("right", "top"))
          .margin(right=_LOGO_MARGIN, top=_LOGO_MARGIN, opacity=0)
      )

    if self._burn_in_subtitles:
      subtitles = mpy_subtitles.SubtitlesClip(
          storyboard.srt_path,
          lambda text: mpy.TextClip(
              text,
              font="Helvetica-Bold",
              fontsize=32,
              color="white",
              stroke_color="black",
              stroke_width=1.0,
          ),
      )
      subtitle_bottom_margin = self._target_resolution[1] - 32 - 64
      subtitles = subtitles.set_position(("center", subtitle_bottom_margin))
      clips.append(subtitles)

    composite_video = mpy.CompositeVideoClip(
        clips, size=self._target_resolution
    ).set_audio(audio_clip)
    composite_video.write_videofile(self._output_video_path)

    audio_clip.close()
    composite_video.close()
    for clip in clips:
      clip.close()

    return self._output_video_path

  def __call__(self, storyboard: storyboarding.Storyboard) -> str:
    return self.process(storyboard)
