import unittest
from unittest import mock

from audio import create_final_audio_step
from moviepy import editor as mpy
import moviepy.audio.fx.all as afx
import numpy as np
import parameterized
import storyboarding


class CreateFinalAudioStepTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.output_path = 'output/path/audio.mp3'
    self.final_audio_step = create_final_audio_step.CreateFinalAudioStep(
        self.output_path
    )
    self.storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.ImageScene(
                image_path='input_images/image1.jpg', start_time=0
            )
        ],
        main_audio_path='/my/narration_audio',
        background_audio_path='/my/background_audio',
    )
    self.narration_volume = (
        create_final_audio_step.CreateFinalAudioStep._NARRATION_VOLUME
    )
    self.background_volume = (
        create_final_audio_step.CreateFinalAudioStep._BACKGROUND_VOLUME
    )

  def _setup_mock_audio_clips(
      self, mock_audiofileclip, narration_duration, background_duration
  ):
    mock_narration_audio = mpy.AudioClip(
        lambda t: 2 * [np.sin(440 * 2 * np.pi * t)], duration=narration_duration
    )
    mock_background_audio = mpy.AudioClip(
        lambda t: 2 * [np.sin(440 * 2 * np.pi * t)],
        duration=background_duration,
    )
    mock_audiofileclip.side_effect = [
        mock_narration_audio,
        mock_background_audio,
    ]
    return mock_narration_audio, mock_background_audio

  def _assert_volumex_calls(self, mock_narration_audio, mock_background_audio):
    narration_volume = (
        create_final_audio_step.CreateFinalAudioStep._NARRATION_VOLUME
    )
    background_volume = (
        create_final_audio_step.CreateFinalAudioStep._BACKGROUND_VOLUME
    )
    self.mock_volumex.assert_has_calls([
        mock.call(mock_narration_audio, narration_volume),
        mock.call(mock_background_audio, background_volume),
    ])

  @mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(afx, 'audio_fadeout', autospec=True)
  @mock.patch.object(mpy, 'AudioFileClip')
  def test_final_audio_path_returned(self, *_):

    mock_audio_fadeout = afx.audio_fadeout
    mock_final_audio = mock_audio_fadeout.return_value
    mock_final_audio.write_audiofile.return_value = self.output_path

    result_audio_path = self.final_audio_step.process(self.storyboard)
    mock_audio_fadeout.assert_called_once()
    mock_final_audio.write_audiofile.assert_called_once_with(
        filename=self.output_path, fps=44100
    )
    self.assertEqual(self.output_path, result_audio_path)

  @parameterized.parameterized.expand([
      ('extend_background', 15, 10, True),  # Narration longer than background
      ('trim_background', 15, 20, False),  # Narration shorter than background
  ])
  @mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(afx, 'audio_fadeout', autospec=True)
  @mock.patch.object(afx, 'volumex', autospec=True)
  @mock.patch.object(afx, 'audio_loop', autospec=True)
  @mock.patch.object(mpy, 'CompositeAudioClip', autospec=True)
  @mock.patch.object(mpy, 'AudioFileClip')
  def test_adjust_audio_clip_durations(
      self,
      _,
      narration_duration,
      background_duration,
      extend_background,
      mock_audiofileclip,
  ):

    mock_narration_audio, mock_background_audio = self._setup_mock_audio_clips(
        mock_audiofileclip, narration_duration, background_duration
    )

    mock_audio_loop = afx.audio_loop
    self.mock_volumex = afx.volumex
    mock_audio_fadeout = afx.audio_fadeout
    mock_composite_audio = mock_audio_fadeout.return_value
    mock_composite_audio.write_audiofile.return_value = self.output_path

    self.final_audio_step.process(self.storyboard)

    if extend_background:
      mock_audio_loop.assert_called_once()
    else:
      mock_audio_loop.assert_not_called()

    self._assert_volumex_calls(mock_narration_audio, mock_background_audio)
    mock_audio_fadeout.assert_called_once()
    mock_composite_audio.write_audiofile.assert_called_once_with(
        filename=self.output_path, fps=44100
    )


if __name__ == '__main__':
  unittest.main()
