from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from rest_framework.request import Request
from .settings import air_drf_relation_settings


class ContextBuilder:
    def __init__(self, user: None):
        self.user = user if user else AnonymousUser

    def build(self):
        if 'HTTP_HOST' not in air_drf_relation_settings:
            raise AttributeError('HTTP_HOST is required for ContextBuilder.')

        http_request = HttpRequest()
        http_request.META['HTTP_HOST'] = air_drf_relation_settings.get('HTTP_HOST')
        http_request._get_scheme = _get_scheme
        context = {
            'user': self.user,
            'request': Request(request=http_request),
            'view': None
        }
        return context


def _get_scheme():
    use_ssl = air_drf_relation_settings.get('USE_SSL', False)
    return 'https' if use_ssl else 'http'
