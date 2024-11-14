"""Utility functions for common operations with Google Cloud Storage."""

import logging
import os
import pathlib
import google.api_core.exceptions as google_exceptions
from google.cloud import storage


def upload_to_gcs(
    source_file_path: str, bucket_name: str, destination_blob: str
) -> str:
  """Uploads a local file to the Google Cloud Storage bucket.

  Args:
    source_file_path: The local file path of the file.
    bucket_name (str): The name of the GCS bucket to upload to.
    destination_blob (str): The name to give the uploaded file in GCS.

  Returns:
    gsutil URI of the file.
  """
  # Append file suffix if not provided in destination_blob
  if pathlib.Path(destination_blob).suffix:
    full_destination_blob = destination_blob
  else:
    suffix = pathlib.Path(source_file_path).suffix
    full_destination_blob = f"{destination_blob}{suffix}"

  logging.info(
      "Uploading to GCP - bucket_name = %s, source_file = %s, destination_blob"
      " = %s",
      bucket_name,
      source_file_path,
      full_destination_blob,
  )

  try:
    client = storage.Client()
    # Check if the local file exists before trying to upload
    if not os.path.isfile(source_file_path):
      raise FileNotFoundError(f"File not found: {source_file_path}")

    blob = client.bucket(bucket_name).blob(full_destination_blob)
    blob.upload_from_filename(source_file_path)
    gcs_uri = f"gs://{bucket_name}/{full_destination_blob}"
    logging.info("File uploaded successfully to %s", gcs_uri)
    return gcs_uri

  except FileNotFoundError as e:
    logging.error("Local file not found: %s. Error: %s", source_file_path, e)
    raise
  except google_exceptions.NotFound as e:
    logging.error("GCS bucket not found: %s. Error: %s", bucket_name, e)
    raise
  except google_exceptions.Forbidden as e:
    logging.error(
        "Permission denied accessing GCS bucket: %s. Error: %s", bucket_name, e
    )
    raise
  except Exception as e:
    logging.error("Error while trying to upload to GCP: %s", e)
    raise
