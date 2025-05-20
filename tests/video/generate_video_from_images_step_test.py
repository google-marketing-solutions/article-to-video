from typing import Tuple
import unittest
from unittest import mock

from audio import create_final_audio_step
from moviepy import editor as mpy
import moviepy.audio.fx.all as afx
import numpy as np
import parameterized
import storyboarding
from video import effects
from video import generate_video_from_images_step
from video import video_generation_errors


def _audio_clip(duration: int = 30):
  """Creates a mock MoviePy AudioClip.

  The actual audio content is a simple sine wave.
  The 'write_audiofile' method is patched to prevent actual file writes.

  Args:
    duration: The duration of the mock audio clip in seconds.

  Returns:
    A mock mpy.AudioClip instance.
  """
  with (mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True),):
    return mpy.AudioClip(
        lambda t: 2 * [np.sin(440 * 2 * np.pi * t)], duration=duration
    )


def _image_clip(dimensions: Tuple[int, int, int] = (100, 100, 3)):
  """Creates a mock MoviePy ImageClip.

  The image content is a randomly generated NumPy array.

  Args:
    dimensions: A tuple (height, width, channels) for the mock image.

  Returns:
    A mock mpy.ImageClip instance.
  """
  return mpy.ImageClip(np.random.randint(0, 256, dimensions, dtype=np.uint8))


class GenerateVideoFromImagesStepTest(unittest.TestCase):

  def test_raises_no_images_error_if_folder_contains_no_images(self):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3', 'output/video/path.mp4'
    )
    with self.assertRaises(video_generation_errors.NoImagesFoundError):
      step(storyboarding.Storyboard([], 'audio/path', 'srt/path'))

  @mock.patch.object(afx, 'audio_loop', autospec=True)
  @mock.patch.object(mpy, 'CompositeVideoClip', autospec=True)
  @mock.patch.object(mpy, 'ImageClip', return_value=_image_clip())
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_audio_clip())
  @mock.patch.object(
      create_final_audio_step.CreateFinalAudioStep, 'process', autospec=True
  )
  def test_generates_video_from_images_returns_output_path(
      self, mock_final_audio_process, mock_audio_file_clip_constructor, *_
  ):
    mock_audio_file_clip_constructor.return_value = _audio_clip(duration=45)
    mock_final_audio_process.return_value = 'mock_audio_path'

    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3',
        'output/video/path.mp4',
    )
    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.Scene(
                image_path='input_images/image1.jpg',
                start_time='00:00:00,000',
            ),
            storyboarding.Scene(
                image_path='input_images/image2.jpg',
                start_time='00:00:24,500',
            ),
        ],
        main_audio_path='/my/audio',
        srt_path='/srt/path',
    )

    self.assertEqual(
        step(storyboard),
        'output/video/path.mp4',
    )

  @mock.patch.object(afx, 'audio_loop', autospec=True)
  @mock.patch.object(mpy, 'CompositeVideoClip', autospec=True)
  @mock.patch.object(mpy, 'ImageClip', return_value=_image_clip())
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_image_clip())
  @mock.patch.object(
      create_final_audio_step.CreateFinalAudioStep, 'process', autospec=True
  )
  def test_only_append_images_before_end_of_audio(
      self,
      mock_final_audio_process,
      mock_audio_file_clip_constructor,
      mock_image_clip_constructor,
      *_,
  ):
    mock_audio_file_clip_constructor.return_value = _audio_clip(duration=15)
    mock_final_audio_process.return_value = 'mock/audio.mp3'

    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3', 'output/video/path.mp4'
    )
    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.Scene(
                image_path='input_images/image1.jpg',
                start_time='00:00:00,000',
            ),
            storyboarding.Scene(
                image_path='input_images/image2.jpg',
                start_time='00:00:20,000',
            ),
        ],
        main_audio_path='/my/audio',
        srt_path='/srt/path',
    )

    step(storyboard)

    # 15 seconds + 1 second to allow for cross fade
    mock_image_clip_constructor.assert_called_once_with(
        'input_images/image1.jpg', duration=16
    )

  @parameterized.parameterized.expand([
      ('zoom_in_slow', 'in', False),
      ('zoom_in_fast', 'in', True),
      ('zoom_out_slow', 'out', False),
      ('zoom_out_fast', 'out', True),
  ])
  @mock.patch.object(mpy.CompositeVideoClip, 'write_videofile', autospec=True)
  @mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(mpy, 'ImageClip', return_value=_image_clip())
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_audio_clip(15))
  @mock.patch.object(effects, 'zoom', autospec=True)
  def test_applies_zoom_animation_correctly(
      self,
      animation,
      direction,
      fast,
      mock_zoom,
      *_,
  ):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3', 'output/video/path.mp4'
    )

    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.Scene(
                image_path='input_images/image1.jpg',
                start_time='00:00:00,000',
                animation=animation,
            ),
        ],
        main_audio_path='/my/audio',
        srt_path='/srt/path',
    )

    step(storyboard)

    mock_zoom.assert_called_once_with(
        mock.ANY,
        direction=direction,
        fast=fast,
    )

  @parameterized.parameterized.expand([
      ('panto_fast', (32, 32), True),
      ('panto_slow', (32, 32), False),
  ])
  @mock.patch.object(mpy.CompositeVideoClip, 'write_videofile', autospec=True)
  @mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(mpy, 'ImageClip', return_value=_image_clip())
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_audio_clip(15))
  @mock.patch.object(effects, 'zoom_pan_to', autospec=True)
  def test_applies_panto_animation_correctly(
      self, animation, target, fast, mock_zoom_pan_to, *_
  ):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3', 'output/video/path.mp4'
    )
    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.Scene(
                image_path='input_images/image1.jpg',
                start_time='00:00:00,000',
                focal_point=[0, 0, 50, 50],
                animation=animation,
            ),
        ],
        main_audio_path='/my/audio',
        srt_path='/srt/path',
    )

    step(storyboard)

    mock_zoom_pan_to.assert_called_once_with(
        mock.ANY,
        target=target,
        fast=fast,
    )

  @parameterized.parameterized.expand([
      # the third dimension is the RGB colors
      ('landscape_image', (1000, 500, 3)),
      ('portrait_image', (500, 1000, 3)),
  ])
  @mock.patch.object(mpy.CompositeAudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(mpy.CompositeVideoClip, 'write_videofile', autospec=True)
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_audio_clip())
  @mock.patch.object(mpy.ImageClip, 'resize', autospec=True)
  def test_resize_images_based_on_dimensions(
      self, unused_test_name, dimensions, mock_resize, *_
  ):
    with mock.patch.object(
        mpy,
        'ImageClip',
        return_value=_image_clip(dimensions),
    ):
      step = generate_video_from_images_step.GenerateVideoFromImagesStep(
          'output/audio/path.mp3', 'output/video/path.mp4'
      )
      storyboard = storyboarding.Storyboard(
          scenes=[
              storyboarding.Scene(
                  image_path='input_images/image1.jpg',
                  start_time='00:00:00,000',
                  focal_point=[0, 0, 50, 50],
                  animation='static',
              ),
          ],
          main_audio_path='/my/audio',
          srt_path='/srt/path',
      )

      step(storyboard)

      if dimensions[0] < dimensions[1]:
        mock_resize.assert_called_once_with(
            mock.ANY, width=step._target_resolution[0]
        )
      else:
        mock_resize.assert_called_once_with(
            mock.ANY, height=step._target_resolution[1]
        )

  @parameterized.parameterized.expand([
      ('slide_left', 'left'),
      ('slide_right', 'right'),
      ('slide_up', 'up'),
      ('slide_down', 'down'),
  ])
  @mock.patch.object(mpy.CompositeVideoClip, 'write_videofile', autospec=True)
  @mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(mpy, 'ImageClip', return_value=_image_clip())
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_audio_clip(15))
  @mock.patch.object(effects, 'slide', autospec=True)
  def test_applies_slide_animation_correctly(
      self, animation, direction, mock_slide, *_
  ):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3', 'output/video/path.mp4'
    )
    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.Scene(
                image_path='input_images/image1.jpg',
                start_time='00:00:00,000',
                animation=animation,
            ),
        ],
        main_audio_path='/my/audio',
        srt_path='srt/path',
    )

    step(storyboard)

    mock_slide.assert_called_once_with(
        mock.ANY,
        direction=direction,
    )

  @mock.patch.object(mpy.CompositeVideoClip, 'write_videofile', autospec=True)
  @mock.patch.object(mpy.AudioClip, 'write_audiofile', autospec=True)
  @mock.patch.object(mpy, 'AudioFileClip', return_value=_audio_clip(15))
  @mock.patch.object(mpy, 'ImageClip', return_value=_image_clip())
  def test_adds_logo(self, mock_image_clip, *_):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/audio/path.mp3', 'output/video/path.mp4'
    )
    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.Scene(
                image_path='input_images/image1.jpg',
                start_time='00:00:00,000',
            ),
        ],
        main_audio_path='/my/audio',
        logo_path='path/to/my/logo.png',
        srt_path='/srt/path',
    )

    step(storyboard)

    mock_image_clip.assert_called_with(
        'path/to/my/logo.png',
        duration=15,  # audio duration
    )


if __name__ == '__main__':
  unittest.main()
