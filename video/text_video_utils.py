"""Utility functions to overlay text on videos."""

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


def get_main_color(image_path):
  """Returns in HEX the main color of an image using K-Means clustering.

  Args:
      image_path: The path to the image file.

  Returns:
      A string representing the hexadecimal color code of the main color.
  """
  img = Image.open(image_path)
  img = img.convert("RGB")
  img = img.resize((200, 200))

  img_array = np.array(img)
  pixels = img_array.reshape(-1, 3)

  kmeans = KMeans(n_clusters=1)
  kmeans.fit(pixels)

  main_color_rgb = kmeans.cluster_centers_[0]
  main_color_rgb = tuple(map(int, main_color_rgb))

  # Convert RGB to HEX
  hex_color = "#{:02x}{:02x}{:02x}".format(*main_color_rgb)

  return hex_color


def text_wrap_title(text, words_per_line):
  """Inserts a newline character in the input text.

  This function splits the input text into words and then joins them back
  with a newline, creating a multi-line string. It is useful for formatting long
  titles or text blocks to fit within a specified width, such as when overlaying
  text on video.

  Args:
      text (str): The input text to format.
      words_per_line (str): The amount of words to have one line.

  Returns:
      str: The formatted text with newline characters inserted.
  """
  words = text.split()
  formatted_text = ""

  for i in range(0, len(words), words_per_line):
    formatted_text += " ".join(words[i : i + words_per_line]) + "\n "

  return formatted_text.strip()
