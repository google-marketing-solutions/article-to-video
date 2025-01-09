import os
import tempfile
import unittest
from unittest import mock
import audio
import audio.subtitles_generation_step
import msgspec
import parameterized
from pipeline import video_generation_context
import storyboarding
import text
from util import create_workdir_step
import vertexai
import video
import video_generator_execution
import yaml


class VideoGeneratorExecutionTest(unittest.TestCase):

  def setUp(self):
    self.temp_work_dir = tempfile.TemporaryDirectory()

    self.video_id = "test_video_id"
    self.context = video_generation_context.VideoGenerationContext(
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
    return super().setUp()

  def tearDown(self):
    self.temp_work_dir.cleanup()
    return super().tearDown()

  @mock.patch.object(
      audio.subtitles_generation_step, "SubtitlesGenerationStep", autospec=True
  )
  @mock.patch.object(
      audio.text_to_speech_step, "TextToSpeechStep", autospec=True
  )
  @mock.patch.object(
      text.summarize_text_step, "SummarizeTextStep", autospec=True
  )
  def test_generate_audio_step(
      self, mock_summarize_text_step, mock_tts_step, mock_subtitles_step
  ):
    video_generator_execution.generate_audio_step(self.context)

    self.assertTrue(os.path.exists(self.context.workdir))

    mock_summarize_text_step.return_value.assert_called_once_with(
        "test article content"
    )
    mock_tts_step.return_value.assert_called_once_with(
        mock_summarize_text_step.return_value.return_value
    )
    mock_subtitles_step.return_value.assert_called_once_with(
        mock_tts_step.return_value.return_value
    )

  @mock.patch.object(storyboarding, "create_storyboard_step", autospec=True)
  def test_generate_storyboard_step(self, mock_create_storyboard_step):
    mock_create_storyboard_step.return_value = storyboarding.Storyboard(
        scenes=[],
        main_audio_path="path/to/audio",
        background_audio_path="path/to/background_audio",
    )
    create_workdir_step.CreateWorkdirStep(self.context)("article content")

    video_generator_execution.generate_storyboard_step(self.context)

    with open(
        self.context.workdir + "/4_storyboard.json", "r", encoding="utf-8"
    ) as storyboard_file:
      storyboard = msgspec.json.decode(
          storyboard_file.read(), type=storyboarding.Storyboard
      )
      self.assertEqual(storyboard, mock_create_storyboard_step.return_value)

  @mock.patch.object(video, "GenerateVideoFromImagesStep", autospec=True)
  def test_generate_video_step(self, mock_generate_video_step):
    create_workdir_step.CreateWorkdirStep(self.context)("article content")
    storyboard = storyboarding.Storyboard(
        scenes=[],
        main_audio_path="path/to/audio",
        background_audio_path="path/to/background_audio",
    )
    with open(
        self.context.workdir + "/4_storyboard.json", "w", encoding="utf-8"
    ) as storyboard_file:
      storyboard_file.write(msgspec.json.encode(storyboard).decode("utf-8"))

    video_generator_execution.generate_video_step(self.context)

    mock_generate_video_step.assert_called_once_with(
        output_audio_path=f"{self.context.workdir}/6_finalaudio.mp3",
        output_video_path=f"{self.context.workdir}/5_withaudiovideo.mp4",
    )
    mock_generate_video_step.return_value.process.assert_called_once_with(
        storyboard
    )

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
      ("multivoice", True),
      ("sentiment", False),
      ("video_overlay", False),
      ("title", False),
      ("article_content", "this is my article content"),
  ])
  @mock.patch.object(vertexai, "init", autospec=True)
  @mock.patch.object(
      video_generator_execution, "generate_audio_step", autospec=True
  )
  @mock.patch.object(
      video_generator_execution, "generate_storyboard_step", autospec=True
  )
  @mock.patch.object(
      video_generator_execution, "generate_video_step", autospec=True
  )
  def test_main_configures_context(
      self,
      context_attr,
      context_attr_expected_value,
      mock_generate_video_step,
      mock_generate_storyboard_step,
      mock_generate_audio_step,
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

    # all three steps are called with the same arg (the context)
    self.assertEqual(
        mock_generate_audio_step.call_args,
        mock_generate_storyboard_step.call_args,
    )
    self.assertEqual(
        mock_generate_storyboard_step.call_args,
        mock_generate_video_step.call_args,
    )

    # the context is what we expect
    context = mock_generate_audio_step.call_args[0][0]
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
        video_generator_execution, step, autospec=True
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
      video_generator_execution, "generate_audio_step", autospec=True
  )
  @mock.patch.object(
      video_generator_execution, "generate_storyboard_step", autospec=True
  )
  @mock.patch.object(
      video_generator_execution, "generate_video_step", autospec=True
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
    context = mock_generate_video_step.call_args[0][0]
    self.assertEqual(
        context.image_paths,
        [
            self.temp_work_dir.name + "/images/image1.jpg",
            self.temp_work_dir.name + "/images/image2.jpg",
        ],
    )


if __name__ == "__main__":
  unittest.main()
