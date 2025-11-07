"""Audio generation pipeline step for converting text to voice via Gemini TTS.

Added for Gemini TTS language support: Migrated from legacy Cloud TTS to Gemini
2.5 Pro TTS for:
- Multi-speaker synthesis with better voice quality
- Support for 83 languages (24 GA + 59 Preview)
- Natural language prompt-based style control
- More natural-sounding multi-speaker conversations
"""

from typing import Tuple
# Added for Gemini TTS language support: Updated to use standard
# texttospeech (v1) for Gemini TTS support
from google.cloud import texttospeech
import pipeline
from text import script_generation
from util import gcs_utils


class TextToSpeechStep(pipeline.VideoGenerationStep):
  """Pipeline step for Gemini TTS multi-speaker synthesis.

  Added for Gemini TTS language support: Refactored to use Gemini 2.5 Pro TTS
  with MultiSpeakerMarkup
  instead of SSML-based synthesis. This provides better multi-speaker quality
  and supports all 83 Gemini TTS languages.
  """

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

  def _create_multi_speaker_turns(
      self, voiceover_statements: list[script_generation.VoiceoverStatement]
  ) -> list[texttospeech.MultiSpeakerMarkup.Turn]:
    """Convert voiceover statements to Gemini TTS multi-speaker turns.

    Added for Gemini TTS language support: Replaces SSML approach. Uses
    structured turn-based format
    for more natural multi-speaker conversations.

    Args:
      voiceover_statements: List of statements with voice and text

    Returns:
      List of Turn objects for MultiSpeakerMarkup
    """
    turns = []
    for statement in voiceover_statements:
      turn = texttospeech.MultiSpeakerMarkup.Turn(
          text=statement.text,
          speaker=statement.voice,
      )
      turns.append(turn)
    return turns

  def _create_speaker_configs(
      self, script: script_generation.VoiceoverScript
  ) -> list[texttospeech.MultispeakerPrebuiltVoice]:
    """Create speaker-to-voice mappings for Gemini TTS.

    Added for Gemini TTS language support: Maps each unique speaker/voice in the
    script to a Gemini voice.
    Ensures at least 2 speakers (API requirement) by adding a secondary voice if
    needed.

    Args:
      script: The voiceover script containing speakers

    Returns:
      List of MultispeakerPrebuiltVoice configurations
    """
    speaker_configs = []
    for speaker in script.speakers:
      config = texttospeech.MultispeakerPrebuiltVoice(
          speaker_alias=speaker.voice,
          speaker_id=speaker.voice,  # Gemini voices use same ID as name
      )
      speaker_configs.append(config)

    # Added for Gemini TTS language support: Gemini API requires at least 2
    # distinct speakers
    if len(speaker_configs) == 1:
      # Get the primary voice
      primary_voice = script.speakers[0].voice
      # Select a different voice from GEMINI_VOICES
      available_voices = [
          v for v in script_generation.GEMINI_VOICES if v != primary_voice
      ]
      secondary_voice = available_voices[0] if available_voices else "Aoede"

      # Add secondary speaker config (unused but required for API)
      secondary_config = texttospeech.MultispeakerPrebuiltVoice(
          speaker_alias=secondary_voice,
          speaker_id=secondary_voice,
      )
      speaker_configs.append(secondary_config)
      self.logger.info(
          "Added secondary voice '%s' to meet Gemini TTS API requirement"
          " (minimum 2 speakers)",
          secondary_voice,
      )

    return speaker_configs

  def process(
      self, initial_value: script_generation.VoiceoverScript
  ) -> Tuple[str, str, str]:
    """Generate audio using Gemini 2.5 Pro TTS.

    Added for Gemini TTS language support: Completely refactored to use Gemini
    TTS API instead of legacy
    Cloud TTS. Uses MultiSpeakerMarkup for structured multi-speaker synthesis
    and adds prompt-based style control.

    Args:
        initial_value: The script for which to generate TTS.

    Returns:
        A tuple containing:
          - The local path to the generated audio file.
          - The GCS URI of the uploaded audio file.
          - The original script text.
    """
    script = initial_value
    output_path = f"{self.workdir}/{self._OUTPUT_AUDIO_FILE}"
    self.logger.info(
        "Synthesizing audio with Gemini TTS in %s to %s...",
        self.language,
        output_path,
    )

    client = texttospeech.TextToSpeechClient()

    # Added for Gemini TTS language support: Create multi-speaker markup
    # for turn-based synthesis
    turns = self._create_multi_speaker_turns(script.statements)

    # Added for Gemini TTS language support: Style prompt for news anchor
    # delivery
    style_prompt = (
        "Act as professional news anchors delivering a news report. "
        "Speak clearly and confidently with appropriate pacing and emphasis. "
        "Maintain an enthusiastic but professional tone."
    )

    # Added for Gemini TTS language support: Construct synthesis input with
    # multi-speaker markup
    synthesis_input = texttospeech.SynthesisInput(
        multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=turns),
        prompt=style_prompt,
    )

    # Added for Gemini TTS language support: Configure multi-speaker voice
    # settings
    speaker_configs = self._create_speaker_configs(script)
    multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
        speaker_voice_configs=speaker_configs
    )

    # Added for Gemini TTS language support: Use Gemini 2.5 Pro TTS model
    # with multi-speaker config
    voice = texttospeech.VoiceSelectionParams(
        language_code=script.language,
        model_name="gemini-2.5-pro-tts",
        multi_speaker_voice_config=multi_speaker_voice_config,
    )

    # Added for Gemini TTS language support: Configure audio output -
    # LINEAR16 at 24kHz for high quality
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
    )

    # Added for Gemini TTS language support: Synthesize speech with Gemini
    # TTS
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_path, "wb") as file:
      file.write(response.audio_content)

    audio_gcs_uri = gcs_utils.upload_to_gcs(
        output_path,
        self.gcs_bucket_name,
        f"{self.video_id}/{self._OUTPUT_AUDIO_FILE}",
    )
    return output_path, audio_gcs_uri, script.text
