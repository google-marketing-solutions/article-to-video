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

import glob
from audio import subtitles_generation_step
from audio import text_to_speech_step
import pipeline
import storyboarding
from util import create_workdir_step
import vertexai
import video


class VideoGeneratorExecution:
  """Class representing one execution of the video generator pipeline."""

  def genvideo(self, context: pipeline.VideoGenerationContext) -> str:
    """Main function containing helper function execution.

    Args:
      context: Arguments given for code execution.

    Returns:
      Path to the uploaded video file.
    """
    vertexai.init(project=context.gcp_project, location=context.gcp_location)

    audio_path, _ = (
        pipeline.VideoGenerationPipeline(context)
        .add_steps(
            create_workdir_step.CreateWorkdirStep,
            text_to_speech_step.TextToSpeechStep,
            subtitles_generation_step.SubtitlesGenerationStep,
        )
        .process(context.article_content)
    )

    output_video_path = f"{context.workdir}/5_withaudiovideo.mp4"
    pipeline.Pipeline().add_steps(
        storyboarding.create_storyboard_step,
        video.GenerateVideoFromImagesStep(
            output_video_path, ken_burns=context.ken_burns
        ),
    ).process(
        image_paths=glob.glob(f"uploads/{context.video_id}/images/*"),
        main_audio_path=audio_path,
        srt_path="[SRT PATH PLACEHOLDER]",
    )

    return f"https://storage.googleapis.com/{context.gcs_bucket_name}/{context.video_id}.mp4"
