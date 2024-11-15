"""Video generation pipeline step for adding article title to video."""

import enum
from typing import Tuple

from moviepy.editor import TextClip
from moviepy.editor import VideoClip
from storyboarding.model import TextOverlay


class Transition(enum.Enum):
  """Enum for transition effects."""

  FADE_IN = "fade_in"
  FADE_OUT = "fade_out"
  SLIDE_FROM_LEFT = "slide_from_left"
  SLIDE_FROM_RIGHT = "slide_from_right"
  SLIDE_FROM_BOTTOM = "slide_from_bottom"


def get_pixel_position(
    video_width: int,
    video_height: int,
    overlay: TextOverlay,
    text_clip: TextClip,
) -> Tuple[int, int]:
  """Converts position keywords in the TextOverlay obj to pixel coordinates.

  This function supports intuitive keywords (e.g., "center", "top", "bottom")
  for positioning text clips within a video frame. Keywords in overlay.position
  are dynamically converted into pixel coordinates, taking into account the
  video dimensions and the size of the text clip.

  Args:
      video_width: The width in pixels of the video.
      video_height: The height in pixels of the video.
      overlay: An object that contains overlay properties, including position,
        video_width, and video_height, among others.
      text_clip: The MoviePy TextClip object, which provides the width and
        height of the text to calculate accurate positioning.

  Returns:
      Tuple: The (x, y) coordinates in pixels where the text clip
      should be positioned within the video frame.

  Position Keywords:
      - "center": Centers the text horizontally or vertically.
      - "left": Aligns text to the left side, with a slight margin from the
      edge.
      - "right": Aligns text to the right side, with a slight margin from the
      edge.
      - "top": Aligns text at the top, with a slight margin from the
      edge.
      - "bottom": Aligns text at the bottom, with a slight margin from the
      edge.

  Notes:
      - If x or y in overlay.position is already a numeric value, it
      will be used as-is.
      - Adjusts for the text clip's dimensions to ensure proper alignment when
      using keywords like "center".
  """
  x, y = overlay.position
  if isinstance(x, str):
    x = x.lower()
    if x == "center":
      x = video_width // 2 - text_clip.w // 2
    elif x == "left":
      x = int(0.1 * video_width)
    elif x == "right":
      x = int(0.9 * video_width - text_clip.w)

  if isinstance(y, str):
    y = y.lower()
    if y == "center":
      y = video_height // 2 - text_clip.h // 2
    elif y == "top":
      y = int(0.1 * video_height)
    elif y == "bottom":
      y = int(0.9 * video_height - text_clip.h)
  return x, y


def apply_transition(
    video_width: int,
    video_height: int,
    text_clip: TextClip,
    overlay: TextOverlay,
    slide_duration=2,
) -> VideoClip:
  """Applies the specified transition effects (in & out) to a MoviePy text clip.

  Args:
      video_width: The width in pixels of the video.
      video_height: The height in pixels of the video.
      text_clip: The MoviePy text clip to apply transitions to.
      overlay:  Contains overlay properties.
      slide_duration: Duration of slide and transition animations in seconds.

  Returns:
      VideoClip: The transformed VideoClip with transition effects applied.

  Raises:
      ValueError: If `slide_duration` is not positive or invalid transition
      type is provided.
  """
  if slide_duration <= 0:
    raise ValueError("slide_duration must be a positive number.")

  # Validate transition_in
  try:
    transition_in = (
        Transition(overlay.transition_in.lower())
        if overlay.transition_in
        else None
    )
  except ValueError as exc:
    raise ValueError(
        f"Invalid transition_in type: {overlay.transition_in.lower()}. Must be"
        f" one of {[t.value for t in Transition]}"
    ) from exc
  # Validate transition_out
  try:
    transition_out = (
        Transition(overlay.transition_out.lower())
        if overlay.transition_out
        else None
    )
  except ValueError as exc:
    raise ValueError(
        f"Invalid transition_out type: {overlay.transition_out.lower()}. Must"
        f" be one of {[t.value for t in Transition]}"
    ) from exc

  end_position = get_pixel_position(
      video_width, video_height, overlay, text_clip
  )
  transition_in_functions = {
      Transition.SLIDE_FROM_LEFT: lambda: (-text_clip.w, end_position[1]),
      Transition.SLIDE_FROM_RIGHT: lambda: (
          video_width,
          end_position[1],
      ),
      Transition.SLIDE_FROM_BOTTOM: lambda: (
          end_position[0],
          video_height,
      ),
  }

  # Apply transition_in
  transition_in_func = transition_in_functions.get(transition_in)

  if transition_in == Transition.FADE_IN:
    text_clip = text_clip.fadein(slide_duration).set_position(end_position)

  elif transition_in_func:
    start_position = (
        transition_in_func() if callable(transition_in_func) else None
    )
    if start_position:  # Apply position change for sliding transitions

      def translate(t):
        if t <= slide_duration:
          x = start_position[0] + t / slide_duration * (
              end_position[0] - start_position[0]
          )
          y = start_position[1] + t / slide_duration * (
              end_position[1] - start_position[1]
          )
        else:
          x, y = end_position
        return (x, y)

      text_clip = text_clip.set_position(translate)

  # Apply transition_out using `set_start`
  if transition_out == Transition.FADE_OUT:
    text_clip = text_clip.set_end(overlay.end_time - slide_duration).fadeout(
        slide_duration
    )

  return text_clip


def wrap_text_by_words(text: str, words_per_line: int) -> str:
  """Wrap text such that only a specified number of words appear per line.

  Args:
      text: The input text to wrap.
      words_per_line: The number of words to include per line.

  Returns:
      str: The wrapped text.
  """
  words = text.split()

  # Use list comprehension to group words into lines
  lines = [
      " ".join(words[i : i + words_per_line])
      for i in range(0, len(words), words_per_line)
  ]

  # Join the lines with newlines for the final wrapped text
  return "\n".join(lines)


def create_text_overlay_video_clip(
    video_width: int, video_height: int, text_overlay: TextOverlay
) -> TextClip:
  """Generates a VideoClip with text overlay and transition effects applied.

  This function takes a TextOverlay object as input, creates a
  TextClip with the specified properties (text, font size, color, alignment,
  etc.), and applies entry and exit transition effects based on the overlay
  settings. The resulting VideoClip can be used as a layer in a composite video.

  Args:
      video_width: The width in pixels of the video.
      video_height: The height in pixels of the video.
      text_overlay: The TextOverlay object containing the overlay properties
        such as text, start and end times, font specifications, background
        color, and transition types.

  Returns:
      VideoClip: A VideoClip with the text overlay and transitions applied.

  Raises:
      ValueError: If the specified transitions are invalid or the slide
      duration is negative.
  """
  # method="label" auto-sizes
  size = (
      (text_overlay.text_w, text_overlay.text_h)
      if text_overlay.method == "caption"
      else None
  )
  if text_overlay.method is None:
    text_overlay.method = "label"
  # Create the text clip with specific styles
  text_clip = (
      TextClip(
          wrap_text_by_words(text_overlay.text, 6),
          fontsize=text_overlay.font_size or 30,
          font="Helvetica",
          color=text_overlay.font_color,
          bg_color=text_overlay.background_color,
          method=text_overlay.method,
          align=text_overlay.alignment,
          interline=-1,
          size=size,
      )
      .set_start(text_overlay.start_time)
      .set_duration(text_overlay.end_time - text_overlay.start_time)
  )
  # Apply transition or static position
  video_clip = apply_transition(
      video_width, video_height, text_clip, text_overlay, slide_duration=2
  )

  # Return the VideoClip (to be added to the video in the broader
  # pipeline)
  return video_clip
