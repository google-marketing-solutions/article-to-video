"""Steps to for Storyboard creation."""

import json
import textwrap

import storyboarding
from storyboarding.model import TextOverlay
from vertexai import generative_models


def serialize_scenes(scenes: list[storyboarding.ImageScene]) -> str:
  """Convert scenes into a string format for inclusion in the Gemini prompt."""
  serialized_scenes = []
  for scene in scenes:
    serialized_scenes.append(
        f"Scene start_time: {scene.start_time}, image_path: {scene.image_path}"
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


def _describe_images(image_file_paths: list[str]) -> str:
  """Describes images for create_scenes method.

  Returns a human readable description and two bounding boxes for each imes.

  Args:
    image_file_paths: The images to describe.

  Returns:
     A human readable description and two bounding boxes for each image.
     One bounding box around the main subject of the image and another around
     the focal point. The list is organized by the file name.
  """
  prompt = textwrap.dedent("""\
    You are a highly advanced computer vision system working for a stock photo
    provider. Your primary objective is to analyze images and provide detailed
    descriptions along with precise bounding box coordinates.  You will receive
    images encoded as base64 strings, and identified by their filenames.

    Input:
    - Image List: A list of images, identified by their file paths that need to
    be analyzed.

    Output:
    For each image, generate the following:
    - description: A detailed description of the image, mentioning prominent
    objects, people, activities, setting, and overall mood. Be objective and
    avoid subjective interpretations. Focus on factual details and avoid
    creative writing.
    - main subject bounding box: Bounding box around the primary subject of the
    image with a description [ymin, xmin, ymax, xmax]
    - focal point bounding box: Bounding box around the focal point of the image
    with a description [ymin, xmin, ymax, xmax]

    Guidelines:
    - Accuracy: Bounding boxes must accurately encompass the intended regions.
    ymin, xmin, ymax, and xmax values should be normalized ints between 0 and
    1000, representing the fraction of the image's height and width. (0,0)
    corresponds to the top-left corner.
    - Objectivity: Descriptions should be factually accurate and avoid
    subjective interpretations, opinions, or assumptions about the image's
    meaning or purpose. Stick to observable details. Avoid phrases like "looks
    like," "appears to be," "might be," etc.
    - Detail: Descriptions should be as detailed as possible, encompassing all
    significant elements within the image. Include details about objects, people
    (if any), activities, setting, lighting, and overall mood conveyed by the
    image. Be specific with object descriptions (e.g., "red leather armchair"
    instead of just "chair").
    - Conciseness: While detailed, descriptions should be concise and avoid
    unnecessary verbosity.
    - No Image URLs: Do not attempt to generate URLs or access external
    resources. All necessary information is contained within the base64 encoded
    image.

    Focal Point vs. Main Subject: The **main subject** is the overall dominant
    element in the image, the core "thing" the picture is about. The **focal
    point** is a specific area within or near the main subject that draws the
    viewer's immediate attention and serves as a visual anchor.

    1. Single Person Portrait:
    - Main Subject: The entire person.
    - Focal Point: The person's face, specifically the eyes.

    2. Group of People:
    - Main Subject: The group as a whole.
    - Focal Point:  A cluster encompassing as many faces as possible. If one
    person is clearly central or interacting, prioritize their face.

    3. Landscape/Nature Scene:
    - Main Subject: The overall scene (e.g., a mountain range, forest,
    seascape).
    - Focal Point: Look for elements that create a strong visual impact:
      * Leading Lines: Where do lines (roads, rivers, fences) converge?
      * Rule of Thirds: Are any key elements positioned at the intersection
        points of a 3x3 grid overlay?
      * Contrast: Is there an area of high contrast (light vs. dark, color
        difference) that draws the eye?
      * Unique Elements: A solitary tree, a distinctive rock formation, a
        waterfall.

    4. Object Photography (Still Life/Product):
    - Main Subject: The object itself.
    - Focal Point: A key detail or feature that highlights the object's design,
      texture, or function. For example:
      * A logo on a product.
      * A unique texture or pattern.
      * A point of reflection or highlight.

    5. Architectural Images:
    - Main Subject: The building or structure.
    - Focal Point: Consider:
      * Entrance/Doorway: Often a natural point of entry and interest.
      * Distinctive Architectural Features: Towers, arches, unique window
        designs.
      * Lines and Perspective: Leading lines or strong perspective points.

    6. Action/Sports Shots:
    - Main Subject: The person or object in motion.
    - Focal Point:  Typically the face of the athlete or the point of action
      (e.g., a ball, a point of contact). Consider the direction of movement –
      the focal point should anticipate or follow the action.

    7. Abstract Images:
    - Main Subject:  The overall composition of shapes, colors, and textures.
    - Focal Point: Can be more subjective but look for:
      * Areas of high contrast or visual weight.
      * Patterns that lead the eye.
      * A central element or anomaly.

    Additional Considerations:
    - Depth of Field: If the image has a shallow depth of field (blurry
      background), the in-focus area is likely the focal point.
    - Lighting: Brightly lit areas often draw the eye more effectively.
    - Context: Consider the story or message the image conveys. The focal
      point should reinforce that narrative.
    - The focal point should be as small as is realistically possible.

    **Example**

    Image List:
    /path/to/image/dog.jpg:
    [image]
    /path/to/image/garden.jpg:
    [image]

    Output:
    /path/to/image/dog.jpg:
    - Description: A brown dog with white paws sits on a green grassy field. The
    dog is facing the camera and has its tongue slightly out. The background
    includes a blue sky with a few scattered white clouds. A small red ball lies
    near the dog's front paws.
    - Main Subject Bounding Box: The main subject is the dog [ymin, xmin, ymax,
      xmax]
    - Focal Point Bounding Box: The focal point is the dog's eyes [ymin, xmin,
    ymax, xmax]

    /path/to/image/garden.jpg:
    - Description: A close-up of a blooming red rose. The petals are velvety and
    slightly unfurled. Water droplets cling to the petals. The background is a
    blurred green foliage.
    - Main Subject Bounding Box: The entire rose, including the stem [ymin,
      xmin, ymax, xmax]
    - Focal Point Bounding Box: The rose petals and bud [ymin, xmin, ymax, xmax]
  """)
  model = generative_models.GenerativeModel("gemini-1.5-pro-002")
  image_parts = ["Image List:"]
  for path in image_file_paths:
    image_parts.extend([path, generative_models.Image.load_from_file(path)])
  response = model.generate_content([prompt, *image_parts])
  return response.text


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
    narration and generate a schedule to display the images.

    Input:
    - SRT Contents: The SRT contains timestamps and the corresponding narration
    for the slideshow.
    - Image List: A list of images, identified by their file paths that can be
    included in the slideshow.

    Output:
    A structured list specifying the following for each image in the slideshow:
    - File Path: The complete path to the image file.
    - Start Time (Timestamp): The precise time (in the same format as the SRT
      timestamps) when the image should appear. This timestamp should align
      logically with the narration in the SRT file.
    - Bounding Boxes: Two bounding boxes associated with the image (if
      provided).
    - Justification for Start Time: Describe your reasoning for choosing the
    specific start time you choose. Does the image content align with an SRT
    cue, is it being placed to make sure the slideshow elements are evenly
    spaced, or some other reason.

    Instructions:
    1. Logical Alignment: Prioritize aligning image timestamps with the content
    of the SRT cues. If an image directly illustrates a specific subtitle, its
    timestamp should match that subtitle's start time.
    2. Thematic Images: You can include images that thematically relate to the
    overall content of the SRT file, even if they don't perfectly match a
    specific subtitle.
    3. Uniform Distribution of Thematic Images:  *Crucially*, for thematic
    images that don't align with specific SRT queues, distribute them **evenly
    across the entire duration** of the SRT file. Calculate the total duration
    of the SRT file and divide it into equal segments for placing these thematic
    images. For instance, if the SRT file is 60 seconds long and you have 3
    thematic images, place them at approximately 20, 40, and 60 seconds. Do not
    have any images start after the last entry in the SRT file.
    4. Maximize Spacing: Regardless of whether an image aligns directly with an
    SRT queue or is thematic, ensure that the image start times are spaced as
    far apart as possible within the overall SRT duration. **Avoid clustering
    images at the beginning.**
    5. The minimum time between images should be about 5 seconds. Prefer at
    least ~10 seconds between cues.
    6. Relevance: Only include images that are relevant to the content of the
    SRT file. Omit irrelevant images.

    **Example**

    SRT Contents:
    1 00:00:00,000 --> 00:00:05,000 This is a story about a cat named Mittens.
    2 00:00:05,000 --> 00:00:10,000 Mittens loved to play in the garden.
    3 00:00:10,000 --> 00:00:15,000 One day, Mittens chased a butterfly.

    Image List:
    /path/to/image/cat.jpg:
    - Description: [description]
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]
    /path/to/image/garden.jpg:
    - Description: [description]
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]
    /path/to/image/butterfly.jpg:
    - Description: [description]
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]
    /path/to/image/dog.jpg:
    - Description: [description]
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]

    Output:
    00:00:00,000 /path/to/image/cat.jpg
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]
    00:00:05,000 /path/to/image/garden.jpg
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]
    00:00:10,000 /path/to/image/butterfly.jpg
    - Main Subject Bounding Box: [ymin, xmin, ymax, xmax]
    - Focal Point Bounding Box: [ymin, xmin, ymax, xmax]
  """)
  model = generative_models.GenerativeModel("gemini-1.5-pro-002")
  image_parts = ["Image List:", _describe_images(image_file_paths)]
  with open(srt_file_path, "r", encoding="utf-8") as srt_file:
    srt_parts = ["SRT Contents:", srt_file.read()]

  response_schema = {
      "type": "array",
      "items": {
          "type": "object",
          "properties": {
              "start_time": {"type": "number"},
              "image_path": {"type": "string"},
              "main_subject": {
                  "type": "array",
                  "items": {"type": "number"},
              },
              "focal_point": {
                  "type": "array",
                  "items": {"type": "number"},
              },
          },
          "required": [
              "start_time",
              "image_path",
              "main_subject",
              "focal_point",
          ],
      },
  }
  response = model.generate_content(
      [task_for_prompt, *image_parts, *srt_parts],
      generation_config=generative_models.GenerationConfig(
          temperature=1.4,
          response_schema=response_schema,
          response_mime_type="application/json",
      ),
  )
  scene_list_json = json.loads(response.text)
  return [storyboarding.ImageScene(**j) for j in scene_list_json]


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
