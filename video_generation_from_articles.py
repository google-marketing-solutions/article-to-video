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


def _get_bool_from_request(
    d: dict[str, str], key: str, default: bool | None = None
) -> bool | None:
  """Safely retrieves and converts a value from a dictionary to a boolean.

  This function attempts to get a value associated with the given key from the
  dictionary.
  - If the key is not found, it returns the `default` value.
  - If the value is already a boolean, it's returned directly.
  - If the value is a string, it's converted to a boolean:
    - true values (case-insensitive): 'true', 't', 'yes', 'y', 'on', '1'.
    - false values (case-insensitive): 'false', 'f', 'no', 'n', 'off', '0'.
  - If the value is a string that cannot be converted, or if it's of any other
    type, the `default` value is returned.

  Args:
    d: The dictionary to look up the key in.
    key: The key whose value is to be retrieved and converted.
    default: The default boolean value to return if the key is not found or if
      the value cannot be converted to a boolean. Defaults to None.

  Returns:
    The boolean representation of the value, or the default value.
  """
  if key not in d:
    return default

  val = d[key]
  if isinstance(val, bool):
    return val
  elif isinstance(val, str):
    s_lower = val.lower().strip()
    if s_lower in ('true', 't', 'yes', 'y', 'on', '1'):
      return True
    elif s_lower in ('false', 'f', 'no', 'n', 'off', '0'):
      return False
  else:
    return default


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
  logging.log(logging.INFO, 'Raw request parameters: %s', request_params)

  image_paths = []
  file_storage = flask.request.files.values()
  for file in file_storage:
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension in ALLOWED_EXTENSIONS:
      folder = f'uploads/{video_id}/images'
      os.makedirs(folder, exist_ok=True)
      upload_path = os.path.join(folder, file.filename)
      file.save(upload_path)
      image_paths.append(upload_path)
    else:
      logging.log(
          logging.INFO,
          '%s does not have a supported image extension.',
          file.filename,
      )

  # if no images were includes in the request, check if any were already
  # uploaded with upload_file
  if not image_paths:
    image_paths = glob.glob(f'uploads/{video_id}/images/*')

  if 'article_content' in flask.request.files:
    article_bytes = flask.request.files['article_content'].read()
    article_content = article_bytes.decode('utf-8')
  elif 'article_content' in request_params:
    article_content = request_params['article_content']
  else:
    article_content = None

  if not article_content or not image_paths:
    error_msg = 'Article content or images not found.'
    logging.log(logging.ERROR, 'Error: %s', error_msg)
    return flask.jsonify({'status': error_msg})

  parsed_request_params = {
      'article_content': article_content,
      'image_paths': image_paths,
      'splash_image': request_params.get('splash_image'),
      'multivoice': _get_bool_from_request(request_params, 'multivoice'),
      'disable_text_overlays': _get_bool_from_request(
          request_params, 'disable_text_overlays'
      ),
      'burn_in_subtitles': _get_bool_from_request(
          request_params, 'burn_in_subtitles'
      ),
      'language': request_params.get('language'),
      'multitext': _get_bool_from_request(request_params, 'multitext'),
  }
  logging.log(
      logging.INFO, 'Parsed request parameters: %s', parsed_request_params
  )

  try:
    # In a production-ready solution, the video generation process would
    # typically be handled by a separate, asynchronous worker process or a
    # managed service  keep the main application responsive. For simplicity in
    # this demo, it's handled synchronously.
    context = pipeline.VideoGenerationContext.from_request(
        config, parsed_request_params, video_id
    )
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
