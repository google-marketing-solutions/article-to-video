import unittest
from pipeline.video_generation_context import VideoGenerationContext


class VideoGenerationContextTest(unittest.TestCase):

  CONFIG = {
      'gcp_project': 'my_gcp_project',
      'gcp_location': 'us_west',
      'gcs_bucket_name': 'my_bucket_name',
      'gcs_bucket_text_path': 'my_gcs_bucket_text_path',
      'gcs_bucket_image_path': 'my_gcs_bucket_image_path',
      'output_path': '/my/output',
  }

  def test_loading_from_config(self):
    context = VideoGenerationContext.from_request(
        self.CONFIG,
        {'article_content': 'my article', 'image_paths': []},
        '0218e40f-d722-4391-8ef7-47bbdaa29200',
    )

    self.assertEqual(context.gcp_project, 'my_gcp_project')
    self.assertEqual(context.gcp_location, 'us_west')
    self.assertEqual(context.gcs_bucket_name, 'my_bucket_name')
    self.assertEqual(context.gcs_bucket_text_path, 'my_gcs_bucket_text_path')
    self.assertEqual(context.gcs_bucket_image_path, 'my_gcs_bucket_image_path')
    self.assertEqual(
        context.workdir, '/my/output/0218e40f-d722-4391-8ef7-47bbdaa29200'
    )

  def test_loading_request_params_defaults(self):
    context = VideoGenerationContext.from_request(
        self.CONFIG,
        {'article_content': 'my article', 'image_paths': []},
        '0218e40f-d722-4391-8ef7-47bbdaa29200',
    )

    self.assertEqual(context.language, 'en-US')
    self.assertEqual(context.burn_in_subtitles, True)
    self.assertEqual(context.disable_text_overlays, False)
    self.assertEqual(context.multitext, False)
    self.assertEqual(context.multivoice, True)

  def test_loading_request_params(self):
    request_params = {
        'article_content': 'my article',
        'image_paths': [],
        'language': 'pt-BR',
        'burn_in_subtitles': False,
        'disable_text_overlays': True,
        'multitext': True,
        'multivoice': False,
    }
    context = VideoGenerationContext.from_request(
        self.CONFIG, request_params, '0218e40f-d722-4391-8ef7-47bbdaa29200'
    )

    self.assertEqual(context.language, 'pt-BR')
    self.assertEqual(context.burn_in_subtitles, False)
    self.assertEqual(context.disable_text_overlays, True)
    self.assertEqual(context.multitext, True)
    self.assertEqual(context.multivoice, False)
