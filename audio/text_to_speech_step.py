"""Audio generation pipeline step for converting text to voice via GCP."""

import re
from google.api_core.exceptions import InvalidArgument
from google.cloud import texttospeech_v1beta1 as texttospeech
import pipeline


class TextToSpeechStep(
    pipeline.video_generation_pipeline.VideoGenerationPipeline
):
  """A pipeline step for generating speech audio from SSML via Text-to-Speech.

  Attributes:
      _LANGUAGE_MAPPINGS (dict): Maps language codes to voice settings.
      _AUDIO_OUTPUT_FILE (str): Filename for the generated audio output file.
  """

  _LANGUAGE_MAPPINGS = {
      "en-US": {
          "voice": "en-US-Wavenet-C",
          "gender": texttospeech.SsmlVoiceGender.FEMALE,
      },
      "pt-BR": {
          "voice": "pt-BR-Wavenet-C",
          "gender": texttospeech.SsmlVoiceGender.FEMALE,
      },
      "es-ES": {
          "voice": "es-ES-Wavenet-C",
          "gender": texttospeech.SsmlVoiceGender.FEMALE,
      },
  }
  _AUDIO_OUTPUT_FILE = "2_readaloud.mp3"

  def __init__(
      self, context: pipeline.video_generation_context.VideoGenerationContext
  ):
    """Initializes the TextToSpeechStep with context information.

    Args:
        context (AtvPipelineStepContext): The context object providing
          configurations such as work directory, project, location, and language
          preferences.
    """
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location
    self.language = context.language

  def __call__(self, ssml_output: str) -> str:
    """Generates audio from SSML text using Google Cloud Text-to-Speech and saves it to an output file.

    If SSML is not supported by the selected voice, reattempt with plain text.

    Args:
        ssml_output (str): The SSML text content to convert into audio.

    Returns:
        tuple: A tuple containing:
            - audio_output_file (str): Path to the generated MP3 audio file.
            - response.timepoints (list): List of timepoints for SSML markers if
            enabled.
    """
    audio_output_file = f"{self.workdir}/{self._AUDIO_OUTPUT_FILE}"
    self.logger.info(
        f"Synthesizing audio in {self.language} to {audio_output_file}..."
    )

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_output)
    voice = texttospeech.VoiceSelectionParams(
        language_code=self.language,
        name=self._LANGUAGE_MAPPINGS[self.language]["voice"],
        ssml_gender=self._LANGUAGE_MAPPINGS[self.language]["gender"],
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    request = texttospeech.SynthesizeSpeechRequest(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
        enable_time_pointing=[
            texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK
        ],
    )

    try:
      response = client.synthesize_speech(request)
    except InvalidArgument as e:
      if "does not support SSML" in str(e):
        self.logger.warning(
            "SSML not supported for"
            f" {self._LANGUAGE_MAPPINGS[self.language]['voice']}. Retrying with"
            " plain text."
        )
        plain_text = self._strip_ssml_tags(ssml_output)
        synthesis_input = texttospeech.SynthesisInput(text=plain_text)
        request = texttospeech.SynthesizeSpeechRequest(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        response = client.synthesize_speech(request)
      else:
        raise e

    with open(audio_output_file, "wb") as out:
      out.write(response.audio_content)

    return (
        audio_output_file,
        response.timepoints if hasattr(response, "timepoints") else [],
    )

  @staticmethod
  def _strip_ssml_tags(ssml_text: str) -> str:
    """Utility method to strip SSML tags, leaving only the plain text."""

    return re.sub(r"<[^>]+>", "", ssml_text).strip()
