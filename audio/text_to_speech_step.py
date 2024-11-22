"""Audio generation pipeline step for converting text to voice via GCP."""

import json
from typing import Dict, Tuple
from google.cloud import texttospeech_v1beta1 as texttospeech
import pipeline
from util import gcs_utils
import vertexai
from vertexai.generative_models import GenerativeModel


class TextToSpeechStep(pipeline.VideoGenerationStep):
  """Pipeline step for converting text to speech with single or multi-voice synthesis."""

  _LANGUAGE_MAPPINGS = {
      "en-US": {
          "voice": "en-US-Journey-F",
          "gender": texttospeech.SsmlVoiceGender.FEMALE,
      },
      "pt-BR": {
          "voice": "pt-BR-Neural2-B",
          "gender": texttospeech.SsmlVoiceGender.MALE,
      },
      "es-ES": {
          "voice": "es-ES-Neural2-F",
          "gender": texttospeech.SsmlVoiceGender.MALE,
      },
  }

  # English-only multi-voice configuration
  _MULTIVOICE_LANGUAGE_MAPPINGS = texttospeech.VoiceSelectionParams(
      language_code="en-US", name="en-US-Studio-MultiSpeaker"
  )

  _OUTPUT_AUDIO_FILE = "2_readaloud.mp3"

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project
    self.gcp_location = context.gcp_location
    self.language = context.language
    self.multivoice = context.multivoice
    self.gcs_bucket_name = context.gcs_bucket_name
    self.video_id = context.video_id

  def __call__(self, summary_text: str) -> Tuple[str, str]:
    """Generate audio for the provided summary text, single or multi-voice.

    Args:
        summary_text: The text content to convert to speech.

    Returns:
        A tuple where the first item is the path to the saved audio file and the
        second item is the transcript or summary text.
    """
    if self.multivoice and self.language == "en-US":
      transcript_json = self.generate_multivoice_transcript(summary_text)
      audio_path = self.generate_multivoice_audio(transcript_json)
      summary_text = transcript_json["textoutput"]
    else:
      audio_path = self.generate_single_voice(summary_text)
    audio_gcs_uri = gcs_utils.upload_to_gcs(
        audio_path,
        self.gcs_bucket_name,
        f"{self.video_id}/{self._OUTPUT_AUDIO_FILE}",
    )
    return audio_gcs_uri, summary_text

  def generate_single_voice(self, summary_text: str) -> str:
    """Generate single-voice audio for the provided text.

    Args:
        summary_text: The text content to convert to speech.

    Returns:
        The path to the generated audio file.
    """
    output_path = f"{self.workdir}/{self._OUTPUT_AUDIO_FILE}"
    self.logger.info(
        f"Synthesizing audio in {self.language} to {output_path}..."
    )

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=summary_text)

    voice_params = self._LANGUAGE_MAPPINGS[self.language]
    voice = texttospeech.VoiceSelectionParams(
        language_code=self.language,
        name=voice_params["voice"],
        ssml_gender=voice_params["gender"],
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_path, "wb") as out:
      out.write(response.audio_content)

    return output_path

  def generate_multivoice_audio(
      self, multivoice_transcript: Dict[str, str]
  ) -> str:
    """Generate multi-voice audio using the provided transcript JSON.

    Args:
        multivoice_transcript: A dictionary containing the transcript data in a
          multi-voice format.

    Returns:
        The path to the generated multi-voice audio file.
    """
    output_path = f"{self.workdir}/{self._OUTPUT_AUDIO_FILE}"
    self.logger.info(f"Synthesizing multispeech audio to {output_path}...")

    client = texttospeech.TextToSpeechClient()
    multi_speaker_markup = texttospeech.MultiSpeakerMarkup()

    for item in multivoice_transcript["narration"]:
      turn = texttospeech.MultiSpeakerMarkup.Turn()
      turn.text = item["statement"]
      turn.speaker = "S" if item["name"] == "Anchor 1" else "R"
      multi_speaker_markup.turns.append(turn)

    synthesis_input = texttospeech.SynthesisInput(
        multi_speaker_markup=multi_speaker_markup
    )
    voice = self._MULTIVOICE_LANGUAGE_MAPPINGS
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_path, "wb") as out:
      out.write(response.audio_content)

    return output_path

  def generate_multivoice_transcript(self, content: str) -> Dict[str, str]:
    """Generate a multi-voice transcript in JSON format from the provided content.

    Args:
        content: The text content to convert into a multi-voice transcript.

    Returns:
        A dictionary representing the structured JSON for the multi-voice
        transcript.
    """
    self.logger.info("Generating multi-voice JSON transcript...")

    vertexai.init(project=self.gcp_project, location=self.gcp_location)

    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
    }

    model = GenerativeModel("gemini-1.5-pro-001")
    prompt = (
        """Take this article and give me a script of two news anchors narrating
        the main points in the article in the form of a news flash. Have them
        briefly introduce the topic before diving in; however, don't have them
        introduce themselves, and don't say things like welcome back, or now
        to story or we are taking you to... as the output of this will be
        consumed independently in a news page. Make one person the main anchor
        who gives the main points and make the other news anchor complement
        with complementary points. It should not be a dialog, rather,
        both should aim to convey the same news content, they should take
        turns when talking and the switch over should be very natural while
        sounding professional. They should sound natural and objective and
        professional. Add some enthusiasm but maintain professionalism.

        Return the script in a JSON format.

        The JSON Object should be formatted as the following:

        {
        "narration": [
            {"name": "Anchor 1", "statement": "This is the first statement."},
            {"name": "Anchor 2", "statement": "This is the second statement."},
            ...
        ],
        "textoutput": "
            This is the first statement.
            This is the second statement."
        }
        The object contains two attributes, one called 'narration' which
        is an array. Each item in the narration array should be a JSON
        Object containing the fields 'name' and 'statement' that represents
        who was speaking and what statement they were making.
        Do not add mark up such as comments indicating this is a json.
        The second is called "textoutput" and it should be a text file
        containing the transcript. Please format the text so each speaker's turn
        starts a new paragraph and don't give the names like in the narration
        attribute. Don't add quotes or slashes within the output.
        This is the article: """ + content
    )

    response = model.generate_content(
        prompt, generation_config=generation_config
    )
    response_json_data = json.loads(response.text, strict=False)

    return response_json_data
