"""Contains class that will act as config for the video generation process."""

from typing import TypedDict


class VideoGenerationContext:
  """Context object that hold general settings for a video generation process."""

  _LANGUAGE_CODES = {
      'Afrikaans': 'af',
      'Albanian': 'sq',
      'Amharic': 'am',
      'Arabic': 'ar',
      'Armenian': 'hy',
      'Azerbaijani': 'az',
      'Basque': 'eu',
      'Belarusian': 'be',
      'Bengali': 'bn',
      'Bosnian': 'bs',
      'Bulgarian': 'bg',
      'Catalan': 'ca',
      'Cebuano': 'ceb',
      'Chinese (Simplified)': 'zh-CN',
      'Chinese (Traditional)': 'zh-TW',
      'Corsican': 'co',
      'Croatian': 'hr',
      'Czech': 'cs',
      'Danish': 'da',
      'Dutch': 'nl',
      'English (US)': 'en-US',
      'English (UK)': 'en-GB',
      'Esperanto': 'eo',
      'Estonian': 'et',
      'Finnish': 'fi',
      'French': 'fr',
      'Frisian': 'fy',
      'Galician': 'gl',
      'Georgian': 'ka',
      'German': 'de',
      'Greek': 'el',
      'Gujarati': 'gu',
      'Haitian Creole': 'ht',
      'Hausa': 'ha',
      'Hawaiian': 'haw',
      'Hebrew': 'he',
      'Hindi': 'hi',
      'Hmong': 'hmn',
      'Hungarian': 'hu',
      'Icelandic': 'is',
      'Igbo': 'ig',
      'Indonesian': 'id',
      'Irish': 'ga',
      'Italian': 'it',
      'Japanese': 'ja',
      'Javanese': 'jv',
      'Kannada': 'kn',
      'Kazakh': 'kk',
      'Khmer': 'km',
      'Korean': 'ko',
      'Kurdish (Kurmanji)': 'ku',
      'Kyrgyz': 'ky',
      'Lao': 'lo',
      'Latin': 'la',
      'Latvian': 'lv',
      'Lithuanian': 'lt',
      'Luxembourgish': 'lb',
      'Macedonian': 'mk',
      'Malagasy': 'mg',
      'Malay': 'ms',
      'Malayalam': 'ml',
      'Maltese': 'mt',
      'Maori': 'mi',
      'Marathi': 'mr',
      'Mongolian': 'mn',
      'Myanmar (Burmese)': 'my',
      'Nepali': 'ne',
      'Norwegian': 'no',
      'Nyanja (Chichewa)': 'ny',
      'Odia (Oriya)': 'or',
      'Pashto': 'ps',
      'Persian': 'fa',
      'Polish': 'pl',
      'Portuguese (Brazil)': 'pt-BR',
      'Portuguese (Portugal)': 'pt-PT',
      'Punjabi': 'pa',
      'Romanian': 'ro',
      'Russian': 'ru',
      'Samoan': 'sm',
      'Scots Gaelic': 'gd',
      'Serbian': 'sr',
      'Sesotho': 'st',
      'Shona': 'sn',
      'Sindhi': 'sd',
      'Sinhala': 'si',
      'Slovak': 'sk',
      'Slovenian': 'sl',
      'Somali': 'so',
      'Spanish': 'es',
      'Sundanese': 'su',
      'Swahili': 'sw',
      'Swedish': 'sv',
      'Tagalog (Filipino)': 'tl',
      'Tajik': 'tg',
      'Tamil': 'ta',
      'Tatar': 'tt',
      'Telugu': 'te',
      'Thai': 'th',
      'Turkish': 'tr',
      'Turkmen': 'tk',
      'Ukrainian': 'uk',
      'Urdu': 'ur',
      'Uyghur': 'ug',
      'Uzbek': 'uz',
      'Vietnamese': 'vi',
      'Welsh': 'cy',
      'Xhosa': 'xh',
      'Yiddish': 'yi',
      'Yoruba': 'yo',
      'Zulu': 'zu',
  }

  class Config(TypedDict):
    gcp_project: str
    gcp_location: str
    gcs_bucket_name: str
    gcs_bucket_text_path: str
    gcs_bucket_image_path: str
    output_path: str

  def __init__(
      self,
      config: Config,
      request_params: dict[str, str],
      video_id: str,
  ):
    """Creates a context object by combining values from the config file, video generation request and generated video UUID.

    Args:
        config: Static configuration values provided from the config file.
        request_params: Specific settings for the current video to be generated.
        video_id: Generated video id, to be used as folder and file names.
    """
    self.gcp_project = config['gcp_project']
    self.gcp_location = config['gcp_location']
    self.gcs_bucket_name = config['gcs_bucket_name']
    self.gcs_bucket_text_path = config['gcs_bucket_text_path']
    self.gcs_bucket_image_path = config['gcs_bucket_image_path']
    self.workdir = f"{config['output_path']}/{video_id}"
    self.video_id = video_id
    self.ken_burns = request_params.get('ken_burns', False)
    self.burned_in_subtitles = request_params.get('burned_in_subtitles', False)
    self.language = self._LANGUAGE_CODES.get(
        request_params.get('language_of_article'), 'en-US'
    )
    self.sentiment = request_params.get('sentiment', False)
    self.video_overlay = request_params.get('video_overlay', False)
    self.title = request_params.get('title', False)
    self.article_content = request_params.get('article_content', False)
    self.multivoice = request_params.get('multivoice', False)
