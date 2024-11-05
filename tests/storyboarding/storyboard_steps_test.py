import unittest
from unittest import mock
from moviepy import editor
import storyboarding


class CreateStoryBoardStepsTest(unittest.TestCase):

  @mock.patch.object(editor, 'AudioFileClip', autospec=True)
  def test_create_storyboard(self, mock_audio_file_clip):
    mock_audio_file_clip.return_value.__enter__.return_value.duration = 46.0
    storyboard = storyboarding.create_storyboard_step(
        ['image/path/1', 'image/path/2'], 'audio_path'
    )

    self.assertEqual(
        storyboard,
        storyboarding.Storyboard(
            scenes=[
                storyboarding.Scene(
                    background_image_path='image/path/1', start_time=0
                ),
                storyboarding.Scene(
                    background_image_path='image/path/2', start_time=23.0
                ),
            ],
            main_audio_path='audio_path',
        ),
    )
