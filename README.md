# README

## Solution Description
This python based solution scrapes text and images from an existing news article from a webpage, generates an AI summary, an Audio from the summary, and finally produces a video file (.mp4) which is a concatenation of the images with some visual effects.

## Requirements
* Google Cloud project with Google Cloud Storage, Vertex AI, and Text-to-Speech enabled APIs.
* Valid news article website content
* AdManager360 as to allow ad insertion


## Environment setup
* Install the following python libraries (requirement.txt pending):

    * pip3 install google-cloud-aiplatform
    * pip3 install google-cloud-texttospeech
    * pip3 install vertexai
    * pip3 install google-cloud-speech
    * pip3 install srt
    * (and any other default package as needed for execution)

* Install the gCloud CLI [Link](https://cloud.google.com/sdk/docs/install)
* Set up GCP default client credentials [Link](https://cloud.google.com/docs/authentication/provide-credentials-adc)
* Install the ffmpeg CLI: [Link](https://ffmpeg.org/download.html)
* Add the article text to a file called Nota.txt in the root of the project (or any other name, it is a parameter in the execution)
* Add the article images as files imagen0.jpg, imagen1.jpg, imagen2.jpg, etc. The prefix ("imagen") can be changed as needed based on constant _IMAGE_FILE_NAME.
* Change the AI prompt as needed (current is in Spanish) in function_summarize_article. A version that allows prompt language change is being developed.
* Change the language of the input/output in constants _LANGUAGE, _VOICE, _SSML_GENDER. All of these parameters can be obtained from: https://cloud.google.com/text-to-speech/docs/voices


## Execution

1. python3 ./video_generator.py "genvideo" -ti "./Nota.txt" -ii "." -gcp "project" (make sure to change the project as per the GCP project being used)

# Disclaimer:
Copyright 2024 Google LLC. This solution, including any related sample code or data, is made available on an “as is,” “as available,” and “with all faults” basis, solely for illustrative purposes, and without warranty or representation of any kind. This solution is experimental, unsupported and provided solely for your convenience. Your use of it is subject to your agreements with Google, as applicable, and may constitute a beta feature as defined under those agreements. To the extent that you make any data available to Google in connection with your use of the solution, you represent and warrant that you have all necessary and appropriate rights, consents and permissions to permit Google to use and process that data. By using any portion of this solution, you acknowledge, assume and accept all risks, known and unknown, associated with its usage, including with respect to your deployment of any portion of this solution in your systems, or usage in connection with your business, if at all.