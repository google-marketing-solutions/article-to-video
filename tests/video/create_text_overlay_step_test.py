import unittest
from storyboarding.model import Storyboard
from storyboarding.model import TextOverlay
from video.create_text_overlay_step import wrap_text_by_words


class CreateTextOverlayStepTest(unittest.TestCase):

  def setUp(self):
    """Initialize the sample data for testing text overlay functions."""
    super().setUp()
    self.sample_text = "Sample text in the center!"
    self.storyboard = Storyboard(
        scenes=[], main_audio_path="", text_overlays=[], srt_path="my/path"
    )

  def test_wrap_text_by_words_basic(self):
    """Test basic wrapping functionality with standard input."""
    text = "This is a simple test to verify text wrapping by word count."
    words_per_line = 4
    expected_output = (
        "This is a simple\ntest to verify text\nwrapping by word count."
    )
    self.assertEqual(wrap_text_by_words(text, words_per_line), expected_output)

  def test_wrap_text_with_large_words_per_line(self):
    """Test wrapping with number of words per line greater than total words."""
    text = "This test should return a single line"
    words_per_line = 10  # Larger than the total words in the text
    expected_output = "This test should return a single line"
    self.assertEqual(wrap_text_by_words(text, words_per_line), expected_output)

  def test_wrap_text_with_empty_input(self):
    """Test wrapping with an empty string."""
    text = ""
    words_per_line = 3
    expected_output = ""
    self.assertEqual(wrap_text_by_words(text, words_per_line), expected_output)

  def test_wrap_text_with_various_spaces(self):
    """Test wrapping with input text containing extra spaces."""
    text = "  Multiple   spaces  in   input text "
    words_per_line = 2
    expected_output = "Multiple spaces\nin input\ntext"
    self.assertEqual(
        wrap_text_by_words(text.strip(), words_per_line), expected_output
    )

  def create_text_overlay(
      self, position_x, position_y, transition_in, transition_out
  ):
    return TextOverlay(
        start_time=1,
        end_time=5,
        text="Sample text in the center!",
        font_style="Helvetica-Bold",
        font_size=60,
        background_color="#000000",
        position=(position_x, position_y),
        alignment="west",
        transition_in=transition_in,
        transition_out=transition_out,
        method="label",
    )
