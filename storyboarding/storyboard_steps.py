"""Steps to for Storyboard creation."""

import json
import textwrap

import storyboarding
from storyboarding.model import TextOverlay
from vertexai import generative_models


def serialize_scenes(scenes: list[storyboarding.Scene]) -> str:
  """Convert scenes into a string format for inclusion in the Gemini prompt."""
  serialized_scenes = []
  for scene in scenes:
    serialized_scenes.append(
        f"Scene start_time: {scene.start_time}, "
        f"background_image_path: {scene.background_image_path}"
    )
  return "\n".join(serialized_scenes)


def create_text_overlays(
    article_content: str, srt_file_path: str, scenes: storyboarding.Scene
) -> list[TextOverlay]:
  """Determines text overlays (what they say and when in the video they appear).

  Takes the article content and an SRT file and determines what text overlays
  should be in the video, and when they should appear.

  Args:
    article_content: Text of the article.
    srt_file_path: The SRT file to organize the images against.
    scenes: visual scenes for the video

  Returns:
     A list of TextOverlays.
  """
  serialized_scenes = serialize_scenes(scenes)

  task_for_prompt = textwrap.dedent("""\
  You are a digital media expert tasked with creating impactful text overlays
  for a narrated video based on an article.

  Given:
  Article Content: The full text of the article.
  SRT File: A subtitle file with timestamps and corresponding text for the video
  narration.
  Scenes: A list of scenes with start times and background image paths.
  Output:
  Produce a JSON array of text overlay objects, each with the following
  properties:

  start_time: (number) When the overlay appears in the video (seconds).
  end_time: (number) When the overlay disappears (seconds).
  text: (string) The text to display.
  speaker: (optional, string or null) The person quoted (from the article, not
    the narrator).
  transition_in: (optional, string or null) "slide_from_left",
    "slide_from_right", "slide_from_bottom", or "fade_in".
  transition_out: (optional, string or null) "fade_out"
  position: (optional, array of strings) X and Y coordinates ("left", "center",
    "right") and ("top", "center", "bottom"). Example: ["right", "center"]
  font_style: (optional, string, default "Helvetica")
  font_size: (optional, number, default 48) Minimum size 48.
  background_color: (optional, string, default "black")
  Rules:

  Prioritize direct quotes from the article.
  Minimum 3 words, maximum 35 words per overlay.
  No overlays in the first 4 seconds of the video.
  One overlay every 15-20 seconds.
  Minimum display time per overlay: 14 seconds.
  Overlay duration: 0.3 seconds per word + 4 seconds buffer.
  Vary overlay positions and transitions. No two overlays should have the same x
    or y position.
  Ensure text is legible against the background image.
  Example Output:

  JSON
  [
    {
      "start_time": 4.5,
      "end_time": 18.5,
      "text": "The future belongs to those who believe in beautiful dreams.",
      "speaker": "Eleanor Roosevelt",
      "transition_in": "fade_in",
      "transition_out": "fade_out",
      "position": ["left", "top"]
    },
    {
      "start_time": 23.0,
      "end_time": 38.0,
      "text": "'The only way to do great work is to love what you do.'",
      "speaker": "Steve Jobs",
      "transition_in": "slide_from_right",
      "transition_out": "fade_out",
      "position": ["right", "bottom"]
    }
  ]
  """)
  model = generative_models.GenerativeModel("gemini-1.5-pro-001")
  with open(srt_file_path, "r", encoding="utf-8") as srt_file:
    srt_parts = ["SRT Contents:", srt_file.read()]
  response_schema = {
      "type": "array",
      "items": {
          "type": "object",
          "properties": {
              "start_time": {"type": "number"},
              "end_time": {"type": "number"},
              "text": {"type": "string"},
              "speaker": {"type": "string", "default": None},
              "transition_in": {
                  "type": "string",
                  "enum": [
                      "slide_from_left",
                      "slide_from_right",
                      "slide_from_bottom",
                      "fade_in",
                  ],
                  "default": "fade_in",
              },
              "transition_out": {
                  "type": "string",
                  "enum": ["fade_out"],
                  "default": "fade_out",
              },
              "font_style": {
                  "type": "string",
                  "default": "Helvetica",
                  "enum": [
                      "Helvetica",
                      "Times",
                      "Courier",
                      "Garamond",
                      "Georgia",
                      "Impact",
                      "Lucida",
                      "Monaco",
                      "Palatino",
                      "Roboto",
                      "Rockwell",
                      "Sans",
                      "Serif",
                      "Symbol",
                      "Tahoma",
                      "Verdana",
                      "Zapfino",
                  ],
              },
              "font_size": {"type": "number", "default": 24},
              "position": {
                  "type": "array",
                  "items": {
                      "type": "string",
                      "enum": ["left", "center", "right", "top", "bottom"],
                  },
                  "minItems": 2,
                  "maxItems": 2,
                  "default": ["center", "center"],
              },
          },
          "required": [
              "start_time",
              "end_time",
              "text",
              "transition_in",
              "transition_out",
              "position",
          ],
      },
  }
  response = model.generate_content(
      [*srt_parts, article_content, serialized_scenes, task_for_prompt],
      generation_config=generative_models.GenerationConfig(
          temperature=1.4,
          response_schema=response_schema,
          response_mime_type="application/json",
      ),
  )
  text_overlay_list_json = json.loads(response.text)
  return [
      storyboarding.TextOverlay(**overlay) for overlay in text_overlay_list_json
  ]


def create_scenes(
    image_file_paths: list[str], srt_file_path: str
) -> list[storyboarding.Scene]:
  """Organizes images into logical scenes based on an SRT file.

  Args:
    image_file_paths: The images to use as background images in the scenes.
    srt_file_path: The SRT file to organize the images against.

  Returns:
    A list of Scenes
  """
  task_for_prompt = textwrap.dedent("""\
    You are an expert slideshow creator with a keen eye for visual storytelling.
    Your task is to analyze a provided SRT file (containing timestamps and
    transcribed narration) and a list of image files. Based on the SRT file's
    content, you will determine the most appropriate images to accompany the
    narration and generate a schedule for their display.

    Input:
    - SRT Contents: The SRT contains timestamps and the corresponding narration
    for the slideshow.
    - Image List: A list of images, identified by their file paths that can be
    included in the slideshow.

    Output:
    - Produce a list of image file paths along with timestamps indicating when
    each image should appear in the slideshow. These timestamps should align
    logically with the narration in the SRT file.
    - You may repeat images if it makes sense to do so.
    - Space the image start times out as much as possible. For a 30 second
    slideshow with 3 images, having cues at 0, 10, 20 is better than 0, 2, 6.
    - Any images that are irrelevant to the SRT file's content should be
    omitted.

    **Example**

    SRT Contents:
    1 00:00:00,000 --> 00:00:05,000 This is a story about a cat named Mittens.
    2 00:00:05,000 --> 00:00:10,000 Mittens loved to play in the garden.
    3 00:00:10,000 --> 00:00:15,000 One day, Mittens chased a butterfly.

    Image List:
    /path/to/image/cat.jpg:
    [image]
    /path/to/image/garden.jpg:
    [image]
    /path/to/image/butterfly.jpg:
    [image]
    /path/to/image/dog.jpg:
    [image]

    Output:
    00:00:00,000 /path/to/image/cat.jpg
    00:00:05,000 /path/to/image/garden.jpg
    00:00:10,000 /path/to/image/butterfly.jpg
  """)
  model = generative_models.GenerativeModel("gemini-1.5-pro-001")
  image_parts = ["Image List:"]
  for p in image_file_paths:
    image_parts.extend([p, generative_models.Image.load_from_file(p)])
  with open(srt_file_path, "r", encoding="utf-8") as srt_file:
    srt_parts = ["SRT Contents:", srt_file.read()]

  response_schema = {
      "type": "array",
      "items": {
          "type": "object",
          "properties": {
              "start_time": {"type": "number"},
              "background_image_path": {"type": "string"},
          },
          "required": ["start_time", "background_image_path"],
      },
  }
  response = model.generate_content(
      [*image_parts, *srt_parts, task_for_prompt],
      generation_config=generative_models.GenerationConfig(
          temperature=1.4,
          response_schema=response_schema,
          response_mime_type="application/json",
      ),
  )
  scene_list_json = json.loads(response.text)
  return [storyboarding.Scene(**j) for j in scene_list_json]


def create_storyboard_step(
    image_paths: list[str],
    main_audio_path: str,
    srt_path: str,
    article_content: str,
) -> storyboarding.Storyboard:
  """Assembles a Storyboard for video generation.

  Args:
    image_paths: The file paths to the images to be used in the slideshow
    main_audio_path: The file path for the main audio (narration)
    srt_path: The file path for the SRT file
    article_content: Text of the article.

  Returns:
    A Storyboard.
  """
  scenes = storyboarding.create_scenes(
      image_file_paths=image_paths,
      srt_file_path=srt_path,
  )
  text_overlays = storyboarding.create_text_overlays(
      article_content, srt_path, scenes
  )

  return storyboarding.Storyboard(
      scenes=scenes,
      main_audio_path=main_audio_path,
      text_overlays=text_overlays,
  )
