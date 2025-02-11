# README

## Solution Description
This is a Python-based solution that processes customer-provided text and image
inputs to convert them into short-form video formats. It generates an AI summary
from the provided text content, an audio track from the summary, and finally
produces a video file (.mp4) that is a concatenation of the provided images with
some visual effects and the audio track as voiceover.

This solution is still under development and should be considered experimental.

## Requirements
* Google Cloud project with Google Cloud Storage, Vertex AI, and Text-to-Speech
  enabled APIs.
* Valid article + related images to convert to a video.

## Environment setup
* Install the requirement.txt libraries.
* Install the gCloud CLI [Link](https://cloud.google.com/sdk/docs/install)
* Set up GCP default client credentials [Link](https://cloud.google.com/docs/authentication/provide-credentials-adc)
* Install the ffmpeg CLI: [Link](https://ffmpeg.org/download.html)
* Install ImageMagick – Mac users can use homebrew: `homebrew install imagemagick` [Link](https://imagemagick.org/script/download.php)
* Update any placeholder values in ```config.yml```

## Execution

### Standalone (CLI)

```bash
usage: video_generator_execution.py [-h] [--config CONFIG] [--video_id VIDEO_ID] --article_path ARTICLE_PATH --image_dir IMAGE_DIR [--disable_text_overlays]
                                    [--burn_in_subtitles] [--language {en-US,en-GB,fr-FR,de-DE,es-ES,pt-BR}] [--step {audio,storyboard,video}] [--debug]

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to the configuration YAML file. Defaults to 'config.yml'.
  --video_id VIDEO_ID   Unique ID for the generated video. If not provided, a UUID will be generated.
  --article_path ARTICLE_PATH, -a ARTICLE_PATH
                        Path to the article text file.
  --image_dir IMAGE_DIR, -i IMAGE_DIR
                        Path to the directory containing images.
  --disable_text_overlays
                        Disables text overlay generation.
  --burn_in_subtitles   When provided, subtitles will be burned into the content.
  --language {en-US,en-GB,fr-FR,de-DE,es-ES,pt-BR}, -l {en-US,en-GB,fr-FR,de-DE,es-ES,pt-BR}
                        The language for the output video. Defaults to 'en-US'.
  --step {audio,storyboard,video}
                        Run a discrete step in the video generation flow.
  --debug, -d           Enable debug logging.
```

To generate a video:

1. Save article contents a text file.
2. Put images into one directory (supported extensions are .jpg, .jpeg, .png,
.gif, .bmp)
3. Provide a human readable video ID (you can also omit this and a UUID will
be generated for the video instead).
3. Run:
```bash
python video_generator_execution.py --article_path path/to/article.txt --image_dir path/to/images/dir --video_id id_for_your_video
```

The video and any other generated assets will be available in the output
directory (configured in config.yml) under a subfolder named for the provided
video ID.

To make edits without regenerating totally from scratch, you can make small
edits to things like timing, animations, and text overlay content in the
storyboard.json file and then regenerate the video based on the updated
storyboard using the ```--step video``` option with the CLI.

### Local Docker

```
sudo docker build -t gtech/video-generation-from-images .
sudo docker run -e PORT=5000 -p 5000:5000 -t gtech/video-generation-from-images
```

### Local Server
```
cd ui
ng build
cd ..
python3 -m flask --app video_generation_from_articles run
```
### Cloud Deploy

```
gcloud builds submit . --substitutions _IMAGE_NAME=atv,_SERVICE_NAME=atv,REPO_NAME=test-repo
```

## Running tests

From the base folder, run

```
python3 -m unittest
```

## Upgrading Dependencies

pip-compile is used to generate the ```requirements.txt``` file. To update
dependencies, make changes to ```requirements.in``` and then use the following
command:

```
pip-compile requirements.in --generate-hashes --upgrade
```

# Disclaimer:
Copyright 2024 Google LLC. This solution, including any related sample code or
data, is made available on an “as is,” “as available,” and “with all faults”
basis, solely for illustrative purposes, and without warranty or representation
of any kind. This solution is experimental, unsupported and provided solely for
your convenience. Your use of it is subject to your agreements with Google, as
applicable, and may constitute a beta feature as defined under those agreements.
To the extent that you make any data available to Google in connection with your
use of the solution, you represent and warrant that you have all necessary and
appropriate rights, consents and permissions to permit Google to use and process
that data. By using any portion of this solution, you acknowledge, assume and
accept all risks, known and unknown, associated with its usage, including with
respect to your deployment of any portion of this solution in your systems, or
usage in connection with your business, if at all.