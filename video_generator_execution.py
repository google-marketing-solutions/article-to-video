#!/usr/bin/env python
# Copyright 2024 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generates a narrated video with subtitles from news articles and images.

This is a standalone script which takes as input an article text in .txt
 format and pictures (each with the same prefix plus a number starting from 0).
It will generate a video out of the concatenated images and text summarization,
 along with narrated audio and srt subtitles.

Added for Gemini TTS language support: Updated to use Gemini 2.5 Pro TTS which
supports 83 languages
(24 GA + 59 Preview). Language choices are dynamically loaded from
pipeline.SUPPORTED_LANGUAGES.

Typical usage example:
"""

import argparse
import hashlib
import logging
import os
import sys
from typing import Any, Iterable, Tuple
import uuid
from audio import subtitles_generation_step
from audio import text_to_speech_step
import pipeline
import storyboarding
import text
import vertexai
import video
import yaml

SCRIPT_FILE_NAME = "1_script.json"

AUDIO_FILE_NAME = "2_readaloud.wav"

SRT_FILE_NAME = "3_subtitles.srt"

STORYBOARD_FILE_NAME = "4_storyboard.json"

OUTPUT_VIDEO_FILE_NAME = "5_withaudiovideo.mp4"

OUTPUT_AUDIO_FILE_NAME = "6_finalaudio.mp3"


class VideoGenerator:
  """Orchestrates the video generation process by managing various steps.

  This class encapsulates the logic for generating audio, creating a storyboard,
  and producing the final video output. It utilizes a `ScriptGenerator` for
  text processing and interacts with various pipeline steps for each stage of
  the video creation.
  """

  def __init__(
      self,
      script_generator: text.ScriptGenerator | None = None,
  ):
    """Initializes the VideoGenerator.

    Args:
      script_generator: An instance of `text.ScriptGenerator` used for
        generating scripts from article content. Defaults to a ScriptGenerator
        configured for 2 speakers.
    """
    self.logger = logging.getLogger(self.__class__.__name__)
    self._script_generator = script_generator or text.ScriptGenerator(
        speakers=2
    )

  def _save_signature(
      self,
      signature_file_path: os.PathLike[str],
      data_deps: Iterable[Any],
      file_deps: Iterable[os.PathLike[str]] | None = None,
  ) -> str:
    """Saves a signature hash for a given set of dependencies.

    This is used for caching purposes to determine if a step needs to be
    re-run.

    Args:
      signature_file_path: The path where the signature file will be saved.
      data_deps: An iterable of data dependencies to include in the signature.
        Each item will be converted to its string representation.
      file_deps: An optional iterable of file paths whose contents will be
        included in the signature.

    Returns:
      The hash signature as a string.
    """
    files = file_deps or []
    signature = hashlib.sha256()
    for dep in data_deps:
      signature.update(str(dep).encode("utf-8"))
    for file_path in files:
      with open(file_path, "rb") as f:
        signature.update(f.read())
    hexdigest = signature.hexdigest()

    dirname = os.path.dirname(signature_file_path)
    os.makedirs(dirname, exist_ok=True)
    with open(signature_file_path, "w", encoding="utf-8") as f:
      f.write(hexdigest)
    return hexdigest

  def _load_signature(
      self, signature_file_path: os.PathLike[str]
  ) -> str | None:
    """Loads a previously saved signature hash from a file.

    Args:
      signature_file_path: The path to the signature file.

    Returns:
      The signature hash as a string if the file exists, otherwise None.
    """
    if not os.path.exists(signature_file_path):
      return None
    with open(signature_file_path, "r", encoding="utf-8") as f:
      return f.read()

  def _is_output_cache_valid(
      self,
      output_paths_to_check: list[os.PathLike[str]],
      signature_file_path: os.PathLike[str],
      current_data_deps: Iterable[Any],
      current_file_deps: Iterable[os.PathLike[str]] | None = None,
  ) -> bool:
    """Determines if cached outputs can be used based on a signature.

    Compares a newly generated signature (based on current dependencies)
    with a cached signature. The cached signature is overwritted with the new
    signature.

    Args:
      output_paths_to_check: A list of file paths that are expected to exist if
        the cache is valid.
      signature_file_path: The path to the file storing the cached signature.
      current_data_deps: An iterable of data dependencies for generating the
        current signature. Each item will be converted to its string
        representation.
      current_file_deps: An optional iterable of file path dependencies for
        generating the current signature.

    Returns:
      True if the cached output can be used, False otherwise.
    """
    current_file_deps = current_file_deps or []
    if not all([os.path.exists(path) for path in output_paths_to_check]):
      return False

    cached_signature = self._load_signature(signature_file_path)
    current_signature = self._save_signature(
        signature_file_path,
        data_deps=current_data_deps,
        file_deps=current_file_deps,
    )
    return cached_signature == current_signature

  def generate_script_step(
      self, context: pipeline.VideoGenerationContext
  ) -> text.VoiceoverScript:
    """Generates a voiceover script from the provided article content.

    Args:
      context: The `VideoGenerationContext` containing configuration and data
        for the script generation process.

    Returns:
      The generated voiceover script.
    """
    script_path = os.path.join(context.workdir, SCRIPT_FILE_NAME)
    script_meta_path = os.path.join(context.workdir, ".meta", "script.meta")

    if self._is_output_cache_valid(
        output_paths_to_check=[script_path],
        signature_file_path=script_meta_path,
        current_data_deps=[context],
    ):
      self.logger.info("Using cached script...")
      return text.load_script(script_path)

    self.logger.info("Generating new script...")

    os.makedirs(context.workdir, exist_ok=True)
    script_path = os.path.join(context.workdir, SCRIPT_FILE_NAME)
    self._script_generator.language = context.language
    self._script_generator.speakers = 2 if context.multivoice else 1
    self._script_generator.multitext = context.multitext
    return self._script_generator.generate(context.article_content, script_path)

  def generate_audio_step(
      self, context: pipeline.VideoGenerationContext
  ) -> Tuple[os.PathLike[str], str]:
    """Generates audio and subtitles from the provided article content.

    Args:
      context: The `VideoGenerationContext` containing configuration and data
        for the audio generation process.

    Returns:
      A tuple containing the local path to the generated audio file and the
      local path to the generated SRT file.
    """
    script = self.generate_script_step(context)

    audio_path = os.path.join(context.workdir, AUDIO_FILE_NAME)
    srt_path = os.path.join(context.workdir, SRT_FILE_NAME)
    audio_meta_path = os.path.join(context.workdir, ".meta", "audio.meta")

    if self._is_output_cache_valid(
        output_paths_to_check=[audio_path, srt_path],
        signature_file_path=audio_meta_path,
        current_data_deps=[context, script],
    ):
      self.logger.info("Using cached audio...")
      return (audio_path, srt_path)
    self.logger.info("Generating new audio...")

    audio_path, audio_gcs_uri, script_text = (
        text_to_speech_step.TextToSpeechStep(context).process(script)
    )
    subtitles_generation_step.SubtitlesGenerationStep(context).process(
        (audio_gcs_uri, script_text)
    )
    return audio_path, srt_path

  def generate_storyboard_step(
      self, context: pipeline.VideoGenerationContext
  ) -> storyboarding.Storyboard:
    """Creates a storyboard from images, audio, and subtitle information.

    If the audio and SRT files do not exist, this method will first trigger
    the `generate_audio_step`.

    Args:
      context: The `VideoGenerationContext` containing all necessary inputs like
        image paths, article content, and audio/SRT file locations.

    Returns:
      A `Storyboard` object representing the generated storyboard.
    """
    audio_path, srt_path = self.generate_audio_step(context)

    storyboard_path = os.path.join(context.workdir, STORYBOARD_FILE_NAME)
    storyboard_meta_path = os.path.join(
        context.workdir, ".meta", "storyboard.meta"
    )
    if self._is_output_cache_valid(
        output_paths_to_check=[storyboard_path],
        signature_file_path=storyboard_meta_path,
        current_data_deps=[context],
        current_file_deps=[srt_path],
    ):
      self.logger.info("Using cached storyboard...")
      return storyboarding.load_storyboard(storyboard_path)
    self.logger.info("Generating new storyboard...")

    return storyboarding.create_storyboard_step(
        article_content=context.article_content,
        image_paths=context.image_paths,
        main_audio_path=audio_path,
        srt_path=srt_path,
        generate_text_overlays=not context.disable_text_overlays,
        splash_image=context.splash_image,
        output_file_path=storyboard_path,
        gcp_project=context.gcp_project,
    )

  def generate_video_step(
      self, context: pipeline.VideoGenerationContext
  ) -> os.PathLike[str]:
    """Generates the final video output from a storyboard.

    If a storyboard file exists, it's loaded; otherwise, it's generated by
    calling `generate_storyboard_step`.

    Args:
      context: The `VideoGenerationContext` providing access to the storyboard
        and output video configuration.

    Returns:
      The local path to the generated video file.
    """
    storyboard = self.generate_storyboard_step(context)

    video_meta_path = os.path.join(context.workdir, ".meta", "video.meta")
    video_path = os.path.join(context.workdir, OUTPUT_VIDEO_FILE_NAME)

    if self._is_output_cache_valid(
        output_paths_to_check=[video_path],
        signature_file_path=video_meta_path,
        current_data_deps=[context, storyboard],
    ):
      self.logger.info("Using cached video...")
      return video_path
    self.logger.info("Generating new video...")

    return video.GenerateVideoFromImagesStep(
        output_audio_path=f"{context.workdir}/{OUTPUT_AUDIO_FILE_NAME}",
        output_video_path=f"{context.workdir}/{OUTPUT_VIDEO_FILE_NAME}",
        burn_in_subtitles=context.burn_in_subtitles,
    ).process(storyboard)


def _parse_args(args=sys.argv[1:]) -> argparse.Namespace:
  """Parses command-line arguments for the video generation script.

  Args:
    args: A list of command-line arguments. Defaults to sys.argv[1:].

  Returns:
    An argparse.Namespace object containing the parsed arguments.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--config",
      "-c",
      type=str,
      default="config.yml",
      help="Path to the configuration YAML file. Defaults to 'config.yml'.",
  )
  parser.add_argument(
      "--video_id",
      type=str,
      default=None,
      help=(
          "Unique ID for the generated video. If not provided, a UUID will be"
          " generated."
      ),
  )
  parser.add_argument(
      "--article_path",
      "-a",
      type=argparse.FileType("r"),
      required=True,
      help="Path to the article text file.",
  )
  parser.add_argument(
      "--image_dir",
      "-i",
      type=str,
      required=True,
      help="Path to the directory containing images.",
  )
  parser.add_argument(
      "--splash_image",
      type=str,
      required=False,
      help="File name of the splash image (do not include filename extension)",
  )
  parser.add_argument(
      "--disable_text_overlays",
      action="store_true",
      default=False,
      help="Disables text overlay generation.",
  )
  parser.add_argument(
      "--burn_in_subtitles",
      action="store_true",
      default=False,
      help="When provided, subtitles will be burned into the content.",
  )
  parser.add_argument(
      "--multi_voice",
      action="store_true",
      default=False,
      help=argparse.SUPPRESS,
  )
  parser.add_argument(
      "--multi_text",
      action="store_true",
      default=False,
      help="When provided, the video will summarize multiple articles.",
  )
  parser.add_argument(
      "--language",
      "-l",
      default="en-US",
      choices=pipeline.SUPPORTED_LANGUAGES,
      help="The language for the output video. Defaults to 'en-US'.",
  )
  parser.add_argument(
      "--step",
      choices=["script", "audio", "storyboard", "video"],
      default="video",
      help="Run a discrete step in the video generation flow.",
  )
  parser.add_argument(
      "--debug",
      "-d",
      action="store_true",
      default=False,
      help="Enable debug logging.",
  )
  return parser.parse_args(args)


def _get_config(config_file_name: str) -> dict[str, str]:
  with open(config_file_name, "r", encoding="utf-8") as config_file:
    return yaml.safe_load(config_file)


def _get_image_paths(image_dir: str) -> list[str]:
  # Fix: Add .webp support for modern image formats
  image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
  if not image_dir.endswith(os.path.sep):
    image_dir += os.path.sep
  image_files = []
  for filename in os.listdir(image_dir):
    _, ext = os.path.splitext(filename)
    if ext.lower() in image_extensions:
      image_files.append(os.path.join(image_dir, filename))
  return image_files


def main(args=sys.argv[1:]):
  """Main entry point for the video generation script.

  Args:
    args: A list of command-line arguments. Defaults to sys.argv[1:].
  """
  parsed_args = _parse_args(args)
  if parsed_args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

  context = pipeline.VideoGenerationContext.from_request(
      _get_config(parsed_args.config),
      request_params={
          "article_content": parsed_args.article_path.read(),
          "image_paths": _get_image_paths(parsed_args.image_dir),
          "splash_image": parsed_args.splash_image,
          "multivoice": parsed_args.multi_voice,
          "disable_text_overlays": parsed_args.disable_text_overlays,
          "burn_in_subtitles": parsed_args.burn_in_subtitles,
          "language": parsed_args.language,
          "multitext": parsed_args.multi_text,
      },
      video_id=parsed_args.video_id or str(uuid.uuid4()),
  )
  parsed_args.article_path.close()

  vertexai.init(project=context.gcp_project, location=context.gcp_location)

  video_generator = VideoGenerator()
  match parsed_args.step:
    case "script":
      video_generator.generate_script_step(context)
    case "audio":
      video_generator.generate_audio_step(context)
    case "storyboard":
      video_generator.generate_storyboard_step(context)
    case "video":
      video_generator.generate_video_step(context)


if __name__ == "__main__":
  main()
