"""Video effects for applying motion to images."""

import math
from typing import Callable, Literal, Protocol
import cv2
from moviepy import editor as mpy
import numpy as np

AnimationStyle = Literal["linear", "fast"]


class _SupportsMultiplication(Protocol):

  def __mul__(self, other):
    ...


def _lerp(
    start: _SupportsMultiplication, end: _SupportsMultiplication, t: float
):
  """Linear interpolation between start and end at time t.

  Args:
    start: Starting value.
    end: Ending value.
    t: Time ratio between 0 and 1.

  Returns:
    The interpolated value.
  """
  return (start * (1 - t)) + (end * t)


def _exp_ease_out(t: float):
  """Exponential ease-out.

  Apply to time ratio before linear interpolation to make the interpolation
  "fast" at the beginning before slowing down.

  Args:
    t: Time ratio between 0 and 1.

  Returns:
    The eased-out time ratio.
  """
  return 1 if t == 1 else 1 - math.pow(2, -10 * t)


def zoom_pan(
    clip: mpy.ImageClip,
    initial_zoom: float = 1.0,
    final_zoom: float | None = None,
    initial_position: tuple[float, float] = (0.0, 0.0),
    final_position: tuple[float, float] | None = None,
    duration: float = None,
    style: AnimationStyle = "linear",
) -> mpy.VideoClip:
  """Applies zoom and pan effects to a video clip.

  The position is interpolated against the zoom level to ensure a smooth
  animation.

  Args:
    clip: The input video clip.
    initial_zoom: The initial zoom level.
    final_zoom: The final zoom level. If None, defaults to initial_zoom.
    initial_position: The initial position (x, y).
    final_position: The final position (x, y). If None, defaults to
      initial_position.
    duration: The duration of the effect. If None, uses the clip's duration.
    style: The animation style, either "linear" or "fast".

  Returns:
    The transformed video clip.

  Raises:
    ValueError: If an invalid interpolation type is provided.
  """
  duration = duration or clip.duration

  initial_position = np.float32(initial_position)
  final_position = (
      np.float32(final_position)
      if final_position is not None
      else initial_position
  )
  final_zoom = final_zoom or initial_zoom

  def frame_filter(get_frame: Callable[[float], np.ndarray], t: float):
    """Applies zoom and pan to a frame at time t.

    Args:
      get_frame: Function to get the original frame at time t.
      t: Current time in the video.

    Returns:
      The transformed frame as a NumPy array.
    """
    frame = get_frame(t)
    if style == "fast":
      time_ratio = _exp_ease_out(t / duration)
    else:
      time_ratio = t / duration
    scale = _lerp(initial_zoom, final_zoom, time_ratio)
    # Find the ratio of the current zoom compared to the final zoom. This is
    # used as the interpolation ratio for panning to ensure a smooth animtation.
    #
    # If there is no interpolation, translate based on the time ratio.
    scale_ratio = (
        time_ratio
        if final_zoom == initial_zoom
        else (scale - initial_zoom) / (final_zoom - initial_zoom)
    )
    translate = -_lerp(
        initial_position * initial_zoom,
        final_position * final_zoom,
        scale_ratio,
    )

    matrix = cv2.getRotationMatrix2D((0, 0), 0, scale)
    matrix[:, 2] += translate

    return cv2.warpAffine(frame, matrix, clip.size)

  return clip.fl(frame_filter)


def slide(
    clip: mpy.ImageClip,
    direction: Literal["left", "right", "up", "down"],
) -> mpy.VideoClip:
  """Applies a slide effect to the clip.

  Args:
    clip: The input video clip.
    direction: The direction of the slide ("left", "right", "up", "down").

  Returns:
    The transformed video clip.

  Raises:
    ValueError: for unsupported direction.
  """
  scale = 1.25
  w, h = np.float32(clip.size)
  # maximum x, y offets to keep the image in the bounds of the viewport.
  offset_x = (scale - 1) * w / scale
  offset_y = (scale - 1) * h / scale

  match direction:
    case "right":
      position_start = (offset_x, offset_y / 2)
      position_end = (0, offset_y / 2)
    case "left":
      position_start = (0, offset_y / 2)
      position_end = (offset_x, offset_y / 2)
    case "down":
      position_start = (offset_x / 2, offset_y)
      position_end = (offset_x / 2, 0)
    case "up":
      position_start = (offset_x / 2, 0)
      position_end = (offset_x / 2, offset_y)
    case _:
      raise ValueError("Unsupported direction:", direction)
  return zoom_pan(
      clip,
      initial_zoom=scale,
      initial_position=position_start,
      final_position=position_end,
  )


def zoom(
    clip: mpy.ImageClip, direction: Literal["in", "out"], fast: bool = False
) -> mpy.VideoClip:
  """Applies a zoom effect to the clip.

  Args:
    clip: The input video clip.
    direction: The direction of the zoom ("in", "out").
    fast: Whether to use fast interpolation.

  Returns:
    The transformed video clip.
  """
  min_zoom = 1.0
  max_zoom = 1.5
  min_zoom_pos = np.float32([0, 0])
  max_zoom_pos = (max_zoom - 1) * np.float32(clip.size) / max_zoom / 2
  return zoom_pan(
      clip,
      initial_position=min_zoom_pos if direction == "in" else max_zoom_pos,
      final_position=max_zoom_pos if direction == "in" else min_zoom_pos,
      initial_zoom=min_zoom if direction == "in" else max_zoom,
      final_zoom=max_zoom if direction == "in" else min_zoom,
      style="fast" if fast else "linear",
  )


def zoom_pan_to(
    clip: mpy.ImageClip, target: tuple[float, float], fast: bool = False
) -> mpy.VideoClip:
  """Pans to a specific target within the clip.

  The target will be the center of the viewport at the end of the pan.

  Args:
      clip: The input video clip.
      target: The (x, y) coordinates of the target.
      fast: If true, animation will start fast and finish slow. Defaults to
        false.

  Returns:
      The transformed video clip.
  """
  target = np.float32(target)
  if np.any(target >= clip.size):
    raise ValueError("Target must be inside image bounds.")

  w, h = np.float32(clip.size)
  distance_to_top_left = abs(np.float32((0, 0)) - target)
  distance_to_bottom_right = abs(np.float32(clip.size) - target)
  min_edge_distances = (
      min(distance_to_top_left[0], distance_to_bottom_right[0]),
      min(distance_to_top_left[1], distance_to_bottom_right[1]),
  )
  # Find the minimum scaling required to get the target to the center of the
  # viewport without black bars on screen.
  # Always zoom to at least 1.5x
  scale = max(
      1.5,
      w / (2 * min_edge_distances[0]),
      h / (2 * min_edge_distances[1]),
  )
  # Calculate the position (without any scaling) where the target is in the
  # center of the frame.
  adj_final_position = np.array(target) - np.array(clip.size) / 4
  return zoom_pan(
      clip,
      initial_zoom=1.0,
      final_zoom=scale,
      initial_position=(0, 0),
      final_position=adj_final_position,
      style="fast" if fast else "linear",
  )
