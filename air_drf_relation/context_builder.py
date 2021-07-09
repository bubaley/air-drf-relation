from django.http import HttpRequest
from django.utils.functional import cached_property

from .settings import air_drf_relation_settings


class AirEmptyRequest(HttpRequest):
    @cached_property
    def _current_scheme_host(self):
        return '{}://{}'.format(self.scheme, self.get_host())

    def get_host(self):
        return self._get_raw_host()

    def _get_raw_host(self):
        if 'HTTP_HOST' not in air_drf_relation_settings:
            raise AttributeError('HTTP_HOST is required for ContextBuilder.')
        return air_drf_relation_settings.get('HTTP_HOST')

    def _get_scheme(self):
        use_ssl = air_drf_relation_settings.get('USE_SSL', False)
        return 'https' if use_ssl else 'http'


def set_empty_request_in_kwargs(kwargs):
    try:
        kwargs['context'] = {'request': AirEmptyRequest()}
    except AttributeError as e:
        pass
