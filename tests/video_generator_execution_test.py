import os
import tempfile
import unittest
from unittest import mock
import audio
import audio.subtitles_generation_step
import parameterized
from pipeline import video_generation_context
import storyboarding
import text
import vertexai
import video
import video_generator_execution
import yaml


class VideoGeneratorTest(unittest.TestCase):

  def setUp(self):
    self.temp_work_dir = tempfile.TemporaryDirectory()

    self.video_id = "test_video_id"
    self.context = video_generation_context.VideoGenerationContext.from_request(
        video_generation_context.VideoGenerationContext.Config({
            "gcp_project": "test-project",
            "gcp_location": "us-central1",
            "output_path": self.temp_work_dir.name,
            "gcs_bucket_name": "test-bucket",
            "gcs_bucket_text_path": "text",
            "gcs_bucket_image_path": "images",
        }),
        request_params={
            "article_content": "test article content",
            "image_paths": ["test_image_1.jpg", "test_image_2.png"],
        },
        video_id=self.video_id,
    )
    self.mock_script_generator = mock.MagicMock(spec=text.ScriptGenerator)
    self.video_generator = video_generator_execution.VideoGenerator(
        self.mock_script_generator
    )
    return super().setUp()

  def tearDown(self):
    self.temp_work_dir.cleanup()
    return super().tearDown()

  @mock.patch.object(os, "makedirs", autospec=True)
  def test_generate_script_step(self, mock_makedirs):
    mock_script = mock.MagicMock(spec=text.VoiceoverScript)
    self.mock_script_generator.generate.return_value = mock_script

    self.context.multivoice = False
    self.context.multitext = False
    self.context.language = "en-US"

    returned_script = self.video_generator.generate_script_step(self.context)

    mock_makedirs.assert_called_once_with(self.context.workdir, exist_ok=True)
    self.assertEqual(self.mock_script_generator.language, "en-US")
    self.assertEqual(self.mock_script_generator.speakers, 1)
    self.assertEqual(self.mock_script_generator.multitext, False)
    self.mock_script_generator.generate.assert_called_once_with(
        self.context.article_content,
        os.path.join(
            self.context.workdir, video_generator_execution.SCRIPT_FILE_NAME
        ),
    )
    self.assertEqual(returned_script, mock_script)

    self.mock_script_generator.reset_mock()
    self.context.multivoice = True
    self.video_generator.generate_script_step(self.context)
    self.assertEqual(self.mock_script_generator.speakers, 2)

  @mock.patch.object(text, "load_script", autospec=True)
  def test_generate_script_step_cache_hit(self, mock_load_script):
    script_path = os.path.join(
        self.context.workdir,
        video_generator_execution.SCRIPT_FILE_NAME,
    )
    directory = os.path.dirname(script_path)
    os.makedirs(directory, exist_ok=True)
    with open(script_path, "w", encoding="utf-8"):
      self.video_generator.generate_script_step(self.context)
      self.video_generator.generate_script_step(self.context)

      self.mock_script_generator.generate.assert_called_once()
      mock_load_script.assert_called_once_with(script_path)

  @mock.patch.object(text, "load_script", autospec=True)
  def test_generate_script_step_cache_miss(self, mock_load_script):
    script_path = os.path.join(
        self.context.workdir,
        video_generator_execution.SCRIPT_FILE_NAME,
    )
    directory = os.path.dirname(script_path)
    os.makedirs(directory, exist_ok=True)
    with open(script_path, "w", encoding="utf-8"):
      self.video_generator.generate_script_step(self.context)
      self.context.article_content = "new article content"
      self.video_generator.generate_script_step(self.context)

      self.assertEqual(self.mock_script_generator.generate.call_count, 2)
      mock_load_script.assert_not_called()

  @mock.patch.object(
      audio.subtitles_generation_step, "SubtitlesGenerationStep", autospec=True
  )
  @mock.patch.object(
      audio.text_to_speech_step, "TextToSpeechStep", autospec=True
  )
  def test_generate_audio_step(self, mock_tts, mock_subtitles_step):
    mock_tts.return_value.process.return_value = (
        "audio_path",
        "audio_uri",
        "script_text",
    )

    self.video_generator.generate_audio_step(self.context)

    self.assertTrue(os.path.exists(self.context.workdir))
    self.mock_script_generator.generate.assert_called_once_with(
        self.context.article_content,
        os.path.join(self.context.workdir, "1_script.json"),
    )
    mock_tts.assert_called_once_with(self.context)
    mock_subtitles_step.assert_called_once_with(self.context)

  @mock.patch.object(
      audio.subtitles_generation_step.SubtitlesGenerationStep,
      "process",
      autospec=True,
  )
  @mock.patch.object(
      audio.text_to_speech_step.TextToSpeechStep, "process", autospec=True
  )
  def test_generate_audio_step_cache_hit(
      self, mock_tts_process, mock_subs_process
  ):
    mock_tts_process.return_value = (
        "audio_path",
        "audio_uri",
        "script_text",
    )
    audio_file_path = os.path.join(
        self.context.workdir, video_generator_execution.AUDIO_FILE_NAME
    )
    srt_file_path = os.path.join(
        self.context.workdir, video_generator_execution.SRT_FILE_NAME
    )
    os.makedirs(self.context.workdir, exist_ok=True)
    with (
        open(audio_file_path, "w", encoding="utf-8"),
        open(srt_file_path, "w", encoding="utf-8"),
    ):
      self.video_generator.generate_audio_step(self.context)
      self.video_generator.generate_audio_step(self.context)

      mock_subs_process.assert_called_once()
      mock_tts_process.assert_called_once()

  @mock.patch.object(
      audio.subtitles_generation_step.SubtitlesGenerationStep,
      "process",
      autospec=True,
  )
  @mock.patch.object(
      audio.text_to_speech_step.TextToSpeechStep, "process", autospec=True
  )
  def test_generate_audio_step_cache_miss(
      self, mock_tts_process, mock_subs_process
  ):
    mock_tts_process.return_value = (
        "audio_path",
        "audio_uri",
        "script_text",
    )
    audio_file_path = os.path.join(
        self.context.workdir, video_generator_execution.AUDIO_FILE_NAME
    )
    srt_file_path = os.path.join(
        self.context.workdir, video_generator_execution.SRT_FILE_NAME
    )
    os.makedirs(self.context.workdir, exist_ok=True)
    with (
        open(audio_file_path, "w", encoding="utf-8"),
        open(srt_file_path, "w", encoding="utf-8"),
    ):
      self.video_generator.generate_audio_step(self.context)
      self.context.article_content = "new article content"
      self.video_generator.generate_audio_step(self.context)

      self.assertEqual(mock_subs_process.call_count, 2)
      self.assertEqual(mock_tts_process.call_count, 2)

  @mock.patch.object(storyboarding, "create_storyboard_step", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_audio_step",
      autospec=True,
  )
  def test_generate_storyboard_step(
      self, mock_generate_audio_step, mock_create_storyboard_step
  ):
    os.makedirs(self.context.workdir, exist_ok=True)
    mock_generate_audio_step.return_value = (
        "audio_path",
        "srt_path",
    )

    sb = self.video_generator.generate_storyboard_step(self.context)

    self.assertEqual(sb, mock_create_storyboard_step.return_value)

  @mock.patch.object(storyboarding, "load_storyboard", autospec=True)
  @mock.patch.object(storyboarding, "create_storyboard_step", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_audio_step",
      autospec=True,
  )
  def test_generate_storyboard_step_cache_hit(
      self,
      mock_generate_audio_step,
      mock_create_storyboard_step,
      mock_load_storyboard,
  ):
    mock_generate_audio_step.return_value = (
        os.path.join(self.context.workdir, "audio.wav"),
        os.path.join(self.context.workdir, "subtitles.srt"),
    )
    storyboard_file_path = os.path.join(
        self.context.workdir, video_generator_execution.STORYBOARD_FILE_NAME
    )
    srt_file_path = mock_generate_audio_step.return_value[1]

    os.makedirs(self.context.workdir, exist_ok=True)
    with (
        open(storyboard_file_path, "w", encoding="utf-8"),
        open(srt_file_path, "w", encoding="utf-8"),
    ):
      self.video_generator.generate_storyboard_step(self.context)
      self.video_generator.generate_storyboard_step(self.context)

      mock_create_storyboard_step.assert_called_once()
      mock_load_storyboard.assert_called_once_with(storyboard_file_path)

  @mock.patch.object(storyboarding, "load_storyboard", autospec=True)
  @mock.patch.object(storyboarding, "create_storyboard_step", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_audio_step",
      autospec=True,
  )
  def test_generate_storyboard_step_cache_miss_due_to_srt_change(
      self,
      mock_generate_audio_step,
      mock_create_storyboard_step,
      mock_load_storyboard,
  ):
    mock_generate_audio_step.return_value = (
        os.path.join(self.context.workdir, "audio.wav"),
        os.path.join(self.context.workdir, "subtitles.srt"),
    )
    storyboard_file_path = os.path.join(
        self.context.workdir, video_generator_execution.STORYBOARD_FILE_NAME
    )
    srt_file_path = mock_generate_audio_step.return_value[1]

    os.makedirs(self.context.workdir, exist_ok=True)
    with (
        open(storyboard_file_path, "w", encoding="utf-8"),
        open(srt_file_path, "w", encoding="utf-8"),
    ):
      self.video_generator.generate_storyboard_step(self.context)
      self.context.article_content = "new article content"
      self.video_generator.generate_storyboard_step(self.context)

      self.assertEqual(mock_create_storyboard_step.call_count, 2)
      mock_load_storyboard.assert_not_called()

  @mock.patch.object(video, "GenerateVideoFromImagesStep", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_storyboard_step",
      autospec=True,
  )
  def test_generate_video_step_storyboard_exists(
      self,
      mock_generate_storyboard_step,
      mock_generate_video_step,
  ):
    os.makedirs(self.context.workdir, exist_ok=True)

    self.video_generator.generate_video_step(self.context)

    mock_generate_video_step.return_value.process.assert_called_once_with(
        mock_generate_storyboard_step.return_value
    )

  @mock.patch.object(video, "GenerateVideoFromImagesStep", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_storyboard_step",
      autospec=True,
  )
  def test_generate_video_step_storyboard_not_exists(
      self,
      mock_generate_storyboard_step,
      mock_generate_video_step,
  ):
    os.makedirs(self.context.workdir, exist_ok=True)

    self.video_generator.generate_video_step(self.context)
    mock_generate_storyboard_step.assert_called_once()

    mock_generate_video_step.assert_called_once()

  @mock.patch.object(
      video.GenerateVideoFromImagesStep, "process", autospec=True
  )
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_storyboard_step",
      autospec=True,
  )
  def test_generate_video_step_cache_hit(
      self, mock_generate_storyboard_step, mock_video_process
  ):
    mock_storyboard = mock.MagicMock(spec=storyboarding.Storyboard)
    mock_storyboard.name = "test_storyboard"  # for consistent hashing
    mock_generate_storyboard_step.return_value = mock_storyboard

    video_file_path = os.path.join(
        self.context.workdir, video_generator_execution.OUTPUT_VIDEO_FILE_NAME
    )
    os.makedirs(self.context.workdir, exist_ok=True)
    with open(video_file_path, "w", encoding="utf-8"):
      self.video_generator.generate_video_step(self.context)
      self.video_generator.generate_video_step(self.context)

      mock_video_process.assert_called_once()
      self.assertEqual(mock_generate_storyboard_step.call_count, 2)

  @mock.patch.object(
      video.GenerateVideoFromImagesStep, "process", autospec=True
  )
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_storyboard_step",
      autospec=True,
  )
  def test_generate_video_step_cache_miss_due_to_storyboard_change(
      self, mock_generate_storyboard_step, mock_video_process
  ):
    mock_storyboard_v1 = mock.MagicMock(spec=storyboarding.Storyboard)
    mock_storyboard_v1.main_audio_path = "audio_path"
    mock_storyboard_v2 = mock.MagicMock(spec=storyboarding.Storyboard)
    mock_storyboard_v2.main_audio_path = "new_audio_path"

    video_file_path = os.path.join(
        self.context.workdir, video_generator_execution.OUTPUT_VIDEO_FILE_NAME
    )
    os.makedirs(self.context.workdir, exist_ok=True)
    with open(video_file_path, "w", encoding="utf-8"):
      mock_generate_storyboard_step.return_value = mock_storyboard_v1
      self.video_generator.generate_video_step(self.context)
      # Second call - storyboard changes, should regenerate
      mock_generate_storyboard_step.return_value = mock_storyboard_v2
      self.video_generator.generate_video_step(self.context)

      self.assertEqual(mock_video_process.call_count, 2)
      self.assertEqual(mock_generate_storyboard_step.call_count, 2)

  def setup_test_env_for_main(self, directory: tempfile.TemporaryDirectory):
    directory_path = directory.name
    test_config = {
        "gcp_project": "test-project",
        "gcp_location": "us-central1",
        "output_path": "test-output-path",
        "gcs_bucket_name": "test-bucket",
        "gcs_bucket_text_path": "text",
        "gcs_bucket_image_path": "images",
    }
    config_path = directory_path + "/config.yml"
    with open(config_path, "w", encoding="utf-8") as config_file:
      yaml.dump(test_config, config_file)

    article_path = directory_path + "/article.txt"
    with open(article_path, "w", encoding="utf-8") as article_file:
      article_file.write("this is my article content")

    image_dir_path = directory_path + "/images"
    os.makedirs(image_dir_path)
    with open(image_dir_path + "/image1.jpg", mode="a", encoding="utf-8"):
      pass
    with open(image_dir_path + "/image2.jpg", mode="a", encoding="utf-8"):
      pass

  @parameterized.parameterized.expand([
      ("gcp_project", "test-project"),
      ("gcp_location", "us-central1"),
      ("gcs_bucket_name", "test-bucket"),
      ("gcs_bucket_text_path", "text"),
      ("gcs_bucket_image_path", "images"),
      ("video_id", "test_video_id"),
      ("language", "en-US"),
      ("multivoice", False),
      ("multitext", False),
      ("article_content", "this is my article content"),
  ])
  @mock.patch.object(vertexai, "init", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_video_step",
      autospec=True,
  )
  def test_main_configures_context(
      self,
      context_attr,
      context_attr_expected_value,
      mock_generate_video_step,
      _,
  ):
    self.setup_test_env_for_main(self.temp_work_dir)

    video_generator_execution.main([
        "--config",
        self.temp_work_dir.name + "/config.yml",
        "--video_id",
        self.video_id,
        "--article_path",
        self.temp_work_dir.name + "/article.txt",
        "--image_dir",
        self.temp_work_dir.name + "/images",
    ])

    # the context is what we expect
    context = mock_generate_video_step.call_args[0][1]
    self.assertEqual(
        getattr(context, context_attr), context_attr_expected_value
    )

  @parameterized.parameterized.expand([
      ("audio", "generate_audio_step"),
      ("storyboard", "generate_storyboard_step"),
      ("video", "generate_video_step"),
  ])
  @mock.patch.object(vertexai, "init", autospec=True)
  def test_main_individual_steps(
      self,
      step_arg,
      step,
      _,
  ):
    self.setup_test_env_for_main(self.temp_work_dir)

    with mock.patch.object(
        video_generator_execution.VideoGenerator, step, autospec=True
    ) as mock_generate_step:
      video_generator_execution.main([
          "--config",
          self.temp_work_dir.name + "/config.yml",
          "--video_id",
          self.video_id,
          "--article_path",
          self.temp_work_dir.name + "/article.txt",
          "--image_dir",
          self.temp_work_dir.name + "/images",
          "--step",
          step_arg,
      ])

      mock_generate_step.assert_called_once()

  @mock.patch.object(vertexai, "init", autospec=True)
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_audio_step",
      autospec=True,
  )
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_storyboard_step",
      autospec=True,
  )
  @mock.patch.object(
      video_generator_execution.VideoGenerator,
      "generate_video_step",
      autospec=True,
  )
  def test_main_configures_context_image_paths(
      self,
      mock_generate_video_step,
      *_,
  ):
    self.setup_test_env_for_main(self.temp_work_dir)

    video_generator_execution.main([
        "--config",
        self.temp_work_dir.name + "/config.yml",
        "--video_id",
        self.video_id,
        "--article_path",
        self.temp_work_dir.name + "/article.txt",
        "--image_dir",
        self.temp_work_dir.name + "/images",
    ])

    # the context is what we expect
    context = mock_generate_video_step.call_args[0][1]
    self.assertCountEqual(
        context.image_paths,
        [
            self.temp_work_dir.name + "/images/image2.jpg",
            self.temp_work_dir.name + "/images/image1.jpg",
        ],
    )


if __name__ == "__main__":
  unittest.main()
