import builtins
import json
import textwrap
import unittest
from unittest import mock
import storyboarding
from vertexai import generative_models

_SCENES = [
    storyboarding.Scene(
        image_path="image/path/1",
        start_time="00:00:00,000",
        focal_point=[0, 0, 1000, 500],
        main_subject=[0, 0, 1000, 1000],
    ),
    storyboarding.Scene(
        image_path="image/path/2",
        start_time="00:00:23,000",
        focal_point=[250, 0, 1000, 500],
        main_subject=[0, 250, 1000, 1000],
    ),
]

_TEXT_OVERLAYS = [
    storyboarding.TextOverlay(
        start_time=4.0,
        end_time=21.6,
        text="This is the content of the article.",
        speaker="",
        transition_in="slide_from_left",
        transition_out="fade_out",
        font_style="Helvetica",
        font_size=48,
        background_color="black",
        alignment="West",
        position=["left", "top"],
    )
]

_TEXT_OVERLAYS_TEXT_FILE = """[
 {"start_time": 4.0, "end_time": 16.0, "text": "James, a first-time homebuyer, purchased a townhouse after a six-month search in a competitive post-COVID housing market.", "speaker": "null", "transition_in": "slide_from_left", "transition_out": "fade_out", "font_style": "Helvetica", "font_size": 54, "position": ["left", "bottom"]},
 {"start_time": 21.0, "end_time": 35.0, "text": "He was drawn to the property's open layout, ample storage, large backyard, and, notably, its potential for Halloween decorating.", "speaker": "null", "transition_in": "fade_in", "transition_out": "fade_out", "font_style": "Helvetica", "font_size": 54, "position": ["right", "center"]}
]
"""

_SRT_FILE_CONTENT = """\
1
00:00:05,000 --> 00:00:10,000
This is some subtitle text.

2
00:00:15,000 --> 00:00:36,000
Another subtitle text.
"""


class CreateStoryBoardStepsTest(unittest.TestCase):

  @mock.patch.object(
      storyboarding.storyboard_steps, "create_scenes", autospec=True
  )
  @mock.patch.object(
      storyboarding.storyboard_steps, "create_text_overlays", autospec=True
  )
  @mock.patch.object(
      generative_models,
      "GenerativeModel",
      autospec=True,
  )
  @mock.patch.object(
      builtins,
      "open",
      new_callable=mock.mock_open,
  )
  def test_create_storyboard(
      self,
      mock_open,
      mock_generative_model,
      mock_create_text_overlays,
      mock_create_scenes,
  ):
    # Mock the return value of create_scenes()
    mock_create_scenes.return_value = _SCENES

    # Mock the return value of create_text_overlays()
    mock_create_text_overlays.return_value = [
        storyboarding.TextOverlay(**overlay)
        for overlay in json.loads(_TEXT_OVERLAYS_TEXT_FILE)
    ]

    # Mock Gemini
    mock_model_instance = mock.Mock()
    mock_generative_model.return_value = mock_model_instance

    # Simulate a response object with a valid JSON text attribute
    mock_response = mock.Mock()
    mock_response.text = _TEXT_OVERLAYS_TEXT_FILE
    mock_model_instance.generate_content.return_value = mock_response

    # Mock open for both text overlays and SRT file
    def mock_open_side_effect(file, *_args, **_kwargs):
      if file == "./output/text_overlays.json":
        return mock.mock_open(read_data=_TEXT_OVERLAYS_TEXT_FILE).return_value
      elif file == "/srt/path":
        return mock.mock_open(read_data=_SRT_FILE_CONTENT).return_value
      else:
        raise FileNotFoundError(f"Mock for {file} not found.")

    mock_open.side_effect = mock_open_side_effect

    storyboard = storyboarding.create_storyboard_step(
        image_paths=["image/path/1", "image/path/2"],
        main_audio_path="audio_path",
        srt_path="/srt/path",
        article_content="This is the content of the article.",
        generate_text_overlays=True,
    )

    storyboard.background_audio_path = "background_music/mild_neutral.mp3"

    self.assertEqual(
        storyboard,
        storyboarding.Storyboard(
            scenes=_SCENES,
            main_audio_path="audio_path",
            text_overlays=mock_create_text_overlays.return_value,
            background_audio_path="background_music/mild_neutral.mp3",
            srt_path="/srt/path",
        ),
    )

  @mock.patch.object(generative_models.Image, "load_from_file", autospec=True)
  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_scenes_test(self, mock_generate_content, *_):
    with mock.patch.object(
        builtins, "open", new_callable=mock.mock_open, read_data="srt content"
    ):
      mock_generate_content.return_value.text = textwrap.dedent("""\
        [
            {"image_path": "image/path/1",
            "start_time": "00:00:00,000",
            "focal_point": [0,0,1000,500],
            "main_subject": [0,0,1000,1000]},
            {"image_path": "image/path/2",
            "start_time": "00:00:23,000",
            "focal_point": [250,0,1000,500],
            "main_subject": [0,250,1000,1000]}
        ]""")

      scenes = storyboarding.create_scenes(
          ["image/path/1", "image/path/2"], "srt_path"
      )

      self.assertEqual(scenes, _SCENES)

  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_text_overlays_test(self, mock_generate_content, *_):
    with mock.patch.object(
        builtins,
        "open",
        new_callable=mock.mock_open,
        read_data=_SRT_FILE_CONTENT,
    ):
      mock_generate_content.return_value.text = json.dumps([{
          "start_time": 4.0,
          "end_time": 21.6,
          "text": "This is the content of the article.",
          "speaker": "",
          "transition_in": "slide_from_left",
          "transition_out": "fade_out",
          "font_style": "Helvetica",
          "font_size": 48,
          "background_color": "black",
          "alignment": "West",
          "position": ["left", "top"],
      }])
      text_overlays = storyboarding.create_text_overlays(
          article_content="This is the content of the article.",
          srt_parts=["SRT contents:", "SRT contents"],
          srt_end_time=30,
          scenes=_SCENES,
      )

    self.assertEqual(text_overlays, _TEXT_OVERLAYS)

  @mock.patch.object(generative_models.Image, "load_from_file", autospec=True)
  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_scenes_first_scene_starts_at_zero(
      self, mock_generate_content, _
  ):
    with mock.patch.object(
        builtins, "open", new_callable=mock.mock_open, read_data="srt content"
    ):
      # Mock the LLM response: first scene does NOT start at 00:00:00,000
      mock_generate_content.return_value.text = textwrap.dedent("""\
        [
            {"image_path": "image/path/1",
            "start_time": "00:00:05,000",
            "focal_point": [0,0,1000,500],
            "main_subject": [0,0,1000,1000]},
            {"image_path": "image/path/2",
            "start_time": "00:00:23,000",
            "focal_point": [250,0,1000,500],
            "main_subject": [0,250,1000,1000]}
        ]""")

      scenes = storyboarding.create_scenes(
          ["image/path/1", "image/path/2"], "srt_path"
      )

      expected_scenes = [
          storyboarding.Scene(
              image_path="image/path/1",
              start_time="00:00:00,000",  # corrected
              focal_point=[0, 0, 1000, 500],
              main_subject=[0, 0, 1000, 1000],
          ),
          storyboarding.Scene(
              image_path="image/path/2",
              start_time="00:00:23,000",
              focal_point=[250, 0, 1000, 500],
              main_subject=[0, 250, 1000, 1000],
          ),
      ]
      self.assertEqual(scenes, expected_scenes)
      self.assertEqual(scenes[0].start_time, "00:00:00,000")

  @mock.patch.object(generative_models.Image, "load_from_file", autospec=True)
  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_scenes_deduplicates_start_times(
      self, mock_generate_content, _
  ):
    with mock.patch.object(
        builtins, "open", new_callable=mock.mock_open, read_data="srt content"
    ):
      # Mock LLM response with duplicate start times
      mock_generate_content.return_value.text = textwrap.dedent("""\
        [
            {"image_path": "image/path/1",
            "start_time": "00:00:00,000",
            "focal_point": [0,0,1000,500],
            "main_subject": [0,0,1000,1000]},
            {"image_path": "image/path/duplicate",
            "start_time": "00:00:05,000",
            "focal_point": [0,0,100,100],
            "main_subject": [0,0,200,200]},
            {"image_path": "image/path/2",
            "start_time": "00:00:05,000",
            "focal_point": [250,0,1000,500],
            "main_subject": [0,250,1000,1000]}
        ]""")

      scenes = storyboarding.create_scenes(
          ["image/path/1", "image/path/duplicate", "image/path/2"], "srt_path"
      )

      # Expecting the second scene with "00:00:05,000" to be dropped
      expected_scenes = [
          storyboarding.Scene(
              image_path="image/path/1",
              start_time="00:00:00,000",
              focal_point=[0, 0, 1000, 500],
              main_subject=[0, 0, 1000, 1000],
          ),
          storyboarding.Scene(
              image_path="image/path/duplicate",
              start_time="00:00:05,000",
              focal_point=[0, 0, 100, 100],
              main_subject=[0, 0, 200, 200],
          ),
      ]
      self.assertEqual(scenes, expected_scenes)
      # Verify no duplicate start times
      start_times = [scene.start_time for scene in scenes]
      self.assertEqual(len(start_times), len(set(start_times)))

  @mock.patch.object(generative_models.Image, "load_from_file", autospec=True)
  @mock.patch.object(
      generative_models.GenerativeModel, "generate_content", autospec=True
  )
  def test_create_scenes_sorts(self, mock_generate_content, _):
    with mock.patch.object(
        builtins, "open", new_callable=mock.mock_open, read_data="srt content"
    ):
      # Mock LLM response with out-of-order start times
      mock_generate_content.return_value.text = textwrap.dedent("""\
        [
            {"image_path": "image/path/two",
            "start_time": "00:00:15,000",
            "focal_point": [0,0,100,100],
            "main_subject": [0,0,200,200]},
            {"image_path": "image/path/zero",
            "start_time": "00:00:00,000",
            "focal_point": [0,0,1000,500],
            "main_subject": [0,0,1000,1000]},
            {"image_path": "image/path/three",
            "start_time": "00:00:20,000",
            "focal_point": [1,1,1,1],
            "main_subject": [2,2,2,2]},
            {"image_path": "image/path/one",
            "start_time": "00:00:10,000",
            "focal_point": [250,0,1000,500],
            "main_subject": [0,250,1000,1000]}
        ]""")

      scenes = storyboarding.create_scenes(
          [
              "image/path/late",
              "image/path/early",
              "image/path/duplicate_late",
              "image/path/middle",
          ],
          "srt_path",
      )

      expected_scenes = [
          storyboarding.Scene(
              image_path="image/path/zero",
              start_time="00:00:00,000",
              focal_point=[0, 0, 1000, 500],
              main_subject=[0, 0, 1000, 1000],
          ),
          storyboarding.Scene(
              image_path="image/path/one",
              start_time="00:00:10,000",
              focal_point=[250, 0, 1000, 500],
              main_subject=[0, 250, 1000, 1000],
          ),
          storyboarding.Scene(
              image_path="image/path/two",
              start_time="00:00:15,000",
              focal_point=[0, 0, 100, 100],
              main_subject=[0, 0, 200, 200],
          ),
          storyboarding.Scene(
              image_path="image/path/three",
              start_time="00:00:20,000",
              focal_point=[1, 1, 1, 1],
              main_subject=[2, 2, 2, 2],
          ),
      ]
      self.assertEqual(scenes, expected_scenes)
      self.assertTrue(
          all(
              scenes[i].start_time <= scenes[i + 1].start_time
              for i in range(len(scenes) - 1)
          )
      )
