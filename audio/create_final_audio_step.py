"""Pipeline step to create final audio for video."""

import logging
import math
from moviepy import editor as mpy
import moviepy.audio.fx.all as afx
import storyboarding


class CreateFinalAudioStep:
  """Pipeline step to combine background and narration audio."""

  _FADE_OUT_DURATION = 3
  _NARRATION_VOLUME = 2.0
  _BACKGROUND_VOLUME = 0.1

  def __init__(self, output_path: str):
    self._logger = logging.getLogger(self.__class__.__name__)
    self._output_path = output_path

  def process(self, storyboard: storyboarding.Storyboard) -> str:
    """Combine background audio and narration audio from storyboard filepaths.

    Args:
        storyboard: The storyboard on which to base the generation.

    Returns:
        A string with the output file path.
    """
    narration_audio_clip = mpy.AudioFileClip(storyboard.main_audio_path)
    background_audio_clip = mpy.AudioFileClip(storyboard.background_audio_path)
    composite_audio_clip = self._adjust_audio_clips(
        main_audio=narration_audio_clip, background_audio=background_audio_clip
    )
    final_audio = afx.audio_fadeout(
        composite_audio_clip, self._FADE_OUT_DURATION
    )
    final_audio.write_audiofile(filename=self._output_path, fps=44100)

    # Close all audio clips
    narration_audio_clip.close()
    background_audio_clip.close()
    composite_audio_clip.close()
    return self._output_path

  def _adjust_audio_clips(
      self, main_audio: mpy.AudioFileClip, background_audio: mpy.AudioFileClip
  ) -> mpy.CompositeAudioClip:
    # Adjust narration audio to be louder and add in a buffer for audio
    # fade out
    narration_audio_length = int(
        math.ceil(main_audio.duration) + self._FADE_OUT_DURATION
    )
    loud_narration_audio = afx.volumex(main_audio, self._NARRATION_VOLUME)
    # Ensure correct duration is set on audio clip copy
    loud_narration_audio.set_duration = narration_audio_length

    # Adjust background audio to be quieter than the main audio
    background_audio_length = background_audio.duration
    soft_background_audio = afx.volumex(
        background_audio, self._BACKGROUND_VOLUME
    )

    # Adjust background audio length to match main audio length
    if narration_audio_length > background_audio_length:
      self._logger.info(
          "Looping background audio to match narration duration of %i seconds",
          narration_audio_length,
      )
      sized_background_audio = afx.audio_loop(
          soft_background_audio, duration=narration_audio_length
      )
    else:
      self._logger.info(
          "Trimming background audio to match narration duration of %i seconds",
          narration_audio_length,
      )
      sized_background_audio = soft_background_audio.subclip(
          0, narration_audio_length
      )

    # Combine audio clips
    self._logger.info("Composing background and narration audio")
    composite_audio_clip = mpy.CompositeAudioClip(
        [loud_narration_audio, sized_background_audio]
    )

    return composite_audio_clip
