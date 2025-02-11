"""Contains class that will act as config for the video generation process."""

from typing import TypedDict


class VideoGenerationContext:
  """Context object that hold general settings for a video generation process."""

  class Config(TypedDict):
    gcp_project: str
    gcp_location: str
    gcs_bucket_name: str
    gcs_bucket_text_path: str
    gcs_bucket_image_path: str
    output_path: str

  def __init__(
      self,
      config: Config,
      request_params: dict[str, str],
      video_id: str,
  ):
    """Creates a context object by combining values from the config file, video generation request and generated video UUID.

    Args:
        config: Static configuration values provided from the config file.
        request_params: Specific settings for the current video to be generated.
        video_id: Generated video id, to be used as folder and file names.
    """
    self.gcp_project = config['gcp_project']
    self.gcp_location = config['gcp_location']
    self.gcs_bucket_name = config['gcs_bucket_name']
    self.gcs_bucket_text_path = config['gcs_bucket_text_path']
    self.gcs_bucket_image_path = config['gcs_bucket_image_path']
    self.workdir = f"{config['output_path']}/{video_id}"
    self.video_id = video_id
    # TODO(cfeldman): Remove ken_burns option from UI and then delete from
    # context. This is currently a no-op.
    self.ken_burns = request_params.get('ken_burns', False)
    self.disable_text_overlays = request_params.get(
        'disable_text_overlays', False
    )
    self.burn_in_subtitles = request_params.get('burn_in_subtitles', False)
    self.language = request_params.get('language', 'en-US')
    self.sentiment = request_params.get('sentiment', False)
    self.video_overlay = request_params.get('video_overlay', False)
    self.title = request_params.get('title', False)
    self.article_content = request_params.get('article_content', False)
    self.image_paths = request_params.get('image_paths', [])
    self.multivoice = request_params.get('multivoice', False)
