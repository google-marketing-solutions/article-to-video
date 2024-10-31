"""Text generation pipeline step for fetching article text from gcp."""

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from google.cloud.exceptions import NotFound
import pipeline


class ArticleFetchGcpStep(
    pipeline.video_generation_pipeline.VideoGenerationPipeline
):
  """A pipeline step for fetching and processing the first available article text file.

  from a specified Google Cloud Storage (GCS) bucket folder.

  Attributes:
      _OUTPUT_FILE (str): The name of the output file where the article text
        will be saved.
  """

  _OUTPUT_FILE = "0_article.txt"

  def __init__(
      self, context: pipeline.video_generation_context.VideoGenerationContext
  ):
    """Initializes the ArticleFetchGcpStep with the provided context, setting up.

    paths for the working directory, bucket name, and text path in GCS.

    Args:
        context (VideoGenerationContext): The context object containing
          configuration details such as work directory, GCS bucket name, and GCS
          text path.
    """
    super().__init__(context)
    self.workdir = context.workdir
    self.gcs_bucket_name = context.gcs_bucket_name
    self.gcs_bucket_text_path = context.gcs_bucket_text_path

  def __call__(self, previous_step_result=None) -> str:
    """Executes the step to fetch the first .txt file from the GCS bucket.

    Args:
        previous_step_result (Optional): The result of the previous pipeline
          step, if any.

    Returns:
        tuple: A tuple containing:
            - article_text (str): The content of the fetched article.
            - article_title (str): The title of the article extracted from its
            content.
    """
    output_path = f"{self.workdir}/{self._OUTPUT_FILE}"
    self.logger.info(
        f"Fetching first .txt file from GCP bucket '{self.gcs_bucket_name}'"
        f" under '{self.gcs_bucket_text_path}' and saving to {output_path}..."
    )

    first_txt_file = self.get_first_txt_file_from_gcp(
        self.gcs_bucket_name, self.gcs_bucket_text_path
    )

    if first_txt_file:
      article_text = self.download_text_file_from_gcp(
          self.gcs_bucket_name, first_txt_file
      )
      with open(output_path, "w") as f:
        f.write(article_text)
      return article_text, self.get_article_title(article_text)
    else:
      self.logger.error("No .txt files found in the specified GCP path.")
      return "", ""

  def get_first_txt_file_from_gcp(
      self, bucket_name: str, folder_path: str
  ) -> str:
    """Finds the first .txt file in the specified Google Cloud Storage (GCS) bucket folder.

    Args:
        bucket_name (str): The name of the GCS bucket.
        folder_path (str): The path within the GCS bucket to search for .txt
          files.

    Returns:
        str: The name of the first .txt file found, or None if no such file is
        found.
    """
    try:
      storage_client = storage.Client()
      bucket = storage_client.bucket(bucket_name)
      blobs = bucket.list_blobs(prefix=folder_path)

      for blob in blobs:
        if blob.name.endswith(".txt"):
          self.logger.info(f"Found .txt file: {blob.name}")
          return blob.name

      self.logger.warning(f"No .txt files found in {bucket_name}/{folder_path}")
      return None

    except NotFound:
      self.logger.error(
          f"Bucket '{bucket_name}' or path '{folder_path}' not found."
      )
      return None
    except GoogleCloudError as e:
      self.logger.error(f"Google Cloud error while fetching .txt files: {e}")
      return None

  def download_text_file_from_gcp(
      self, bucket_name: str, file_path: str
  ) -> str:
    """Downloads the specified text file from the GCS bucket and returns its contents as a string.

    Args:
        bucket_name (str): The name of the GCS bucket.
        file_path (str): The path of the text file in the GCS bucket.

    Returns:
        str: The contents of the downloaded text file, or an empty string if an
        error occurs.
    """
    try:
      storage_client = storage.Client()
      bucket = storage_client.bucket(bucket_name)
      blob = bucket.blob(file_path)

      file_contents = blob.download_as_text()
      return file_contents

    except NotFound:
      self.logger.error(
          f"File '{file_path}' not found in bucket '{bucket_name}'."
      )
      return ""
    except GoogleCloudError as e:
      self.logger.error(f"Google Cloud error while downloading text file: {e}")
      return ""

  def get_article_title(self, article_text: str) -> str:
    """Extracts the title from the article text, typically the first line of the text.

    Args:
        article_text (str): The content of the article from which the title is
          to be extracted.

    Returns:
        str: The extracted title of the article, assumed to be the first line.
    """
    self.logger.info("Extracting title from article text...")
    title = article_text.split("\n", 1)[0]
    return title
