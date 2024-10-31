"""Text generation pipeline step for generating subtitles."""

import datetime
import re

import pipeline
import srt


class GenerateSubtitlesStep(
    pipeline.video_generation_pipeline.VideoGenerationPipeline
):
  """A pipeline step that generates an SRT subtitle file from SSML output and timepoints.

  Attributes:
      _SRT_FILE_OUTPUT (str): The name of the output SRT file.
  """

  _SRT_FILE_OUTPUT: str = "4_subtitles.srt"

  def __init__(
      self, context: pipeline.video_generation_context.VideoGenerationContext
  ):
    """Initializes the GenerateSubtitlesStep with context information.

    Args:
        context (VideoGenerationContext): The context object containing
          configurations such as work directory and GCP project.
    """
    super().__init__(context)
    self.workdir = context.workdir
    self.gcp_project = context.gcp_project

  def _generate_subs(
      self, output_srt_path: str, ssml_output: str, timepoints: str
  ) -> str:
    """Generates an SRT file from SSML and timepoint data and writes it to the specified path.

    Args:
        output_srt_path (str): The file path where the SRT file will be saved.
        ssml_output (str): The SSML string containing subtitle content with
          `<mark>` tags.
        timepoints (str): A list of timepoints specifying when each subtitle
          should appear.

    Returns:
        str: The path to the generated SRT file.
    """
    srt_output = []

    # Extract text segments from SSML with <mark> tags
    text_segments = re.findall(r'<mark name="mark\d+"/>[^<]+', ssml_output)

    # Ensure the number of text segments and timepoints are aligned
    min_length = min(len(text_segments), len(timepoints))

    for i in range(min_length):
      start_time = datetime.timedelta(seconds=timepoints[i].time_seconds)
      end_time = (
          datetime.timedelta(seconds=timepoints[i + 1].time_seconds)
          if i < min_length - 1
          else start_time + datetime.timedelta(seconds=1)
      )

      # Add each subtitle segment to the SRT output
      content = text_segments[i].strip()
      if content:
        srt_output.append(
            srt.Subtitle(
                index=i + 1, start=start_time, end=end_time, content=content
            )
        )

    # Write the SRT file
    with open(output_srt_path, "w") as f:
      f.write(srt.compose(srt_output))

    return output_srt_path

  def __call__(self, params) -> str:
    """Generates and writes an SRT subtitle file using SSML and timepoint data.

    Args:
        params (tuple): A tuple containing: - ssml_output (str): The SSML text
          with subtitle content. - timepoints (list): List of timepoints
          indicating subtitle timings.

    Returns:
        str: The path to the generated SRT subtitle file.
    """
    (ssml_output, timepoints) = params
    output_path = f"{self.workdir}/{self._SRT_FILE_OUTPUT}"
    self.logger.info(f"Generating subtitles and saving to {output_path}...")
    subtitles = self._generate_subs(output_path, ssml_output, timepoints)
    return subtitles
