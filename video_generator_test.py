# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for video_generator.py."""

import argparse
import pathlib
import unittest
from unittest import mock

import google

import video_generator

class VideoGeneratorTest(unittest.TestCase):

  def test_execution_bad_input_paths(self):
    "Tests for valid input params before processing."


    parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    main_parser = subparsers.add_parser(
      "genvideo", help=video_generator.main.__doc__
    )
    main_parser.add_argument("-ti", "--text-input", dest="text_input_path")
    main_parser.add_argument("-ii", "--image-input", dest="image_input_path")
    main_parser.add_argument("-gcp", "--google-cloud-project",
                             dest="gcp_project")
    args = parser.parse_args(
      ["genvideo", "-ti", "bad_path", "-ii", "bad_path", "-gcp", "existing_gcp"]
    )

    with self.assertRaises(FileNotFoundError):
      video_generator.main(args)


  def test_execution_bad_input_gcp(self):
    "Tests for valid gcp before processing."

    parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    main_parser = subparsers.add_parser(
      "genvideo", help=video_generator.main.__doc__
    )
    main_parser.add_argument("-ti", "--text-input", dest="text_input_path")
    main_parser.add_argument("-ii", "--image-input", dest="image_input_path")
    main_parser.add_argument("-gcp", "--google-cloud-project",
                             dest="gcp_project")

    args = parser.parse_args(
      ["genvideo", "-ti", "Nota.txt", "-ii", "./", "-gcp",
       "bad_gcp_xyzzzz12345985973"]
    )

    with self.assertRaises(google.api_core.exceptions.PermissionDenied):
      video_generator.main(args)

if __name__ == "__main__":
  unittest.main()