"""Contains class that will act as config for the video generation process."""

import dataclasses
import os
import typing
from typing import Literal, TypedDict


# Full list from: https://cloud.google.com/text-to-speech/docs/gemini-tts
SupportedLanguage = Literal[
    # GA (Generally Available) Languages - 24 total
    'ar-EG',  # Arabic (Egypt)
    'bn-BD',  # Bangla (Bangladesh)
    'nl-NL',  # Dutch (Netherlands)
    'en-IN',  # English (India)
    'en-US',  # English (United States)
    'fr-FR',  # French (France)
    'de-DE',  # German (Germany)
    'hi-IN',  # Hindi (India)
    'id-ID',  # Indonesian (Indonesia)
    'it-IT',  # Italian (Italy)
    'ja-JP',  # Japanese (Japan)
    'ko-KR',  # Korean (South Korea)
    'mr-IN',  # Marathi (India)
    'pl-PL',  # Polish (Poland)
    'pt-BR',  # Portuguese (Brazil)
    'ro-RO',  # Romanian (Romania)
    'ru-RU',  # Russian (Russia)
    'es-ES',  # Spanish (Spain)
    'ta-IN',  # Tamil (India)
    'te-IN',  # Telugu (India)
    'th-TH',  # Thai (Thailand)
    'tr-TR',  # Turkish (Turkey)
    'uk-UA',  # Ukrainian (Ukraine)
    'vi-VN',  # Vietnamese (Vietnam)
    # Preview Languages - 59 total
    'af-ZA',  # Afrikaans (South Africa)
    'sq-AL',  # Albanian (Albania)
    'am-ET',  # Amharic (Ethiopia)
    'ar-001',  # Arabic (World)
    'hy-AM',  # Armenian (Armenia)
    'az-AZ',  # Azerbaijani (Azerbaijan)
    'eu-ES',  # Basque (Spain)
    'be-BY',  # Belarusian (Belarus)
    'bg-BG',  # Bulgarian (Bulgaria)
    'my-MM',  # Burmese (Myanmar)
    'ca-ES',  # Catalan (Spain)
    'ceb-PH',  # Cebuano (Philippines)
    'cmn-CN',  # Chinese, Mandarin (China)
    'cmn-TW',  # Chinese, Mandarin (Taiwan)
    'hr-HR',  # Croatian (Croatia)
    'cs-CZ',  # Czech (Czech Republic)
    'da-DK',  # Danish (Denmark)
    'en-AU',  # English (Australia)
    'en-GB',  # English (United Kingdom)
    'et-EE',  # Estonian (Estonia)
    'fil-PH',  # Filipino (Philippines)
    'fi-FI',  # Finnish (Finland)
    'fr-CA',  # French (Canada)
    'gl-ES',  # Galician (Spain)
    'ka-GE',  # Georgian (Georgia)
    'el-GR',  # Greek (Greece)
    'gu-IN',  # Gujarati (India)
    'ht-HT',  # Haitian Creole (Haiti)
    'he-IL',  # Hebrew (Israel)
    'hu-HU',  # Hungarian (Hungary)
    'is-IS',  # Icelandic (Iceland)
    'jv-JV',  # Javanese (Java)
    'kn-IN',  # Kannada (India)
    'kok-IN',  # Konkani (India)
    'lo-LA',  # Lao (Laos)
    'la-VA',  # Latin (Vatican City)
    'lv-LV',  # Latvian (Latvia)
    'lt-LT',  # Lithuanian (Lithuania)
    'lb-LU',  # Luxembourgish (Luxembourg)
    'mk-MK',  # Macedonian (North Macedonia)
    'mai-IN',  # Maithili (India)
    'mg-MG',  # Malagasy (Madagascar)
    'ms-MY',  # Malay (Malaysia)
    'ml-IN',  # Malayalam (India)
    'mn-MN',  # Mongolian (Mongolia)
    'ne-NP',  # Nepali (Nepal)
    'nb-NO',  # Norwegian, Bokmål (Norway)
    'nn-NO',  # Norwegian, Nynorsk (Norway)
    'or-IN',  # Odia (India)
    'ps-AF',  # Pashto (Afghanistan)
    'fa-IR',  # Persian (Iran)
    'pt-PT',  # Portuguese (Portugal)
    'pa-IN',  # Punjabi (India)
    'sr-RS',  # Serbian (Serbia)
    'sd-IN',  # Sindhi (India)
    'si-LK',  # Sinhala (Sri Lanka)
    'sk-SK',  # Slovak (Slovakia)
    'sl-SI',  # Slovenian (Slovenia)
    'es-419',  # Spanish (Latin America)
    'es-MX',  # Spanish (Mexico)
    'sw-KE',  # Swahili (Kenya)
    'sv-SE',  # Swedish (Sweden)
    'ur-PK',  # Urdu (Pakistan)
]

SUPPORTED_LANGUAGES = typing.get_args(SupportedLanguage)


@dataclasses.dataclass
class VideoGenerationContext:
  """Holds general settings and configuration for a video generation process.

  This dataclass centralizes all parameters required throughout the video
  generation pipeline. It includes GCP configuration, GCS bucket paths,
  input/output paths, and various flags controlling the video's features.

  Attributes:
    gcp_project: Google Cloud Project ID.
    gcp_location: Google Cloud region/location for services.
    gcs_bucket_name: Name of the GCS bucket for storing assets.
    gcs_bucket_text_path: GCS path for storing text/script related files.
    gcs_bucket_image_path: GCS path for storing image assets.
    video_id: Unique identifier for the video, used for naming output files and
      directories.
    workdir: Local file system path to the working directory for this video
      generation instance. Automatically derived from `output_path` and
      `video_id`.
    article_content: Path or reference to the input article content.
    image_paths: Path or reference to the image assets to be used.
    splash_image: Optional path to an image for the video's splash screen.
    language: Language code for text-to-sspeech and content (e.g., 'en-US').
    burn_in_subtitles: If True, subtitles will be burned into the video.
    disable_text_overlays: If True, text overlays on images will be disabled.
    multitext: Signifies that input text consists of multiple artiles or pieces
      of content.
    multivoice: If True, the narration will be a conversation between two
      speakers.
  """

  # gcp config
  gcp_project: str
  gcp_location: str
  gcs_bucket_name: str
  gcs_bucket_text_path: str
  gcs_bucket_image_path: str
  # output config
  output_path: dataclasses.InitVar[  # pylint: disable=g-missing-from-attributes (InitVar)
      os.PathLike[str]
  ]
  video_id: str
  workdir: os.PathLike[str] = dataclasses.field(init=False)
  # input assets
  article_content: os.PathLike[str]
  image_paths: os.PathLike[str]
  splash_image: os.PathLike[str] | None = None
  # video settings
  language: SupportedLanguage = 'en-US'
  burn_in_subtitles: bool = True
  disable_text_overlays: bool = False
  multitext: bool = False
  multivoice: bool = True

  def __post_init__(self, output_path: os.PathLike[str]):
    """Initializes the working directory path after the object is created.

    The working directory (`workdir`) is constructed by joining the
    `output_path` with the `video_id`.

    Args:
      output_path: The base directory where output files will be stored. This is
        an InitVar and not stored directly as an attribute after init.
    """
    self.workdir = os.path.join(output_path, self.video_id)

  class Config(TypedDict):
    """TypedDict defining the structure for static configuration values.

    This is typically loaded from a configuration file and passed to
    `VideoGenerationContext.from_request`.
    """

    gcp_project: str
    gcp_location: str
    gcs_bucket_name: str
    gcs_bucket_text_path: str
    gcs_bucket_image_path: str
    output_path: str

  @classmethod
  def from_request(
      cls,
      config: Config,
      request_params: dict[str, any],
      video_id: str,
  ):
    """Creates a `VideoGenerationContext` instance.

    This factory method combines static configuration values (e.g., from a
    config file), dynamic request parameters for a specific video, and a
    generated video ID to instantiate the context.

    Args:
      config: A dictionary (matching `VideoGenerationContext.Config`) containing
        static configuration values.
      request_params: A dictionary containing specific settings for the current
        video to be generated (e.g., language, article_content).
      video_id: The unique identifier for the video, used for naming output
        folders and files.

    Returns:
        An instance of `VideoGenerationContext`.
    """
    gcp_project = config['gcp_project']
    gcp_location = config['gcp_location']
    gcs_bucket_name = config['gcs_bucket_name']
    gcs_bucket_text_path = config['gcs_bucket_text_path']
    gcs_bucket_image_path = config['gcs_bucket_image_path']

    output_path = config['output_path']

    return VideoGenerationContext(
        gcp_project=gcp_project,
        gcp_location=gcp_location,
        gcs_bucket_name=gcs_bucket_name,
        gcs_bucket_text_path=gcs_bucket_text_path,
        gcs_bucket_image_path=gcs_bucket_image_path,
        output_path=output_path,
        video_id=video_id,
        **request_params,
    )
