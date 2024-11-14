"""Tests for utility functions in gcs_utils.py."""

import unittest
from unittest import mock
from util import gcs_utils
from google.cloud import storage


class GcsUtilsTest(unittest.TestCase):

  def setUp(self):
    """Set up for test methods."""
    super().setUp()
    self.bucket_name = "bucket"
    self.file_name = "somevideoid/testfile.mp3"
    self.test_file_path = "tests/audio/goldens/audio.mp3"

  @mock.patch.object(storage, "Client")
  def test_write_success(self, mock_storage_client):
    mock_bucket = mock_storage_client.return_value.bucket
    mock_blob = mock_bucket.return_value.blob

    expected_gs_uri = "gs://bucket/somevideoid/testfile.mp3"

    uri = gcs_utils.upload_to_gcs(
        self.test_file_path, self.bucket_name, self.file_name
    )

    mock_storage_client.assert_called_once()
    mock_bucket.assert_called_once_with(self.bucket_name)
    mock_blob.assert_called_once_with(self.file_name)
    mock_blob.return_value.upload_from_filename.assert_called_once()
    self.assertEqual(expected_gs_uri, uri)
    
  @mock.patch.object(storage, "Client")
  def test_write_failure(self, mock_storage_client):
    mock_bucket = mock_storage_client.return_value.bucket
    mock_blob = mock_bucket.return_value.blob
    mock_blob.return_value.upload_from_filename.side_effect = Exception()

    with self.assertRaises(Exception):
      gcs_utils.upload_to_gcs(
          self.test_file_path, self.bucket_name, self.file_name
      )

    mock_storage_client.assert_called_once()
    mock_bucket.assert_called_once_with(self.bucket_name)
    mock_blob.assert_called_once_with(self.file_name)


if __name__ == "__main__":
  unittest.main()
