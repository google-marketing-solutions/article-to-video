import os
import tempfile
import unittest
from unittest import mock

import text


_SINGLE_VOICE_SCRIPT_JSON = """
{
  "speakers": [
    {
    "persona": "Lead Anchor",
    "voice": "en-US-Studio-O"
    },
  ],
  "statements": [
    {
    "voice": "en-US-Studio-O",
    "statement": "first statement"
    },
    {
    "voice": "en-US-Studio-O",
    "statement": "second statement"
    },
  ],
  "text": "first statement second statement"
}
"""

_MULTI_VOICE_SCRIPT_JSON = """
{
  "speakers": [
    {
    "persona": "Lead Anchor",
    "voice": "en-US-Studio-O"
    },
    {
    "persona": "Second Anchor",
    "voice": "en-US-Studio-Q"
    }
  ],
  "statements": [
    {
    "voice": "en-US-Studio-O",
    "statement": "first statement"
    },
    {
    "voice": "en-US-Studio-Q",
    "statement": "second statement"
    },
  ],
  "text": "first statement second statement"
}
"""


class SummarizeTextStepTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.workdir = tempfile.TemporaryDirectory()
    os.makedirs(self.workdir.name + "/somearticleid", exist_ok=True)

  def tearDown(self):
    self.workdir.cleanup()
    return super().tearDown()

  @mock.patch.object(text, "ScriptGenerator", autospec=True)
  def test_generate_script(self, mock_generator):
    step = text.summarize_text_step.SummarizeTextStep("workdir", mock_generator)

    self.assertEqual(
        step("some article content"),
        mock_generator.generate.return_value,
    )


if __name__ == "__main__":
  unittest.main()
