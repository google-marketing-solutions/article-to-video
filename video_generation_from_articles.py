"""Flask app for handling HTTP responses."""

import glob
import logging
import os
import uuid
import flask
import pipeline
from util import gcs_utils
import vertexai
from video import video_generation_errors
import video_generator_execution
import yaml

config = yaml.safe_load(open('config.yml'))

vertexai.init(project=config['gcp_project'], location=config['gcp_location'])

logging.basicConfig(level=logging.INFO)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', '.gif', '.bmp'}

app = flask.Flask(__name__)


@app.route('/')
def index():
  return flask.send_from_directory(
      os.path.join(app.root_path, 'static'), 'index.html'
  )


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
  image_file = file.filename

  os.makedirs(folder, exist_ok=True)
  upload_path = os.path.join(folder, file.filename)
  file.save(upload_path)

  return flask.jsonify({'file': image_file})


@app.route('/video/<video_id>/generate', methods=['POST'])
def generate_video(video_id: str):
  """Generates a video with given inputs.

  This endpoint accepts `multipart/form-data` requests.

  **Path Parameter:**
    - `video_id` (str): A unique identifier for this video generation request.

  **Multipart/form-data Parameters:**
    - `article_content` (file): The text file (e.g., .txt) containing the
      article content.
    - Image files (files): One or more image files (e.g., .png, .jpg,
      .jpeg, .gif, .bmp). The server processes all uploaded files with
      allowed extensions. You can use distinct names for each file part
      (e.g., `image_file1`, `image_file2`).
    - All of the command line parameters supported by VideoGenerator are also
      supported.

  Args:
      video_id: Id of the video currently being generated.

  Returns:
      JSON with the path to the file generated.
  """
  request_params = dict(flask.request.form)
  print(request_params)

  image_paths = []
  file_storage = flask.request.files.values()
  for file in file_storage:
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
      logging.log(
          logging.INFO, 'Skipping unsupported file extnsion: %s', extension
      )
      continue

    folder = f'uploads/{video_id}/images'

    os.makedirs(folder, exist_ok=True)
    upload_path = os.path.join(folder, file.filename)
    file.save(upload_path)
    image_paths.append(upload_path)

  try:
    if 'article_content' in flask.request.files:
      article_bytes = flask.request.files['article_content'].read()
      request_params['article_content'] = article_bytes.decode('utf-8')
    request_params['image_paths'] = image_paths or glob.glob(
        f'uploads/{video_id}/images/*'
    )

    # In a production-ready solution, the video generation process would
    # typically be handled by a separate, asynchronous worker process or a
    # managed service  keep the main application responsive. For simplicity in
    # this demo, it's handled synchronously.
    context = pipeline.VideoGenerationContext(config, request_params, video_id)
    video_path = video_generator_execution.VideoGenerator().generate_video_step(
        context
    )
    gcs_uri = gcs_utils.upload_to_gcs(
        video_path,
        config['gcs_bucket_name'],
        os.path.join('generated_videos', video_id, 'video.mp4'),
    )

    return flask.jsonify({
        'status': 'Your video has been generated successfully',
        'path': gcs_uri.replace('gs://', 'https://storage.googleapis.com/'),
    })
  except video_generation_errors.NoImagesFoundError:
    return flask.jsonify(
        {'status': 'Not enough suitable images found in article'}
    )
  except Exception:  # pylint: disable=broad-exception-caught
    return flask.jsonify({'status': 'Unknown error generating your video.'})
