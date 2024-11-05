"""Steps to for Storyboard creation."""

from moviepy import editor as mpy
import storyboarding


# TODO(cfeldman): Adapt this into a pipeline or other more advanced
# implementation to support more complex storyboarding (ie with Gemini).
def create_storyboard_step(
    image_file_paths: list[str], audio_file_path: str
) -> storyboarding.Storyboard:
  """Creates simple storyboards.

  This is a dead simple first version that defines the storyboard for a
  slideshow of evenly spaced images with an audio track overlay.

  Args:
    image_file_paths: a list of image to be used as background images
    audio_file_path: the main audio file

  Returns:
    A Storyboard.
  """
  # TODO(cfeldman): Ideally, the duration would be passed in instead of
  # calculated. Maybe we can get the duration from the TTS response.
  with mpy.AudioFileClip(audio_file_path) as audio_clip:
    duration = audio_clip.duration
  each_image_duration = duration / len(image_file_paths)
  return storyboarding.Storyboard(
      scenes=[
          storyboarding.Scene(
              background_image_path=path,
              start_time=each_image_duration * i,
          )
          for i, path in enumerate(image_file_paths)
      ],
      main_audio_path=audio_file_path,
  )
