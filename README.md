# README

## Solution Description
This is a Python-based solution that processes customer-provided text and image
inputs to convert them into short-form video formats. It generates an AI summary
from the provided text content, an audio track from the summary using Gemini 2.5
Pro TTS, and finally produces a video file (.mp4) that is a concatenation of the
provided images with some visual effects and the audio track as voiceover.

**Key Features:**
* **83 Language Support** - Gemini TTS supports 24 GA languages and 59 Preview
  languages
* **Natural Multi-Speaker Audio** - Up to 8 universal voices (Kore, Charon,
  Aoede, Puck, Fenrir, Leda, Zephyr, Orus)
* **High Quality Audio** - 24kHz LINEAR16 audio output
* **Modern Image Format Support** - Supports WEBP, JPEG, PNG, GIF, and BMP

This solution is still under development and should be considered experimental.

### Colab

Try Article to Video in Colab!

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/google-marketing-solutions/article-to-video/blob/main/colab/Article_to_Video.ipynb)

## Requirements
* A Google Cloud project with the following APIs enabled:
  * **Vertex AI API / Agent Platform API** (`aiplatform.googleapis.com`)
  * **Cloud Text-to-Speech API** (`texttospeech.googleapis.com`)
  * **Cloud Natural Language API** (`language.googleapis.com`)
  * **Cloud Storage API** (`storage.googleapis.com`)
* Valid article + related images to convert to a video.
* Python 3.12 or higher recommended.
* google-cloud-texttospeech >= 2.31.0 (for Gemini TTS support)

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
                                    [--multi_text] [--splash_image SPLASH_IMAGE] [--burn_in_subtitles] [--language LANGUAGE] [--step {audio,storyboard,video}] [--debug]

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to the configuration YAML file. Defaults to 'config.yml'.
  --video_id VIDEO_ID   Unique ID for the generated video. If not provided, a UUID will be generated.
  --article_path ARTICLE_PATH, -a ARTICLE_PATH
                        Path to the article text file.
  --image_dir IMAGE_DIR, -i IMAGE_DIR
                        Path to the directory containing images.
  --multi_text MULTI_TEXT
                        Specify that the LLM is to summarize multiple articles, not just 1.
                        Changes prompt accordingly.
  --splash_image SPLASH_IMAGE
                        Specifies the file name of the splash image (do not
                        include filename extension)
                        indicating the image to optionally use at the beginning
                        of the video
  --disable_text_overlays
                        Disables text overlay generation.
  --burn_in_subtitles   When provided, subtitles will be burned into the content.
  --language LANGUAGE, -l LANGUAGE
                        The language for the output video. Supports 83 languages via Gemini TTS.
                        Popular options: en-US, en-GB, es-ES, fr-FR, de-DE, pt-BR, ja-JP, ko-KR, 
                        zh-CN, ar-EG, hi-IN, it-IT, nl-NL, pl-PL, ru-RU, tr-TR, and many more.
                        See pipeline/video_generation_context.py for the complete list.
                        Defaults to 'en-US'.
  --step {audio,storyboard,video}
                        Run a discrete step in the video generation flow.
  --debug, -d           Enable debug logging.
```

To generate a video:

1. Save article contents a text file.
2. Put images into one directory (supported extensions are .jpg, .jpeg, .png,
.gif, .bmp, .webp)
3. Provide a human readable video ID (you can also omit this and a UUID will
be generated for the video instead).
3. Run:
```bash
python video_generator_execution.py --article_path path/to/article.txt --image_dir path/to/images/dir --video_id id_for_your_video
```

For multi-speaker narration (conversational style with 2 voices), add the
`--multi_voice` flag:
```bash
python video_generator_execution.py --article_path path/to/article.txt --image_dir path/to/images/dir --video_id id_for_your_video --multi_voice
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
[sudo] docker build -t gtech/video-generation-from-images .
[sudo] docker run -e PORT=5000 -p 5000:5000 -t gtech/video-generation-from-images
```

The docker image with build and deploy the UI, but the UI is still experimental
and will not work correctly at this time. However, the CLI can be accessed with
the docker by running the following command (you'll also need to configure your
Google Cloud ADC):

```
docker exec -it <CONTAINER_ID> /bin/bash
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
python3 -m unittest discover -p "*_test.py"
```

## Upgrading Dependencies

pip-compile is used to generate the ```requirements.txt``` file. To update
dependencies, make changes to ```requirements.in``` and then use the following
command:

```
pip-compile requirements.in --generate-hashes --upgrade
```

**Note:** The solution requires `google-cloud-texttospeech >= 2.31.0` for Gemini
TTS multi-speaker synthesis support.

## Language Support

This solution uses Gemini 2.5 Pro TTS which supports 83 languages:

**Generally Available (GA) - 24 Languages:**
Arabic (Egypt), Bangla (Bangladesh), Dutch (Netherlands), English (India/US),
French (France), German (Germany), Hindi (India), Indonesian (Indonesia),
Italian (Italy), Japanese (Japan), Korean (South Korea), Marathi (India),
Polish (Poland), Portuguese (Brazil), Romanian (Romania), Russian (Russia),
Spanish (Spain), Tamil (India), Telugu (India), Thai (Thailand), Turkish
(Turkey), Ukrainian (Ukraine), Vietnamese (Vietnam)

**Preview - 59 Additional Languages:**
Including Afrikaans, Albanian, Amharic, Armenian, Azerbaijani, Basque,
Belarusian, Bulgarian, Burmese, Catalan, Chinese (Mandarin), Croatian, Czech,
Danish, Estonian, Filipino, Finnish, Galician, Georgian, Greek, Gujarati,
Hebrew, Hungarian, Icelandic, Javanese, Kannada, and many more.

For the complete list, see `pipeline/video_generation_context.py` or the
[Gemini TTS documentation](https://cloud.google.com/text-to-speech/docs/gemini-tts#available_languages).

## Migration Notes

This solution has been migrated from the legacy Cloud Text-to-Speech API to
Gemini 2.5 Pro TTS. See `CHANGES.md` for detailed migration documentation
including:
* API changes and improvements
* Language expansion (6 → 83 languages)
* Voice updates (8 universal voices)
* Bug fixes and enhancements

# Disclaimer:
Copyright 2025 Google LLC. This solution, including any related sample code or
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