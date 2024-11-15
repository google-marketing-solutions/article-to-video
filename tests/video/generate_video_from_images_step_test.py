import tempfile
import unittest
from unittest import mock

from moviepy import editor
import storyboarding
from truth import truth
from video import generate_video_from_images_step
from video import video_generation_errors


class GenerateVideoFromImagesStepTest(unittest.TestCase):

  def test_raises_no_images_error_if_folder_contains_no_images(self):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/path'
    )
    with truth.AssertThat(
        video_generation_errors.NoImagesFoundError
    ).IsRaised():
      step(storyboarding.Storyboard([], 'audio/path'))

  @mock.patch.object(editor, 'CompositeVideoClip', autospec=True)
  @mock.patch.object(editor, 'ImageClip', autospec=True)
  @mock.patch.object(editor, 'AudioFileClip', autospec=True)
  def test_generates_video_from_images_returns_output_path(
      self, mock_audio_file_clip, *_
  ):
    mock_audio_file_clip.return_value.duration = 45.0
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        'output/path'
    )
    storyboard = storyboarding.Storyboard(
        scenes=[
            storyboarding.ImageScene(
                image_path='input_images/image1.jpg',
                start_time=0,
            ),
            storyboarding.ImageScene(
                image_path='input_images/image2.jpg',
                start_time=24.5,
            ),
        ],
        main_audio_path='/my/audio',
    )

    self.assertEqual(
        step(storyboard),
        'output/path',
    )

  def test_runs_command_and_validates_golden(self):
    tmp_output_dir = tempfile.TemporaryDirectory()

    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        tmp_output_dir.name + '5_withaudiovideo.mp4'
    )

    dir_root = 'tests/video/goldens/generate_video_from_images/'
    focal_points = [
        [0, 0, 1000, 1000],  # Entire image
        [0, 500, 500, 1000],  # Top-right quadrant
        [0, 0, 500, 500],  # Top-left quadrant
        [500, 500, 1000, 1000],  # Lower-right quadrant
        [500, 0, 1000, 500],  # Lower-left quadrant
        [0, 0, 1000, 1000],
        [0, 0, 1000, 1000],
    ]
    scenes = [
        storyboarding.ImageScene(
            i * 10, f'{dir_root}/image{i+1}.png', focal_point=focal_points[i]
        )
        for i in range(7)
    ]
    storyboard = storyboarding.Storyboard(
        scenes=scenes,
        main_audio_path=(
            'tests/video/goldens/generate_video_from_images/audio.mp3'
        ),
    )

    result = step(storyboard)

    files_equal = True
    with open(
        'tests/video/goldens/generate_video_from_images/5_withaudiovideo.mp4',
        'rb',
    ) as one:
      with open(result, 'rb') as two:
        chunk = other = True
        while chunk or other:
          chunk = one.read(1000)
          other = two.read(1000)
          if chunk != other:
            files_equal = False

    truth.AssertThat(files_equal).IsTrue()
    tmp_output_dir.cleanup()


if __name__ == '__main__':
  unittest.main()
