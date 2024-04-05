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

""" Generates a narrated video with subtitles from news articles and images.

This is a standalone script which takes as input an article text in .txt
 format and pictures (each with the same prefix plus a number starting from 0).
It will generate a video out of the concatenated images and text summarization,
 along with narrated audio and srt subtitles.
Typical usage example:
  python3 ./video_generator.py "genvideo" -ti "./Nota.txt" -ii "."
  -gcp "project"
"""

import argparse
import datetime
import glob
import math
import subprocess
import vertexai
from vertexai.language_models import TextGenerationModel
from google.cloud import texttospeech
from google.cloud import speech_v1
import srt


_AUDIO_OUTPUT = "./readaloud.mp3"
_AUDIO_WAV = "./readaloud.wav"
_IMAGE_FILE_NAME = "imagen"
_SRT_FILE_OUTPUT = "./subtitles.srt"
_VIDEO_OUTPUT_WITHOUT_AUDIO = "./mutedvideo.mp4"
_VIDEO_OUTPUT_WITH_AUDIO = "./withaudiovideo.mp4"
_VIDEO_OUTPUT_FINAL = "./finalvideo.mp4"
_VIDEO_OUTPUT_FINAL_WITH_SRT = "./finalvideosubs.mp4"

_CLOUD_PROJECT_LOCATION = "us-central1"

# https://cloud.google.com/text-to-speech/docs/voices
_LANGUAGE = "es-US"
_VOICE = "es-US-Polyglot-1"
_SSML_GENDER = texttospeech.SsmlVoiceGender.MALE


def _summarize_article(text_input_path: str, gcp: str) -> str:
  """Article summarization (spanish articles, change prompt if needed).

  Args:
    text_input_path: A string. Path of the text file containing the article
     to be summarized.
    gcp: A string. The Google cloud project.

  Returns:
    A string with the article summary
  """
  with open(text_input_path, "r") as file:
    content = file.read()
    vertexai.init(project=gcp, location=_CLOUD_PROJECT_LOCATION)
    parameters = {
        "temperature": 0.2,
        "max_output_tokens": 900,
        "top_p": 0.8,
        "top_k": 40,
    }
    model = TextGenerationModel.from_pretrained("text-bison@001")
    response = model.predict(
        "Crear un resumen del contenido del siguiente articulo "
        "y tener en cuenta las siguientes restricciones:"
        "1. El resumen debe de contener entre 400 y 600 palabras"
        "2. El resumen NO debe mencionar al autor del articulo"
        "3. El resumen debe comenzar con una frase que capte la atencion "
        "del lector y que este relacionado con el contenido del articulo"
        "4. El resumen debe terminar con una frase de conclusion "
        "5. En caso de que el articulo contenga numeros o estadisticas deben "
        "ser mencionadas en el resumen"
        "6. El resumen debe contenter mas de 2 frases"
        "7. El resumen debe contener un maximo de 6 frases"
        "El siguiente es el articulo a resumir con las restricciones "
        "mencionadas: "
        + content,
        **parameters
    )
    summary_text = response.text
    summary_text = summary_text.replace("*", "")
    return summary_text


def _write_audio_file_from_text(summary_text: str) -> str:
  """Audio generation.

  Args:
    summary_text: A string of the text content.

  Returns:
    A string with the saved output file name.
  """
  client = texttospeech.TextToSpeechClient()
  synthesis_input = texttospeech.SynthesisInput(text=summary_text)
  voice = texttospeech.VoiceSelectionParams(
      language_code=_LANGUAGE, name=_VOICE, ssml_gender=_SSML_GENDER
  )
  audio_config = texttospeech.AudioConfig(
      audio_encoding=texttospeech.AudioEncoding.MP3
  )
  response = client.synthesize_speech(
      input=synthesis_input, voice=voice, audio_config=audio_config
  )

  with open(_AUDIO_OUTPUT, "wb") as out:
    out.write(response.audio_content)
    return out


def _generate_video_file_from_image_files(image_input_path: str) -> str:
  """Video generation.

  Args:
    image_input_path: A string of the image files path.

  Returns:
    A string with the saved output file name.
  """
  video_transition_effect = (
      "circleopen"  # fade, slideright , circleopen ,  fadeblack
  )
  number_of_images = len(
      glob.glob(image_input_path + "/" + _IMAGE_FILE_NAME + "*")
  )
  audio_file_length = _obtain_midia_length(_AUDIO_OUTPUT)
  _create_video_without_audio(
      number_of_images,
      audio_file_length,
      video_transition_effect,
      image_input_path,
  )
  _add_audio_to_video(_VIDEO_OUTPUT_WITHOUT_AUDIO, _AUDIO_OUTPUT)
  _write_subs()
  _add_subs_to_video()
  return _VIDEO_OUTPUT_FINAL_WITH_SRT


def _obtain_midia_length(media_file: str) -> float:
  """Calculates a media file length.

  Args:
    media_file: A string of the media files path.

  Returns:
    A float with the length in seconds.
  """
  ffmpeg_command = [
      "ffprobe",
      "-i",
      media_file,
      "-show_entries",
      "format=duration",
      "-v",
      "quiet",
      "-of",
      'csv="p=0"',
  ]

  length_in_seconds = (
      _execute_ffmpeg_command(ffmpeg_command)
      .replace("b", "")
      .replace("n", "")
      .replace("\\", "")
      .replace("'", "")
  )
  return float(length_in_seconds)


def _execute_ffmpeg_command(command: str) -> str:
  """Executes a ffmpeg command as a subprocess.

  Args:
    command: a string containing the ffmpeg command to be executed.

  Returns:
    A string with the stdout by the ffmpeg client.
  """
  ffmpeg_command_txt = " ".join(command)
  pipe = subprocess.run(
      ffmpeg_command_txt,
      shell=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      bufsize=10**9,
  )

  return str(pipe.stdout)


def _create_video_without_audio(
    number_of_images: int,
    audio_file_length: float,
    video_transition_effect: str,
    image_path: str,
) -> str:
  """Creates a video concatenating different images taken as input.

  Args:
    number_of_images: an int with the number of images to be added.
    audio_file_length: a float containing the length of the audio file.
    video_transition_effect: a string containing the transition effect between
    images. Possible choices: fade, slideright circleopen fadeblack
    image_path: a string containing the image files path.

  Returns:
    A string with the output file path.
  """
  ffmpeg_command = ["ffmpeg"]
  each_image_duration = math.ceil(audio_file_length / number_of_images)

  for i in range(number_of_images):
    image = image_path + "/" + _IMAGE_FILE_NAME + str(i) + ".jpg"
    ffmpeg_command.extend(
        ["-loop", "1", "-t", str(each_image_duration), "-i", image]
    )

  ffmpeg_command.extend(['-filter_complex "'])

  for i in range(number_of_images):
    ffmpeg_command.append(
        "["
        + str(i)
        + "]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:"
        + "-1:-1,setsar=1,fps=30,format=yuv420p["
        + str(i)
        + "p];"
    )

  offset = each_image_duration - 1
  for i in range(number_of_images):
    if i == 0:
      ffmpeg_command.append(
          "["
          + str(i)
          + "p]["
          + str(i + 1)
          + "p]xfade=transition="
          + video_transition_effect
          + ":duration=1:offset="
          + str(offset)
          + "["
          + str(i + 1)
          + "x]"
      )
    if i == (number_of_images - 1):
      continue
    if i != 0:
      ffmpeg_command.append(
          ";["
          + str(i)
          + "x]["
          + str(i + 1)
          + "p]xfade=transition="
          + video_transition_effect
          + ":duration=1:offset="
          + str(offset)
          + "["
          + str(i + 1)
          + "x]"
      )
    offset = each_image_duration + offset - 1

  ffmpeg_command.extend(
      [
          '"',
          "-map",
          "[" + str(i) + "x]",
          "-c:v",
          "libx264",
          "-crf",
          "17",
          "-y",
          _VIDEO_OUTPUT_WITHOUT_AUDIO,
      ]
  )
  _execute_ffmpeg_command(ffmpeg_command)
  return _VIDEO_OUTPUT_WITHOUT_AUDIO


def _add_audio_to_video(muted_audio: str, audio_file: str) -> str:
  """Adds the narrated audio to the video file and saves a new file

  Args:
    muted_audio: path of the video file without audio.
    audio_file: path of the audio file to be added to the muted video.

  Returns:
    A string with the output file path.
  """
  ffmpeg_command = [
      "ffmpeg",
      "-i",
      muted_audio,
      "-i",
      audio_file,
      "-c",
      "copy",
      "-y",
      _VIDEO_OUTPUT_FINAL,
  ]
  _execute_ffmpeg_command(ffmpeg_command)
  return _VIDEO_OUTPUT_FINAL


def _write_subs() -> str:
  """Writes subs file. MP3 must be converted to .wav for proper encoding.

  Returns:
    A string with the output file path.
  """
  ffmpeg_command = ["ffmpeg", "-y", "-i", _AUDIO_OUTPUT, _AUDIO_WAV]
  _execute_ffmpeg_command(ffmpeg_command)
  text_with_timings = _fetch_text_from_audio_with_timings(_AUDIO_WAV)
  _generate_subs(text_with_timings)
  return _SRT_FILE_OUTPUT


def _fetch_text_from_audio_with_timings(audio_path: str) -> object:
  """Fetches the individual word timings to be used for subtitle creation

  Args:
    audio_path: path of the audio file.

  Returns:
    An object of the speech to text api containing the words and their timings.
  """
  with open(audio_path, "rb") as audio_file:
    content = audio_file.read()

  client = speech_v1.SpeechClient()
  config = speech_v1.RecognitionConfig(
      enable_word_time_offsets=True,
      enable_automatic_punctuation=True,
      sample_rate_hertz=24000,
      language_code="es-US",
  )
  audio = speech_v1.RecognitionAudio(content=content)
  operation = client.long_running_recognize(config=config, audio=audio)
  response = operation.result()
  return response


def _generate_subs(text_with_timings: object, bin_size: int = 3) -> str:
  """Generates synced subs using timed bins.

  Args:
    text_with_timings: String path of the audio file.
    bin_size: An int. Here, bin_size = 3 means each bin takes 3 secs.
     All the words in the interval of 3 secs from the input will be
     grouped together.

  Returns:
    A string with the output .srt subs file.
  """
  transcriptions = []
  index = 0

  for result in text_with_timings.results:
    try:
      if result.alternatives[0].words[0].start_time.seconds:
        start_sec = result.alternatives[0].words[0].start_time.seconds
        start_microsec = result.alternatives[0].words[0].start_time.microseconds
      else:
        start_sec = 0
        start_microsec = 0
      end_sec = start_sec + bin_size  # bin end sec

      last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
      last_word_end_microsec = (
          result.alternatives[0].words[-1].end_time.microseconds
      )
      transcript = result.alternatives[0].words[0].word

      index += 1  # subtitle index.

      for i in range(len(result.alternatives[0].words) - 1):
        try:
          word = result.alternatives[0].words[i + 1].word
          word_start_sec = (
              result.alternatives[0].words[i + 1].start_time.seconds
          )
          word_start_microsec = (
              result.alternatives[0].words[i + 1].start_time.microseconds
          )
          word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
          word_end_microsec = (
              result.alternatives[0].words[i + 1].end_time.microseconds
          )

          if word_end_sec < end_sec:
            transcript = transcript + " " + word
          else:
            previous_word_end_sec = (
                result.alternatives[0].words[i].end_time.seconds
            )
            previous_word_end_microsec = (
                result.alternatives[0].words[i].end_time.microseconds
            )
            transcriptions.append(
                srt.Subtitle(
                    index,
                    datetime.timedelta(0, start_sec, start_microsec),
                    datetime.timedelta(
                        0, previous_word_end_sec, previous_word_end_microsec
                    ),
                    transcript,
                )
            )

            start_sec = word_start_sec
            start_microsec = word_start_microsec
            end_sec = start_sec + bin_size
            transcript = result.alternatives[0].words[i + 1].word

            index += 1
        except IndexError:
          pass

      transcriptions.append(
          srt.Subtitle(
              index,
              datetime.timedelta(0, start_sec, start_microsec),
              datetime.timedelta(0, last_word_end_sec, last_word_end_microsec),
              transcript,
          )
      )
      index += 1
    except IndexError:
      pass

  subtitles = srt.compose(transcriptions)

  with open(_SRT_FILE_OUTPUT, "w") as f:
    f.write(subtitles)

  return _SRT_FILE_OUTPUT


def _add_subs_to_video() -> srt:
  """Adds subs to the existing video file.

  Returns:
    A string with the output video file with subs.
  """
  ffmpeg_command = [
      "ffmpeg",
      "-y",
      "-i",
      _VIDEO_OUTPUT_FINAL,
      "-i",
      _SRT_FILE_OUTPUT,
      "-c",
      "copy",
      "-c:s",
      "mov_text",
      _VIDEO_OUTPUT_FINAL_WITH_SRT,
  ]
  _execute_ffmpeg_command(ffmpeg_command)
  return _VIDEO_OUTPUT_FINAL_WITH_SRT


def main(in_args: object) -> str:
  """Main function containing helper function execution.

  Args:
    in_args: Arguments given for code execution.
  """
  summary_text = _summarize_article(in_args.text_input_path, in_args.gcp_project)
  _write_audio_file_from_text(summary_text)
  _generate_video_file_from_image_files(in_args.image_input_path)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
  )
  subparsers = parser.add_subparsers(dest="command")
  main_parser = subparsers.add_parser("genvideo", help=main.__doc__)
  main_parser.add_argument("-ti", "--text-input", dest="text_input_path")
  main_parser.add_argument("-ii", "--image-input", dest="image_input_path")
  main_parser.add_argument("-gcp", "--google-cloud-project", dest="gcp_project")
  args = parser.parse_args()
  main(args)
