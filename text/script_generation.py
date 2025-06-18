"""Generates voiceover scripts based on a source text."""

import dataclasses
import json
import textwrap
from typing import Literal
import msgspec
import pipeline
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


class ScriptLoadError(Exception):
  """Custom exception for errors during voiceover script loading."""

  pass


def load_script(script_path: str) -> VoiceoverScript:
  """Loads a voiceover script from a JSON file."""
  try:
    with open(script_path, "r", encoding="utf-8") as file:
      script_content = file.read()
      return msgspec.json.decode(script_content, type=VoiceoverScript)
  except FileNotFoundError:
    raise ScriptLoadError(
        f"Voiceover script file not found: {script_path}"
    ) from None
  except IOError as e:
    raise ScriptLoadError(
        f"Error reading voiceover script file {script_path}: {e}"
    ) from e
  except UnicodeDecodeError as e:
    raise ScriptLoadError(
        f"Error decoding voiceover script file {script_path} as UTF-8. Ensure"
        " it's UTF-8 encoded."
    ) from e
  except msgspec.DecodeError as e:
    raise ScriptLoadError(
        f"Invalid voiceover script file format or content in {script_path}: {e}"
    ) from e
  except Exception as e:  # Catch any other unexpected errors
    raise ScriptLoadError(
        "An unexpected error occurred while loading voiceover script"
        f" {script_path}: {e}"
    ) from e


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
      multitext: bool = False,
      language: pipeline.SupportedLanguage = "en-US",
      llm: genai.GenerativeModel | None = None,
  ):
    self.speakers = speakers
    self.language = language
    self.multitext = multitext
    self._llm = llm or genai.GenerativeModel("gemini-2.5-pro")

  def _create_response_schema(self) -> dict[str, any]:
    return {
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "default_voice": {
                "type": "string",
                "enum": self._voices,
            },
            "speakers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "persona": {"type": "string"},
                        "voice": {
                            "type": "string",
                            "enum": self._voices,
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

  @property
  def language(self) -> pipeline.SupportedLanguage:
    return self._language

  @language.setter
  def language(self, language: pipeline.SupportedLanguage) -> None:
    if language not in VOICES:
      raise ValueError(f"Language {language} not supported.")
    self._voices = VOICES[language]
    self._language = language

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

    multitext_edit1 = "this article"
    multitext_extra_instructions = ""

    if self.multitext:
      multitext_edit1 = "these articles"
      multitext_extra_instructions = textwrap.dedent("""\
            - When combining and narrating all the articles follow these rules:
            1- IMPORTANT: Do not omit any of the articles. Summarize them all
                and narrate them all.
            2- Clearly state when you're transitioning from one article to the
                next.
            3- Reorder and narrate the articles in the most cohesive way,
                ensuring similar topics are discussed one after the other.
            4- Start the narration explaining you are summarizing several
                articles.
            5- Wrap up the narration with a salutation.
        """)

    prompt = textwrap.dedent(f"""\
      Take {multitext_edit1} and give me a script of news anchors narrating the
      main points in {multitext_edit1} in the form of a news flash.
      The speaker(s) should briefly introduce the topic(s) in less than 15
      seconds before diving in; however, they shouldn't introduce themselves,
      or say things like welcome back, or now to story, or we are taking
      you to... as the output of this will be consumed independently in a
      news page. Also don't make mention to a time of day (like 'good evening'
      or 'good morning' If there are multiple speakers,
      one person should be the main anchor who gives the
      main points, while the other anchor makes complementary points.
      It should not be a dialog, rather, the speaker(s) should both should
      aim to convey the same news content. If there are multiple speakers
      they should take turns when talking and the switch over should be
      very natural while sounding professional. Add some enthusiasm
      but maintain professionalism.

      Output:
      - Identify the speaker(s). For each speaker, describe their persona, and
      choose a voice. Valid voices are: {", ".join(self._voices)}.
      - Write the script. For each statement, identify the speaker by their
      voice and write the statement in a way befitting of their assigned
      persona.
      - Include the complete, combined, transcipt of the narration. Each
      speaker's turn should start a new paragraph.
      - Generate the script in the language: {self.language}.

      Additional instructions:
      - Don't add quotes or slashes within the output.
      {multitext_extra_instructions}

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

    # Gemini sometimes returns voices that are not in the list of available
    # voices. When this happens, fall back to a valid default option.
    if script.default_voice not in self._voices:
      script.default_voice = self._voices[0]

    for statement in script.statements:
      if statement.voice not in self._voices:
        statement.voice = script.default_voice

    if output_file:
      with open(output_file, "w", encoding="utf-8") as file:
        json.dump(dataclasses.asdict(script), file, indent=2)
    return script
