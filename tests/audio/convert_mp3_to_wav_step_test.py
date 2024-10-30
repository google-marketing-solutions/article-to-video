import unittest
from unittest import mock

from audio import convert_mp3_to_wav_step
from pipeline import video_generation_context
from truth import truth


class ConvertMp3ToWavStepTest(unittest.TestCase):

  _CONTEXT = video_generation_context.VideoGenerationContext(
      {
          "gcp_project": "my_gcp_project",
          "gcp_location": "us_west",
          "gcs_bucket_name": "my_bucket_name",
          "gcs_bucket_text_path": "my_gcs_bucket_text_path",
          "gcs_bucket_image_path": "my_gcs_bucket_image_path",
          "output_path": "tests/audio/generated/convert_mp3_to_wav_step",
      },
      {},
      "0218e40f-d722-4391-8ef7-47bbdaa29200",
  )

  def test_converts_audio_correctly(self):
    step = convert_mp3_to_wav_step.ConvertMp3ToWavStep(self._CONTEXT)
    execute_ffmpeg_command = mock.MagicMock()
    step.execute_ffmpeg_command = execute_ffmpeg_command
    step("/my/input/audio.mp3")

    execute_ffmpeg_command.assert_called_once_with([
        "ffmpeg",
        "-y",
        "-i",
        "/my/input/audio.mp3",
        "tests/audio/generated/convert_mp3_to_wav_step/0218e40f-d722-4391-8ef7-47bbdaa29200/3_readaloud.wav",
    ])

  def test_runs_command_and_validates_golden(self):
    step = convert_mp3_to_wav_step.ConvertMp3ToWavStep(self._CONTEXT)

    result = step("tests/audio/goldens/audio.mp3")

    files_equal = True
    with open("tests/audio/goldens/audio.wav", "rb") as one:
      with open(result, "rb") as two:
        chunk = other = True
        while chunk or other:
          chunk = one.read(1000)
          other = two.read(1000)
          if chunk != other:
            files_equal = False

    truth.AssertThat(files_equal).IsTrue()
