"""Contains class that will act as config for the video generation process."""

import dataclasses
import os
import typing
from typing import Literal, TypedDict


SupportedLanguage = Literal[
    'en-US', 'en-GB', 'fr-FR', 'de-DE', 'es-ES', 'pt-BR'
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
