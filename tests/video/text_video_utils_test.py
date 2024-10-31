import unittest

from PIL import Image
from truth import truth
from video import text_video_utils


class TextVideoUtilsTest(unittest.TestCase):
  def test_get_main_color(self):
    # Create a test image that is predominantly red
    red_image = Image.new("RGB", (200, 200), (255, 0, 0))
    red_image.save("test_red_image.jpg")

    main_color = text_video_utils.get_main_color("test_red_image.jpg")
    truth.AssertThat(main_color).IsEqualTo("#fe0000")

  def text_wrap_title(self):
    input_text = (
        "This is a sample text for testing the insert newline function."
    )
    formatted_text = text_video_utils.text_wrap_title(input_text, 6)
    expected_text = (
        "This is a sample text\n for testing the text wrap\n function."
    )
    truth.AssertThat(formatted_text).IsEqualTo(expected_text)

  def test_text_wrap_title_standard_case(self):
    input_text = (
        "This is a sample text to test the insert newline function that adds a"
        " line break after every six words."
    )
    expected_output = (
        "This is a sample text to\n test the insert newline function that\n"
        " adds a line break after every\n six words."
    )
    result = text_video_utils.text_wrap_title(input_text, 6)
    truth.AssertThat(result).IsEqualTo(expected_output)

  def test_text_wrap_title_short_text(self):
    input_text = "Short title"
    expected_output = "Short title"
    result = text_video_utils.text_wrap_title(input_text, 6)
    truth.AssertThat(result).IsEqualTo(expected_output)

  def test_text_wrap_title_exactly_six_words(self):
    input_text = "One two three four five six"
    expected_output = "One two three four five six"
    result = text_video_utils.text_wrap_title(input_text, 6)
    truth.AssertThat(result).IsEqualTo(expected_output)

  def test_text_wrap_title_eleven_words(self):
    input_text = "This is another title with exactly eleven words only"
    expected_output = "This is another title with exactly\n eleven words only"
    result = text_video_utils.text_wrap_title(input_text, 6)
    truth.AssertThat(result).IsEqualTo(expected_output)
