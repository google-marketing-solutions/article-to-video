"""Generates voiceover scripts based on a source text."""

import dataclasses
import json
import textwrap
from typing import Literal
import msgspec
from vertexai import generative_models as genai


@dataclasses.dataclass
class VoiceoverSpeaker:
  persona: str
  voice: str


@dataclasses.dataclass
class VoiceoverStatement:
  voice: str
  text: str


@dataclasses.dataclass
class VoiceoverScript:
  language: str
  default_voice: str
  speakers: list[VoiceoverSpeaker]
  statements: list[VoiceoverStatement]
  text: str


VOICES = {
    # English (US)
    "en-US": [
        "en-US-Studio-O",
        "en-US-Studio-Q",
    ],
    # English (UK)
    "en-GB": [
        "en-GB-Studio-B",
        "en-GB-Studio-C",
    ],
    # French
    "fr-FR": [
        "fr-FR-Studio-A",
        "fr-FR-Studio-D",
    ],
    # German
    "de-DE": [
        "de-DE-Studio-B",
        "de-DE-Studio-C",
    ],
    # Spanish (Spain)
    "es-ES": [
        "es-ES-Studio-C",
        "es-ES-Studio-F",
    ],
    # Portuguese (Brazilian)
    "pt-BR": [
        "pt-BR-Neural2-B",
        "pt-BR-Neural2-C",
    ],
}


class ScriptGenerator:
  """Generates voiceover scripts based on a source text."""

  def __init__(
      self,
      speakers: Literal[1, 2],
      language: Literal["en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "pt-BR"],
      llm: genai.GenerativeModel = genai.GenerativeModel("gemini-1.5-pro-001"),
  ):
    self.speakers = speakers
    self.language = language
    self._llm = llm

  def _create_response_schema(self) -> dict[str, any]:
    return {
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "default_voice": {
                "type": "string",
                "enum": VOICES.get(self.language, "en-US"),
            },
            "speakers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "persona": {"type": "string"},
                        "voice": {
                            "type": "string",
                            "enum": VOICES.get(self.language, "en-US"),
                        },
                    },
                },
                "minItems": self.speakers,
                "maxItems": self.speakers,
            },
            "statements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "voice": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
            },
            "text": {"type": "string"},
        },
        "required": [
            "language",
            "default_voice",
            "speakers",
            "statements",
            "text",
        ],
    }

  def generate(
      self, source_text: str, output_file: str | None = None
  ) -> VoiceoverScript:
    """Generates a voiceover script based on a source text.

    Args:
      source_text: The text to generate a script for.
      output_file: An optional file path to save the generated script.

    Returns:
      The generated script.
    """
    prompt = textwrap.dedent(f"""\
      Take this article and give me a script of news anchors narrating the main
      points in the article in the form of a news flash. The speaker(s) should
      briefly introduce the topic before diving in; however, they shouldn't
      introduce themselves, or say things like welcome back, or now to story, or
      we are taking you to... as the output of this will be consumed
      independently in a news page. If there are multiple speakers, one person
      should be the main anchor who gives the main points, while the other
      anchor makes complementary points. It should not be a dialog, rather, the
      speaker(s) should both should aim to convey the same news content. If
      there are multiple speakers they should take turns when talking and the
      switch over should be very natural while sounding professional. Add some
      enthusiasm but maintain professionalism.

      Output:
      - Identify the speaker(s). For each speaker, describe their persona, and
      choose a voice.
      - Write the script. For each statement, identify the speaker by their
      voice and write the statement in a way befitting of their assigned
      persona.
      - Include the complete, combined, transcipt of the narration. Each
      speaker's turn should start a new paragraph.
      - Generate the script in the language: {self.language}.

      Additional instructions:
      - Don't add quotes or slashes within the output.

      This is the article:
      {source_text}
    """)
    response = self._llm.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=self._create_response_schema(),
        ),
    )
    script = msgspec.json.decode(response.text, type=VoiceoverScript)
    if output_file:
      with open(output_file, "w", encoding="utf-8") as file:
        json.dump(dataclasses.asdict(script), file, indent=2)
    return script
