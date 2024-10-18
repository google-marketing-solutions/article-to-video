import unittest
from unittest import mock

from pipeline import video_generation_context
from truth import truth
from video import generate_video_from_images_step
from video import video_generation_errors


class GenerateVideoFromImagesStepTest(unittest.TestCase):

  _CONTEXT = video_generation_context.VideoGenerationContext(
      {
          'gcp_project': 'my_gcp_project',
          'gcp_location': 'us_west',
          'gcs_bucket_name': 'my_bucket_name',
          'gcs_bucket_text_path': 'my_gcs_bucket_text_path',
          'gcs_bucket_image_path': 'my_gcs_bucket_image_path',
          'output_path': 'tests/video/generated/generate_video_from_images',
      },
      {'ken_burns': True},
      '0218e40f-d722-4391-8ef7-47bbdaa29200',
  )

  def test_raises_no_images_error_if_folder_contains_no_images(self):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        self._CONTEXT
    )
    execute_ffmpeg_command = mock.MagicMock()
    step.execute_ffmpeg_command = execute_ffmpeg_command
    with truth.AssertThat(
        video_generation_errors.NoImagesFoundError
    ).IsRaised():
      step(('/not/my/images/*', '/my/audio'))

  def test_generates_video_from_images(self):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        self._CONTEXT
    )
    execute_ffmpeg_command = mock.MagicMock()
    step.execute_ffmpeg_command = execute_ffmpeg_command
    with mock.patch('glob.glob') as glob_mock:
      glob_mock.return_value = ['/my/images/1', '/my/images/2', '/my/images/3']
      step(('/my/images/*', '/my/audio'))

    execute_ffmpeg_command.assert_called_with([
        'ffmpeg',
        '-i',
        '/my/images/1',
        '-i',
        '/my/images/2',
        '-i',
        '/my/images/3',
        '-filter_complex',
        (
            "\"[0:v]zoompan=z='min(zoom+0.0015,1.5)':d=33:s=1280x720,fade=t=out:st=0.3333333333333333:d=1[v0];"
            "[1:v]zoompan=z='min(zoom+0.0015,1.5)':d=33:s=1280x720,fade=t=out:st=0.3333333333333333:d=1[v1];"
            "[2:v]zoompan=z='min(zoom+0.0015,1.5)':d=33:s=1280x720,fade=t=out:st=0.3333333333333333:d=1[v2];"
            '[v0][v1]xfade=transition=fade:duration=1:offset=-0.6666666666666667[v1];'
            '[v1][v2]xfade=transition=fade:duration=1:offset=-0.3333333333333334[v2]"'
        ),
        '-map',
        '[v2]',
        '-c:v',
        'libx264',
        '-crf',
        '23',
        '-preset',
        'medium',
        '-pix_fmt',
        'yuv420p',
        '-r',
        '25',
        '-y',
        'tests/video/generated/generate_video_from_images/0218e40f-d722-4391-8ef7-47bbdaa29200/5_mutedvideo.mp4',
    ])

  def test_runs_command_and_validates_golden(self):
    step = generate_video_from_images_step.GenerateVideoFromImagesStep(
        self._CONTEXT
    )

    result, _ = step((
        'tests/video/goldens/generate_video_from_images/image*',
        'tests/video/goldens/generate_video_from_images/audio.mp3',
    ))

    files_equal = True
    with open(
        'tests/video/goldens/generate_video_from_images/5_mutedvideo.mp4', 'rb'
    ) as one:
      with open(result, 'rb') as two:
        chunk = other = True
        while chunk or other:
          chunk = one.read(1000)
          other = two.read(1000)
          if chunk != other:
            files_equal = False

    truth.AssertThat(files_equal).IsTrue()
