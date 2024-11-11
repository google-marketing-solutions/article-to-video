"""Video generation pipeline step for generating the base video from images."""

import logging
import cv2
from moviepy import editor as mpy
import numpy as np
import pipeline
import storyboarding
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
      ken_burns: bool = True,
  ):
    self._logger = logging.getLogger(self.__class__.__name__)
    self._output_path = output_path
    self._target_resolution = target_resolution
    self._fps = fps
    self._ken_burns = ken_burns

  def _apply_ken_burns(
      self,
      clip: mpy.ImageClip,
      focal_point_bbox: list[str] = None,
      speed: int = 1,
  ) -> mpy.ImageClip:
    """Apply a "Ken Burns" stlye animation to add motion to a static image.

    The current implementation zooms slowly while panning towards the focal
    point of the image, as defined by the focal_point_bbox. If no bounding box
    is provided for the focal point, the zoom/pan will move towards
    the center of the image.

    Args:
      clip: The moviepy ImageClip to animate.
      focal_point_bbox: A bounding box around the focal point of the image. The
        bounding box should have coordinates normalized to 1000, and be in the
        format [ymx, xmin, ymax, xmax]. Defaults to include the entire image.
      speed: The speed to zoom in during the animation. Defaults to 1.

    Returns:
      The animated image clip.
    """
    focal_point_bbox = focal_point_bbox or [0, 0, 1000, 1000]
    duration = clip.duration
    ymin, xmin, ymax, xmax = np.array(focal_point_bbox) / 1000

    def filter_frame(get_frame, t):
      """Calculates the appropriate zoom/pan for a given frame in the video."""
      frame = get_frame(t)
      h, w = frame.shape[:2]

      # Calculate the zoom factor
      zoom = 1 + (t * speed / duration)

      # Calculate center of the focal point bbox
      bbox_center_x = w * (xmin + xmax) / 2
      bbox_center_y = h * (ymin + ymax) / 2

      # Calculate translation to move focal point towards center of screen
      # during zoom
      dx = bbox_center_x - (bbox_center_x * zoom)
      dy = bbox_center_y - (bbox_center_y * zoom)

      transform_matrix = np.array([
          [zoom, 0, dx],  # [x_scale, x_rotate, x_shift]
          [0, zoom, dy],  # [y_scale, y_rotate, y_shift]
      ])
      return cv2.warpAffine(frame, transform_matrix, (w, h))

    return clip.fl(filter_frame)

  def _render_image_scene(
      self, scene: storyboarding.ImageScene, duration: float
  ) -> mpy.ImageClip:
    """Converts a ImageScene storyboard skeleton into an ImageClip.

    Args:
      scene: The ImageScene to render.
      duration: The desired length of the ImageScene.

    Returns:
      A moviepy ImageClip.
    """
    clip = (
        mpy.ImageClip(
            scene.image_path,
            duration=duration,
        )
        .resize(width=self._target_resolution[0])
        .set_fps(self._fps)
        .set_start(scene.start_time - 1)
    )
    if self._ken_burns:
      # Apply the Ken Burns effect (zoom, pan, fade)
      clip = clip.fx(
          self._apply_ken_burns, focal_point_bbox=scene.focal_point
      ).crossfadein(1.0)
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
      if isinstance(scene, storyboarding.ImageScene):
        self._logger.info("\t-%s", scene.image_path)
        clip_end_time = (
            audio_file_length
            if i + 1 == len(storyboard.scenes)
            else storyboard.scenes[i + 1].start_time
        )
        if scene.start_time < clip_end_time:
          clips.append(
              self._render_image_scene(
                  scene, duration=clip_end_time - scene.start_time + 1
              )
          )
        else:
          break
      else:
        raise NotImplementedError(
            "Requested scene type is currently unsupported."
        )

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
