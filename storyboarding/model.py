"""Model classes for Storyboarding."""

import dataclasses
from typing import Optional


@dataclasses.dataclass
class Scene:
  start_time: float
  background_image_path: str


@dataclasses.dataclass
class Storyboard:
  scenes: list[Scene]
  main_audio_path: str
  background_audio_path: Optional[str] = None
