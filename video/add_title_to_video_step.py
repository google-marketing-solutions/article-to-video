"""Video generation pipeline step for adding article title to video."""

from moviepy.editor import CompositeVideoClip
from moviepy.editor import TextClip
from moviepy.editor import VideoFileClip
import pipeline
from video import text_video_utils


class AddTitleToVideoStep(pipeline.VideoGenerationStep):
  """Class responsible for adding the article title overlay to the video."""

  _OUTPUT_FILE: str = "7a_withtitlevideo.mp4"

  def __init__(self, context: pipeline.VideoGenerationContext):
    super().__init__(context)
    self.workdir = context.workdir

  def __call__(self, params) -> str:
    (article_title, video_path) = params
    output_path = f"{self.workdir}/{self._OUTPUT_FILE}"
    self.logger.info(
        f"Adding title ({article_title}) to {video_path} and writing to"
        f" {output_path}..."
    )
    try:
      hex_color_background = text_video_utils.get_main_color(
          "./input/favicon.ico"
      )
    except FileNotFoundError:
      hex_color_background = "#000000"  # Default to black if no favicon
    escaped_article_text = text_video_utils.text_wrap_title(article_title, 6)
    escaped_new_lines_text = escaped_article_text.replace("'", "\u2019")

    try:
      # Overlay the article title
      video_clip = VideoFileClip(video_path)

      # Create the text with a background color
      text_clip = TextClip(
          escaped_new_lines_text,
          fontsize=70,
          color="white",
          bg_color=hex_color_background,
          font="Arial",
          align="West",  # Aligns text to the left
      )

      # Position the text 10% from the top and 5% from the left
      y_position = 0.1 * video_clip.h
      x_position = 0.05 * video_clip.w
      text_clip = text_clip.set_duration(6).set_pos((x_position, y_position))

      # Overlay the text on the video
      final_clip = CompositeVideoClip([video_clip, text_clip])
      final_clip.write_videofile(output_path)

      return output_path

    except Exception as e:  # pylint: disable=broad-except
      self.logger.error(f"Error processing video: {e}")
      return video_path
