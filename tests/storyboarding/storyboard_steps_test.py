import builtins
import json
import textwrap
import unittest
from unittest import mock
import storyboarding
from vertexai import generative_models

_SCENES = [
    storyboarding.Scene(background_image_path="image/path/1", start_time=0),
    storyboarding.Scene(background_image_path="image/path/2", start_time=23.0),
]

_TEXT_OVERLAYS = [
    storyboarding.TextOverlay(
        start_time=4.0,
        end_time=21.6,
        text="This is the content of the article.",
        speaker=None,
        transition_in="slide_from_left",
        transition_out="fade_out",
        font_style="Helvetica",
        font_size=48,
        background_color="black",
        alignment="West",
        position=["Left", "Top"],
    )
]


class CreateStoryBoardStepsTest(unittest.TestCase):

  @mock.patch.object(
      builtins, "open", new_callable=mock.mock_open, read_data="srt content"
  )
  @mock.patch.object(generative_models.Image, "load_from_file", autospec=True)
  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_scenes_test(self, mock_generate_content, *_):
    mock_generate_content.return_value.text = textwrap.dedent("""\
    [
        {"background_image_path": "image/path/1", "start_time": 0},
        {"background_image_path": "image/path/2", "start_time": 23.0}
    ]""")

    scenes = storyboarding.create_scenes(
        ["image/path/1", "image/path/2"], "srt_path"
    )

    self.assertEqual(scenes, _SCENES)

  @mock.patch.object(
      builtins, "open", new_callable=mock.mock_open, read_data="srt content"
  )
  @mock.patch.object(generative_models.Image, "load_from_file", autospec=True)
  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_text_overlays_test(self, mock_generate_content, *_):
    mock_generate_content.return_value.text = json.dumps([{
        "start_time": 4.0,
        "end_time": 21.6,
        "text": "This is the content of the article.",
        "speaker": None,
        "transition_in": "slide_from_left",
        "transition_out": "fade_out",
        "font_style": "Helvetica",
        "font_size": 48,
        "background_color": "black",
        "alignment": "West",
        "position": ["Left", "Top"],
    }])
    text_overlays = storyboarding.create_text_overlays(
        article_content="This is the content of the article.",
        srt_file_path="srt content",
        scenes=_SCENES,
    )

    self.assertEqual(text_overlays, _TEXT_OVERLAYS)

  @mock.patch.object(storyboarding, "create_scenes", autospec=True)
  @mock.patch.object(
      builtins,
      "open",
      new_callable=mock.mock_open,
      read_data="Mock SRT content",
  )
  def test_create_storyboard(self, _, mock_create_scenes):
    mock_create_scenes.return_value = _SCENES
    storyboard = storyboarding.create_storyboard_step(
        image_paths=["image/path/1", "image/path/2"],
        main_audio_path="audio_path",
        srt_path="srt_path",
        article_content="This is the content of the article.",
    )
    storyboard.text_overlays = []
    self.assertEqual(
        storyboard,
        storyboarding.Storyboard(
            scenes=_SCENES,
            main_audio_path="audio_path",
        ),
    )
