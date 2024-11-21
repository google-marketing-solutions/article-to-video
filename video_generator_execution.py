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
Typical usage example:
"""

import argparse
import logging
import os
import sys
import uuid
from audio import subtitles_generation_step
from audio import text_to_speech_step
import msgspec
import pipeline
import storyboarding
from text import summarize_text_step
from util import create_workdir_step
import vertexai
import video
import yaml

AUDIO_FILE_NAME = "2_readaloud.mp3"

SRT_FILE_NAME = "3_subtitles.srt"

STORYBOARD_FILE_NAME = "4_storyboard.json"

OUTPUT_VIDEO_FILE_NAME = "5_withaudiovideo.mp4"


def generate_audio_step(context: pipeline.VideoGenerationContext):
  """Generates audio and subtitles based on the article content.

  This function orchestrates the pipeline steps for generating audio from
  the article summary and creating corresponding subtitles.

  Args:
    context: A VideoGenerationContext object.
  """
  pipeline.Pipeline(
      steps=[
          create_workdir_step.CreateWorkdirStep(context),
          summarize_text_step.SummarizeTextStep(context),
          text_to_speech_step.TextToSpeechStep(context),
          subtitles_generation_step.SubtitlesGenerationStep(context),
      ]
  ).process(context.article_content)


def generate_storyboard_step(context: pipeline.VideoGenerationContext):
  """Generates a storyboard based on the article, images, audio, and subtitles.

  Args:
    context: A VideoGenerationContext object.
  """
  storyboard = storyboarding.create_storyboard_step(
      article_content=context.article_content,
      image_paths=context.image_paths,
      main_audio_path=f"{context.workdir}/{AUDIO_FILE_NAME}",
      srt_path=f"{context.workdir}/{SRT_FILE_NAME}",
  )
  with open(
      f"{context.workdir}/{STORYBOARD_FILE_NAME}", "w", encoding="utf-8"
  ) as f:
    f.write(msgspec.json.encode(storyboard).decode("utf-8"))


def generate_video_step(context: pipeline.VideoGenerationContext):
  """Generates a video based on the storyboard.

  Args:
    context: A VideoGenerationContext object.
  """
  storyboard_file_path = f"{context.workdir}/{STORYBOARD_FILE_NAME}"
  try:
    with open(storyboard_file_path, "r", encoding="utf-8") as storyboard_file:
      storyboard = msgspec.json.decode(
          storyboard_file.read(), type=storyboarding.Storyboard
      )
      video.GenerateVideoFromImagesStep(
          output_path=f"{context.workdir}/{OUTPUT_VIDEO_FILE_NAME}"
      ).process(storyboard)
  except (FileNotFoundError, msgspec.ValidationError, IOError):
    print("Failed to load storyboard file:", storyboard_file_path)


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
      "--single_voice",
      action="store_true",
      default=False,
      help=(
          "Use a single voice for all narration. Defaults to False"
          " (multivoice)."
      ),
  )
  parser.add_argument(
      "--step",
      choices=["audio", "storyboard", "video"],
      default=None,
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
  image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
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

  context = pipeline.VideoGenerationContext(
      _get_config(parsed_args.config),
      request_params={
          "article_content": parsed_args.article_path.read(),
          "image_paths": _get_image_paths(parsed_args.image_dir),
          "multivoice": not parsed_args.single_voice,
      },
      video_id=parsed_args.video_id or str(uuid.uuid4()),
  )
  parsed_args.article_path.close()
  steps = (
      [parsed_args.step]
      if parsed_args.step
      else ["audio", "storyboard", "video"]
  )

  vertexai.init(project=context.gcp_project, location=context.gcp_location)
  if "audio" in steps:
    generate_audio_step(context)
  if "storyboard" in steps:
    generate_storyboard_step(context)
  if "video" in steps:
    generate_video_step(context)


if __name__ == "__main__":
  main()
