"""Subtitles generation pipeline step."""

import string
from typing import List, MutableSequence, Tuple
from google.cloud import speech_v1
import pipeline
import srt
from util import gcs_utils


class SubtitlesGenerationStep(pipeline.VideoGenerationStep):
  """Pipeline step for generating SRT file based on text and audio file."""

  _OUTPUT_SRT_FILE = "3_subtitles.srt"

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location
    self.gcs_bucket_name = context.gcs_bucket_name
    self.video_id = context.video_id
    self.language = context.language

  def __call__(self, audio_and_transcript: Tuple[str, str]) -> str:
    """Generate subtitles SRT file based on audio and transcript text.

    Args:
      audio_and_transcript: Tuple that contains(audio_file_path, transcript
        text)

    Returns:
      Local file path for the and generated SRT file.
    """

    words = self._transcribe_audio(audio_and_transcript[0])
    subtitles = self._break_sentences(audio_and_transcript[1])
    with open(f"{self.workdir}/subtitles_plain.txt", "w") as f:
      f.writelines(line + "\n" for line in subtitles)
    subs = self._attach_timestamps(words, subtitles)
    output_path = f"{self.workdir}/{self._OUTPUT_SRT_FILE}"
    with open(output_path, "w") as f:
      f.writelines(srt.compose(subs))
    self.logger.info("Wrote subtitles to %s", output_path)
    gcs_uri = gcs_utils.upload_to_gcs(
        output_path,
        self.gcs_bucket_name,
        f"{self.video_id}/{self._OUTPUT_SRT_FILE}",
    )
    self.logger.info("Uploaded SRT file to GCS: %s", gcs_uri)
    return output_path

  def _transcribe_audio(
      self, audio_gcs_uri: str
  ) -> MutableSequence[speech_v1.types.WordInfo]:
    """Transcribe audio file.

    Transcribe audio file from Cloud Storage using speech recognition
    and output a list of words. Each word has start_time and end_time.

    Args:
      audio_gcs_uri: URI for audio file in GCS, e.g. gs://[BUCKET]/[FILE]

    Returns:
      A list of words with timestamps. For example:
      [
        {
          "word": "Hello",
          "start_time": "0:01:04",
          "end_time": "0:01:04.500000"
        },
        {
          "word": "world",
          "start_time": "0:01:04.500000",
          "end_time": "0:01:05.200000"
        },
        ...
      ]
    """

    self.logger.info("Transcribing %s ...", audio_gcs_uri)
    client = speech_v1.SpeechClient()

    config = {
        "enable_word_time_offsets": True,
        "enable_automatic_punctuation": False,
        "language_code": self.language,
        "audio_channel_count": 1,
        "encoding": "LINEAR16",
        "model": "latest_long",
        "use_enhanced": True,
        "diarization_config": {
            "enable_speaker_diarization": True,
            "min_speaker_count": 1,
            "max_speaker_count": 2,
        },
    }

    operation = client.long_running_recognize(
        config=config,
        audio={"uri": audio_gcs_uri},
    )
    response = operation.result()

    words = []
    for result in response.results:
      words.extend(result.alternatives[0].words)
    print("Transcribing finished")
    return words

  def _break_sentences(self, transcript: str) -> List[str]:
    """Breakdown a transcript into subtitle lines.

    Args:
      transcript: A string contains transcript of the audio file.

    Returns:
      A list of subtitle lines.
    """
    subtitles = []
    first_word = True
    char_count = 0
    content = ""

    for word in transcript.split():
      char_count += len(word)
      content += " " + word.strip()

      if (
          "." in word
          or "!" in word
          or "?" in word
          or char_count > 40
          or ("," in word and not first_word)
      ):
        # break sentence at: . ! ? or line length exceeded
        # also break if , and not first word
        subtitles.append(content)
        first_word = True
        content = ""
        char_count = 0
      else:
        first_word = False

    return subtitles

  def _attach_timestamps(
      self,
      words: MutableSequence[speech_v1.types.WordInfo],
      subtitles: List[str],
  ) -> List[str]:
    r"""Attach start_time and end_time for each subtitle line.

    Loop through each subtitle line, find the matching end word
    in the transcribed words list, and get corresponding timestamps
    to format the subtitle line into SRT format.

    Args:
      words: A list of detected words with timestamps.
      subtitles: A list of subtitle lines that needs to be timestamped.

    Returns:
      A list of subtitle lines in SRT format. For example:
      [
        "1\n00:00:00,000 --> 00:00:05,000\nHello, world!\n",
        "2\n00:00:05,000 --> 00:00:10,000\nThis is a test.\n",
      ]
    """
    words_count = len(words)
    line_idx = 1
    end_index = -1
    srt_lines = []
    for line in subtitles:
      start_index = end_index + 1
      # No more detected words are available, finish the operation.
      if start_index >= words_count:
        break
      split_line = line.split()
      end_index = end_index + len(split_line)
      end_word = self.remove_end_punctuation(split_line[-1].strip())
      found_match = False

      # If no more words left, pick the last word as the end_index
      if end_index >= words_count:
        end_index = words_count
      else:
        # step 1: look for excat word match from end_index-2 to end_index+2,
        # and calculate simlarity score
        highest_similarity_score = 0
        most_similar_word_index = end_index
        for i in [
            end_index,
            end_index - 1,
            end_index + 1,
            end_index - 2,
            end_index + 2,
        ]:
          if i >= words_count:
            continue
          w = words[i].word.strip()
          if end_word == w or end_word.endswith(w):
            end_index = i
            found_match = True
            break
          else:
            similarity_score = self.get_similarity_score(end_word, w)
            if similarity_score > highest_similarity_score:
              highest_similarity_score = similarity_score
              most_similar_word_index = i
        # step 2: if no exact word match is found, choose the word with
        # the highest similarity score
        if not found_match:
          end_index = most_similar_word_index

      start_timestamp = words[start_index].start_time
      end_timestamp = words[end_index].end_time
      srt_lines.append(
          srt.Subtitle(
              index=line_idx,
              start=start_timestamp,
              end=end_timestamp,
              content=srt.make_legal_content(line),
          )
      )
      line_idx += 1
    return srt_lines

  @staticmethod
  def remove_end_punctuation(text: str) -> str:
    """Removes punctuation from both ends of a string.

    Args:
      text: The input string.

    Returns:
      The string with punctuation removed from its ends.
    """
    # Remove punctuation from the beginning
    while text and text[0] in string.punctuation:
      text = text[1:]

    # Remove punctuation from the end
    while text and text[-1] in string.punctuation:
      text = text[:-1]

    return text

  @staticmethod
  def get_similarity_score(word1: str, word2: str) -> float:
    """Calculates the Jaccard similarity between two words.

    Jaccard similarity is calculated by dividing the number of elements that the
    sets have in common (the intersection) by the total number of elements in
    both sets (the union).

    Args:
      word1: String of word 1.
      word2: String of word 2.

    Returns:
      Jaccard similarity score.
    """
    set1 = set(word1)
    set2 = set(word2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union
