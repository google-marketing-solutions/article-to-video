import unittest
from unittest import mock

from audio import create_final_audio_step
from moviepy import editor as mpy
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
            storyboarding.Scene(
                image_path='input_images/image1.jpg', start_time='0'
            )
        ],
        main_audio_path='/my/narration_audio.mp3',
        background_audio_path='/my/background_audio.wav',
        srt_path='my/srt/path',
    )
    self.fade_duration = (
        create_final_audio_step.CreateFinalAudioStep._FADE_OUT_DURATION
    )
    self.fps = 44100

  @mock.patch.object(
      create_final_audio_step.mpy, 'CompositeAudioClip', autospec=True
  )
  @mock.patch.object(create_final_audio_step.afx, 'audio_loop', autospec=True)
  @mock.patch.object(create_final_audio_step.afx, 'volumex', autospec=True)
  @mock.patch.object(
      create_final_audio_step.afx, 'audio_fadeout', autospec=True
  )
  @mock.patch.object(
      create_final_audio_step.mpy, 'AudioFileClip', autospec=True
  )
  def test_final_audio_path_returned(
      self,
      mock_audio_file_clip,
      mock_audio_fadeout,
      mock_volumex,
      mock_audio_loop,
      mock_composite_audio_clip,
  ):
    """Tests that the process method runs and returns the correct output path."""
    mock_narration_clip_instance = mock.MagicMock()
    mock_narration_clip_instance.duration = 10.0
    mock_narration_clip_instance.close = mock.Mock()

    mock_background_clip_instance = mock.MagicMock()
    mock_background_clip_instance.duration = 15.0
    mock_background_clip_instance.close = mock.Mock()

    mock_audio_file_clip.side_effect = (
        lambda path: mock_narration_clip_instance
        if path == self.storyboard.main_audio_path
        else mock_background_clip_instance
    )

    mock_volumex_output_clip = mock.MagicMock(spec=mpy.AudioClip)
    mock_volumex_output_clip.set_duration.return_value = (
        mock_volumex_output_clip
    )
    mock_volumex_output_clip.subclip.return_value = mock.MagicMock(
        spec=mpy.AudioClip
    )
    mock_volumex.return_value = mock_volumex_output_clip

    mock_audio_loop.return_value = mock.MagicMock(spec=mpy.AudioClip)

    mock_composite_instance = mock.MagicMock()
    mock_composite_instance.close = mock.Mock()
    mock_composite_audio_clip.return_value = mock_composite_instance

    mock_final_clip_instance = mock.MagicMock(spec=mpy.AudioClip)
    mock_final_clip_instance.write_audiofile = mock.Mock()
    mock_audio_fadeout.return_value = mock_final_clip_instance

    result_audio_path = self.final_audio_step.process(self.storyboard)

    self.assertEqual(self.output_path, result_audio_path)
    mock_final_clip_instance.write_audiofile.assert_called_once_with(
        filename=self.output_path, fps=self.fps
    )
    mock_narration_clip_instance.close.assert_called_once()
    mock_background_clip_instance.close.assert_called_once()
    mock_composite_instance.close.assert_called_once()


if __name__ == '__main__':
  unittest.main()
