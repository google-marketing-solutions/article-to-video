import unittest
from unittest import mock

import cv2
from moviepy import editor as mpy
import numpy as np
from video import effects


class EffectsTest(unittest.TestCase):

  def test_zoom_pan_starts_at_initial_center(self):
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    clip = mpy.ImageClip(image, duration=1)
    clip = effects.zoom_pan(clip, initial_position=(20, 22.0), initial_zoom=1.0)

    # first frame should be:
    #   1.0x scaled around the original center
    #   translated by -20.0 pixels from top left in the x direction
    #   translated by -22.0 pixels from top left in the y direction
    matrix = np.float32([
        [1, 0, -20.0],
        [0, 1, -22.0],
    ])
    expected_frame = cv2.warpAffine(image, matrix, (100, 100))

    np.testing.assert_array_equal(expected_frame, clip.get_frame(0))

  def test_zoom_pan_ends_at_target_center(self):
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    clip = mpy.ImageClip(image, duration=1)
    clip = effects.zoom_pan(
        clip,
        initial_position=(20.0, 22.0),
        final_position=(75.0, 72.0),
        initial_zoom=1.0,
        final_zoom=1.0,
    )

    # last frame should be:
    #   1.0x scaled around the new center
    #   translated by -75.0 pixels from top left in the x direction
    #   translated by -72.0 pixels from top left in the y direction
    matrix = np.float32([
        [1, 0, -75.0],
        [0, 1, -72.0],
    ])
    expected_frame = cv2.warpAffine(image, matrix, (100, 100))

    np.testing.assert_array_equal(expected_frame, clip.get_frame(1.0))

  def test_zoom_pan_starts_at_initial_zoom(self):
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    clip = mpy.ImageClip(image, duration=1)
    clip = effects.zoom_pan(
        clip,
        initial_zoom=3.0,
    )

    # first frame should be:
    #   3.0x scaled from center
    matrix = np.float32([
        [3, 0, 0],
        [0, 3, 0],
    ])
    expected_frame = cv2.warpAffine(image, matrix, (100, 100))

    np.testing.assert_array_equal(expected_frame, clip.get_frame(0.0))

  def test_zoom_pan_ends_at_final_zoom(self):
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    clip = mpy.ImageClip(image, duration=1)
    clip = effects.zoom_pan(
        clip,
        initial_zoom=3.0,
        final_zoom=4.0,
    )

    # last frame should be:
    #   4.0x scaled from center
    matrix = np.float32([
        [4, 0, 0],
        [0, 4, 0],
    ])
    expected_frame = cv2.warpAffine(image, matrix, (100, 100))

    np.testing.assert_array_equal(expected_frame, clip.get_frame(1.0))

  def test_zoom_pan_midpoint_fast(self):
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    clip = mpy.ImageClip(image, duration=1)
    clip = effects.zoom_pan(
        clip,
        initial_position=(20.0, 22.0),
        final_position=(75.0, 72.0),
        initial_zoom=1.0,
        final_zoom=4.0,
        style="fast",
    )

    zoom = 3.90625
    scale_ratio = 0.96875

    translate = (np.array([20, 22]) * 1.0 * (1 - scale_ratio)) + (
        np.array([75, 72]) * 4.0 * scale_ratio
    )

    matrix = np.float32([
        [zoom, 0, -translate[0]],
        [0, zoom, -translate[1]],
    ])
    expected_frame = cv2.warpAffine(image, matrix, (100, 100))
    np.testing.assert_allclose(expected_frame, clip.get_frame(0.5), atol=2)

  def test_zoom_pan_midpoint_linear(self):
    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    clip = mpy.ImageClip(image, duration=1)
    clip = effects.zoom_pan(
        clip,
        initial_position=(20.0, 22.0),
        final_position=(75.0, 72.0),
        initial_zoom=1.0,
        final_zoom=4.0,
        style="linear",
    )

    # midpoint frame should be:
    zoom = 2.5
    scale_ratio = 0.5

    translate = (np.float32([20, 22]) * 1.0 * (1 - scale_ratio)) + (
        np.float32([75, 72]) * 4 * scale_ratio
    )

    matrix = np.float32([
        [zoom, 0, -translate[0]],
        [0, zoom, -translate[1]],
    ])
    expected_frame = cv2.warpAffine(image, matrix, (100, 100))
    np.testing.assert_allclose(expected_frame, clip.get_frame(0.5), atol=2)

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_slide_left(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.slide(mock_clip, direction="left")

    mock_zoom_pan.assert_called_once_with(
        mock_clip,
        initial_zoom=1.25,
        initial_position=(0, 10.0),
        final_position=(20.0, 10.0),
    )

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_slide_right(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.slide(mock_clip, direction="right")

    mock_zoom_pan.assert_called_once_with(
        mock_clip,
        initial_zoom=1.25,
        initial_position=(20.0, 10.0),
        final_position=(0.0, 10.0),
    )

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_slide_up(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.slide(mock_clip, direction="up")

    mock_zoom_pan.assert_called_once_with(
        mock_clip,
        initial_zoom=1.25,
        initial_position=(10.0, 0),
        final_position=(10.0, 20.0),
    )

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_slide_down(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.slide(mock_clip, direction="down")

    mock_zoom_pan.assert_called_once_with(
        mock_clip,
        initial_zoom=1.25,
        initial_position=(10.0, 20.0),
        final_position=(10.0, 0),
    )

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_zoom_in_slow(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.zoom(mock_clip, direction="in", fast=False)

    args, kwargs = mock_zoom_pan.call_args
    self.assertEqual(len(args), 1)
    self.assertEqual(args[0], mock_clip)
    self.assertEqual(kwargs["initial_zoom"], 1.0)
    self.assertEqual(kwargs["final_zoom"], 1.5)
    np.testing.assert_array_equal(kwargs["initial_position"], (0, 0))
    np.testing.assert_allclose(kwargs["final_position"], (16.66, 16.66), atol=1)
    self.assertEqual(kwargs["style"], "linear")

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_zoom_out_fast(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.zoom(mock_clip, direction="out", fast=True)

    args, kwargs = mock_zoom_pan.call_args
    self.assertEqual(len(args), 1)
    self.assertEqual(args[0], mock_clip)
    self.assertEqual(kwargs["initial_zoom"], 1.5)
    self.assertEqual(kwargs["final_zoom"], 1.0)
    np.testing.assert_allclose(
        kwargs["initial_position"], (16.66, 16.66), atol=1
    )
    np.testing.assert_array_equal(kwargs["final_position"], (0, 0))
    self.assertEqual(kwargs["style"], "fast")

  @mock.patch.object(effects, "zoom_pan", autospec=True)
  def test_zoom_out_slow(self, mock_zoom_pan):
    mock_clip = mock.MagicMock(spec=mpy.ImageClip)
    mock_clip.size = (100, 100)

    effects.zoom(mock_clip, direction="out", fast=False)

    args, kwargs = mock_zoom_pan.call_args
    self.assertEqual(len(args), 1)
    self.assertEqual(args[0], mock_clip)
    self.assertEqual(kwargs["initial_zoom"], 1.5)
    self.assertEqual(kwargs["final_zoom"], 1.0)
    np.testing.assert_allclose(
        kwargs["initial_position"], (16.66, 16.66), atol=1
    )
    np.testing.assert_array_equal(kwargs["final_position"], (0, 0))
    self.assertEqual(kwargs["style"], "linear")


@mock.patch.object(effects, "zoom_pan", autospec=True)
def test_zoom_pan_to_fast(self, mock_zoom_pan):
  mock_clip = mock.MagicMock(spec=mpy.ImageClip)
  mock_clip.size = (100, 100)
  target = (25, 50)

  effects.zoom_pan_to(mock_clip, target, fast=True)

  args, kwargs = mock_zoom_pan.call_args
  self.assertEqual(len(args), 1)
  self.assertEqual(args[0], mock_clip)
  self.assertEqual(kwargs["initial_zoom"], 1.0)
  self.assertEqual(kwargs["final_zoom"], 2.0)
  np.testing.assert_array_equal(kwargs["initial_position"], (0, 0))
  np.testing.assert_allclose(kwargs["final_position"], (-12.5, -25.0), atol=1)
  self.assertEqual(kwargs["style"], "fast")


@mock.patch.object(effects, "zoom_pan", autospec=True)
def test_zoom_pan_to_slow(self, mock_zoom_pan):
  mock_clip = mock.MagicMock(spec=mpy.ImageClip)
  mock_clip.size = (100, 100)
  target = (25, 50)

  effects.zoom_pan_to(mock_clip, target, fast=False)

  args, kwargs = mock_zoom_pan.call_args
  self.assertEqual(len(args), 1)
  self.assertEqual(args[0], mock_clip)
  self.assertEqual(kwargs["initial_zoom"], 1.0)
  self.assertEqual(kwargs["final_zoom"], 2.0)
  np.testing.assert_array_equal(kwargs["initial_position"], (0, 0))
  np.testing.assert_allclose(kwargs["final_position"], (-12.5, -25.0), atol=1)
  self.assertEqual(kwargs["style"], "linear")


if __name__ == "__main__":
  unittest.main()
