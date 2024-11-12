"""Steps to for Storyboard creation."""

import json
import textwrap
import storyboarding
from vertexai import generative_models


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
) -> storyboarding.Storyboard:
  """Assembles a Storyboard for video generation.

  Args:
    image_paths: The file paths to the images to be used in the slideshow
    main_audio_path: The file path for the main audio (narration)
    srt_path: The file path for the SRT file

  Returns:
    A Storyboard.
  """
  return storyboarding.Storyboard(
      scenes=storyboarding.create_scenes(
          image_file_paths=image_paths,
          srt_file_path=srt_path,
      ),
      main_audio_path=main_audio_path,
  )
