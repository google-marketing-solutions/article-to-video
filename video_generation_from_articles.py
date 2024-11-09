"""Flask app for handling HTTP responses."""

import logging
import os
import time
import uuid
import flask
import pipeline
from video import video_generation_errors
import video_generator_execution
import yaml

config = yaml.safe_load(open('config.yml'))

logging.basicConfig(level=logging.INFO)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app = flask.Flask(__name__)


@app.route('/')
def index():
  return flask.render_template('index.html')


@app.route('/favicon.ico')
def favicon():
  return flask.send_from_directory(
      os.path.join(app.root_path, 'static'),
      'favicon.ico',
      mimetype='image/vnd.microsoft.icon',
  )


@app.route('/video/new_id', methods=['GET'])
def generate_video_id():
  return flask.jsonify({'video_id': str(uuid.uuid4())})


@app.route('/video/<video_id>/image/<image_path>', methods=['GET'])
def get_image(video_id: str, image_path: str):
  return flask.send_from_directory(
      os.path.join(app.root_path, f'uploads/{video_id}/images'), image_path
  )


@app.route('/video/<video_id>/image/upload', methods=['POST'])
def upload_file(video_id: str):
  """Uploads file to local folder.

  Args:
      video_id: Id of the video currently being generated.

  Returns:
      JSON with the path to the file uploaded.
  """
  if 'file' not in flask.request.files:
    return flask.jsonify({'error': 'Please provide file'})

  file = flask.request.files['file']
  # If the user does not select a file, the browser submits an
  # empty file without a filename.
  if not file.filename:
    return flask.jsonify({'error': 'Filename blank'})

  extension = file.filename.rsplit('.', 1)[1].lower()

  if extension not in ALLOWED_EXTENSIONS:
    return flask.jsonify(
        {'error': f'The supported file formats are: {ALLOWED_EXTENSIONS}'}
    )

  folder = f'uploads/{video_id}/images'
  image_file = f'{int(time.time())}.{extension}'

  os.makedirs(folder, exist_ok=True)
  upload_path = os.path.join(folder, image_file)
  file.save(upload_path)

  return flask.jsonify({'file': image_file})


@app.route('/video/<video_id>/generate', methods=['POST'])
def generate_video(video_id: str):
  """Generates a video with given inputs.

  Args:
      video_id: Id of the video currently being generated.

  Returns:
      JSON with the path to the file generated.
  """
  data = flask.request.get_json()
  try:
    context = pipeline.VideoGenerationContext(config, data, video_id)
    video_uri = video_generator_execution.VideoGeneratorExecution().genvideo(
        context
    )
    return flask.jsonify({
        'status': 'Your video has been generated successfully',
        'path': video_uri,
    })
  except video_generation_errors.NoImagesFoundError:
    return flask.jsonify(
        {'status': 'Not enought suitable images found in article'}
    )
  except Exception:  # pylint: disable=broad-exception-caught
    return flask.jsonify({'status': 'Unknown error generating your video.'})
