"""Audio generation pipeline step for converting text to voice via GCP."""

from typing import Tuple
from google.cloud import texttospeech_v1beta1 as texttospeech
import pipeline
from text import script_generation
from util import gcs_utils


class TextToSpeechStep(pipeline.VideoGenerationStep):
  """Pipeline step for converting text to speech with single or multi-voice synthesis."""

  _OUTPUT_AUDIO_FILE = "2_readaloud.wav"

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location
    self.language = context.language
    self.multivoice = context.multivoice
    self.gcs_bucket_name = context.gcs_bucket_name
    self.video_id = context.video_id

  def _surround_with_voice_tags(
      self, statement: script_generation.VoiceoverStatement
  ) -> str:
    return f'<voice name="{statement.voice}">{statement.text}</voice>'

  def _create_ssml(
      self, voiceover_statements: list[script_generation.VoiceoverStatement]
  ) -> str:
    statements_ssml = "".join(
        [self._surround_with_voice_tags(s) for s in voiceover_statements]
    )
    return "<speak>" + statements_ssml + "</speak>"

  def process(
      self, initial_value: script_generation.VoiceoverScript
  ) -> Tuple[str, str]:
    """Generate audio for the provided summary text, single or multi-voice.

    Args:
        initial_value: The script for which to generate TTS.

    Returns:
        A tuple where the first item is the path to the saved audio file and the
        second item is the transcript or summary text.
    """
    script = initial_value
    output_path = f"{self.workdir}/{self._OUTPUT_AUDIO_FILE}"
    self.logger.info(
        "Synthesizing audio in %s to %s...", self.language, output_path
    )
    script_ssml = self._create_ssml(script.statements)
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(ssml=script_ssml)
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=texttospeech.VoiceSelectionParams(
            language_code=script.language, name=script.default_voice
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        ),
    )
    with open(output_path, "wb") as file:
      file.write(response.audio_content)
    audio_gcs_uri = gcs_utils.upload_to_gcs(
        output_path,
        self.gcs_bucket_name,
        f"{self.video_id}/{self._OUTPUT_AUDIO_FILE}",
    )
    return audio_gcs_uri, script.text
