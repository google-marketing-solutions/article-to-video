"""Errors for the video generation process."""


class NoImagesFoundError(Exception):
  """Used when the input folder for generating the video contains no images."""

  pass
