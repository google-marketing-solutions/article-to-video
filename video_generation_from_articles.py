"""Flask app for handling HTTP responses."""

import logging
import os
import time
import uuid
import flask

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
