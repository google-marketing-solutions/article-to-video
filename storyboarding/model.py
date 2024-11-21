"""Model classes for Storyboarding."""

import dataclasses
from typing import Literal, Optional, Tuple

ImageAnimation = Literal[
    "zoom_in_slow",
    "zoom_in_fast",
    "zoom_out_slow",
    "zoom_out_fast",
    "slide_left",
    "slide_right",
    "slide_up",
    "slide_down",
    "panto_slow",
    "panto_fast",
    "static",
]


@dataclasses.dataclass
class Scene:
  """A Scene composed from a static image.

  Attributes:
    start_time: The start time in the larger timeline for the Scene.
    image_path: The path to the image.
    animation: An animation to apply to the static image.
    main_subject: A bounding box, with coordinates normalized to 1000,
      representing the main area subject for the image. Defaults to the entire
      image.
    focal_point: A bounding box, with coordinates normalized to 1000,
      representing the main focal point for the image. The center of the
      bounding box should be considered the focal point. Default focal point is
      the center of the image.
  """

  start_time: float
  image_path: str
  animation: ImageAnimation = "static"
  main_subject: list[float] = dataclasses.field(
      default_factory=lambda: [0.0, 0.0, 1000.0, 1000.0]
  )
  focal_point: list[float] = dataclasses.field(
      default_factory=lambda: [0.0, 0.0, 1000.0, 1000.0]
  )


@dataclasses.dataclass
class TextOverlay:
  """Class to handle text that will be overlaid onto the video."""

  start_time: float
  end_time: float
  text: str
  speaker: Optional[str] = None
  transition_in: Optional[str] = None
  transition_out: Optional[str] = None
  font_style: str = "Helvetica"
  font_size: int = 24
  background_color: str = "black"
  alignment: str = "West"
  position: Tuple[str, str] = ("center", "center")
  method: str = "label"
  text_w: Optional[int] = None
  text_h: Optional[int] = None
  _font_color: Optional[str] = None

  @property
  def font_color(self) -> str:
    if self._font_color is None:
      self._font_color = self.calculate_text_color(self.background_color)
    return self._font_color

  @font_color.setter
  def font_color(self, value: str):
    self._font_color = value

  def calculate_text_color(self, background_hex_color: str) -> str:
    """Determine black or white for text font against a given background color.

    This function calculates the luminance of a color specified in hexadecimal
    format
    and returns "black" if the luminance is greater than 0.5 (indicating a
    lighter background),
    and "white" otherwise (for darker backgrounds).

    Args:
        background_hex_color: The background color in hexadecimal format (e.g.,
          "#RRGGBB").

    Returns:
        The optimal text color, either "black" or "white".

    Raises:
        ValueError: If the input `background_hex_color` is not a valid
        hexadecimal color string.
    """
    if background_hex_color is None:
      return "white"
    try:
      # Gets two letters at a time e.g. "RR" and then the next two, etc. and
      # converts them into integers from base-16
      r, g, b = (int(background_hex_color[i : i + 2], 16) for i in (1, 3, 5))
      luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
      return "black" if luminance > 0.5 else "white"
    except ValueError:
      print("Warning: Invalid hex color format; using white text color.")
      return "white"


@dataclasses.dataclass
class Storyboard:
  scenes: list[Scene]
  main_audio_path: str
  background_audio_path: Optional[str] = None
  text_overlays: list[TextOverlay] = dataclasses.field(default_factory=list)
  logo_path: Optional[str] = None
