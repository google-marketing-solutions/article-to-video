import os
import unittest

from moviepy.editor import CompositeVideoClip
from moviepy.editor import VideoFileClip
from storyboarding.model import Storyboard
from storyboarding.model import TextOverlay
from video.create_text_overlay_step import create_text_overlay_video_clip
from video.create_text_overlay_step import wrap_text_by_words


class CreateTextOverlayStepTest(unittest.TestCase):

  def setUp(self):
    """Initialize the sample data for testing text overlay functions."""
    super().setUp()
    self.sample_text = "Sample text in the center!"
    self.storyboard = Storyboard(
        scenes=[],
        main_audio_path="",
        text_overlays=[],
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
    """Test wrapping with a number of words per line greater than total words."""
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
        start_time=4,
        end_time=10,
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

  def test_positions_and_validate_goldens(self):
    """Test text overlay creation for each position option and validate against golden files."""
    positions = [
        ("left", "bottom"),
        ("center", "center"),
        ("right", "top"),
    ]
    transitions_in = [
        "slide_from_left",
        "slide_from_right",
        "slide_from_bottom",
        "fade_in",
    ]
    transition_out = "fade_out"
    video_path = "tests/video/goldens/7_withlogovideo_1min.mp4"
    video_clip = VideoFileClip(video_path)
    generated_files = []  # Track files to clean up later

    for position in positions:
      for transition_in in transitions_in:
        position_x, position_y = position
        text_overlay = self.create_text_overlay(
            position_x, position_y, transition_in, transition_out
        )

        textclip = create_text_overlay_video_clip(
            video_height=1080, video_width=1920, text_overlay=text_overlay
        )
        # Generate the final composite video
        final_clip = CompositeVideoClip([video_clip] + [textclip])
        output_dir = "./tests/video/generated/create_overlays_testing"
        output_path = (
            f"{position_x}_"
            f"{position_y})_{transition_in}_with_{transition_out}.mp4"
        )

        if not os.path.exists(output_dir):
          os.makedirs(output_dir)
        final_output_path = output_dir + "/" + output_path
        final_clip.write_videofile(final_output_path)
        print(f"Wrote to output_path {final_output_path}")
        generated_files.append(final_output_path)  # Track file

        # Validate against golden file
        golden_path = (
            f"tests/video/goldens/overlays/{position_x}_"
            f"{position_y}_{transition_in}_with_{transition_out}.mp4"
        )
        files_equal = True
        with (
            open(golden_path, "rb") as golden_file,
            open(final_output_path, "rb") as output_file,
        ):
          while True:
            golden_chunk = golden_file.read(1000)
            output_chunk = output_file.read(1000)
            if not golden_chunk and not output_chunk:
              break
            if golden_chunk != output_chunk:
              files_equal = False
              break

        self.assertTrue(files_equal)
        print(f"Golden file validation successful for {output_path}")

    # Cleanup: Remove all generated files
    print("Cleaning up generated files...")
    for file_path in generated_files:
      if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted {file_path}")
    print("All generated files cleaned up.")
