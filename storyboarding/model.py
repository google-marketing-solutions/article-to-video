"""Model classes for Storyboarding."""

import dataclasses
import datetime
import time
from typing import Literal, Optional, Tuple

ImageAnimation = Literal[
    "zoom_in_slow",
    "zoom_out_slow",
    "zoom_out_fast",
    "slide_left",
    "slide_right",
    "slide_up",
    "slide_down",
    "panto_slow",
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
    justification: a rationale provided by the LLM as to why a scene was
      constructed as such. Useful for debugging.
  """

  start_time: str
  image_path: str
  animation: ImageAnimation = "static"
  main_subject: list[float] = dataclasses.field(
      default_factory=lambda: [0.0, 0.0, 1000.0, 1000.0]
  )
  focal_point: list[float] = dataclasses.field(
      default_factory=lambda: [0.0, 0.0, 1000.0, 1000.0]
  )
  justification: Optional[str] = None

  @property
  def start_time_seconds(self) -> float:
    """Returns the timestamp in seconds."""

    if not self.start_time:
      return 0
    else:
      x = time.strptime(self.start_time.split(",")[0], "%H:%M:%S")
      start_time_seconds = datetime.timedelta(hours=x.tm_hour,
                                              minutes=x.tm_min,
                                              seconds=x.tm_sec).total_seconds()
      return start_time_seconds


@dataclasses.dataclass
class TextOverlay:
  """Class to handle text that will be overlaid onto the video."""

  start_time: float
  end_time: float
  text: str
  speaker: Optional[str] = None
  transition_in: Optional[str] = None
  transition_out: Optional[str] = None
  font_style: str = "Verdana-Bold"
  font_size: int = 40
  background_color: str = "rgba(0, 0, 0, 0.5)"
  font_color: str = "white"
  alignment: str = "West"
  position: Tuple[str, str] = ("center", "center")
  method: str = "label"
  text_w: Optional[int] = None
  text_h: Optional[int] = None


@dataclasses.dataclass
class Storyboard:
  scenes: list[Scene]
  main_audio_path: str
  srt_path: str
  background_audio_path: Optional[str] = None
  text_overlays: list[TextOverlay] = dataclasses.field(default_factory=list)
  logo_path: Optional[str] = None
