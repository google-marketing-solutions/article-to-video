import unittest
from pipeline.video_generation_context import VideoGenerationContext
from truth.truth import AssertThat


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
    context = VideoGenerationContext(
        self.CONFIG, {}, '0218e40f-d722-4391-8ef7-47bbdaa29200'
    )

    AssertThat(context.gcp_project).IsEqualTo('my_gcp_project')
    AssertThat(context.gcp_location).IsEqualTo('us_west')
    AssertThat(context.gcs_bucket_name).IsEqualTo('my_bucket_name')
    AssertThat(context.gcs_bucket_text_path).IsEqualTo(
        'my_gcs_bucket_text_path'
    )
    AssertThat(context.gcs_bucket_image_path).IsEqualTo(
        'my_gcs_bucket_image_path'
    )
    AssertThat(context.workdir).IsEqualTo(
        '/my/output/0218e40f-d722-4391-8ef7-47bbdaa29200'
    )

  def test_loading_request_params_defaults(self):
    context = VideoGenerationContext(
        self.CONFIG, {}, '0218e40f-d722-4391-8ef7-47bbdaa29200'
    )

    AssertThat(context.ken_burns).IsFalse()
    AssertThat(context.disable_text_overlays).IsFalse()
    AssertThat(context.burn_in_subtitles).IsFalse()
    AssertThat(context.language).IsEqualTo('en-US')
    AssertThat(context.sentiment).IsFalse()
    AssertThat(context.video_overlay).IsFalse()
    AssertThat(context.title).IsFalse()

  def test_loading_request_params(self):
    request_params = {
        'ken_burns': True,
        'burned_in_subtitles': False,
        'language_of_article': 'Portuguese (Brazil)',
        'sentiment': True,
        'video_overlay': True,
        'title': True,
    }
    context = VideoGenerationContext(
        self.CONFIG, request_params, '0218e40f-d722-4391-8ef7-47bbdaa29200'
    )

    AssertThat(context.ken_burns).IsTrue()
    AssertThat(context.burn_in_subtitles).IsFalse()
    AssertThat(context.language).IsEqualTo('pt-BR')
    AssertThat(context.sentiment).IsTrue()
    AssertThat(context.video_overlay).IsTrue()
    AssertThat(context.title).IsTrue()
