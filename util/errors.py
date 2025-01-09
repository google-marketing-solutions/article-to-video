"""Errors for the video generation process."""


class GeminiError(Exception):
  """Used when the Gemini does not return the expected response.

  args:
    message (str): Explanation of the error.
    code (int, optional): An error code for programmatic handling.
  """

  def __init__(self, message, code=None):
    super().__init__(message)
    self.message = message
    self.code = code

  def __str__(self):
    if self.code:
      return f"{self.code}: {self.message}"
    return self.message
