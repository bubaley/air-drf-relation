from django.http import HttpRequest
from django.utils.functional import cached_property

from .settings import air_drf_relation_settings


class AirEmptyRequest(HttpRequest):
    """
    Empty HTTP request implementation for DRF contexts.

    Provides a minimal HTTP request with configurable host and scheme
    based on air_drf_relation_settings.
    """

    @cached_property
    def _current_scheme_host(self):
        """Build complete URL with scheme and host."""
        return f'{self.scheme}://{self.get_host()}'

    @property
    def scheme(self):
        """Get the HTTP scheme (http or https) from settings."""
        return self._get_scheme()

    def get_host(self):
        """Get the HTTP host from settings or default."""
        return self._get_raw_host()

    def _get_raw_host(self):
        """Get raw host value from settings."""
        return air_drf_relation_settings.get('HTTP_HOST', 'localhost:8000')

    def _get_scheme(self):
        """Determine scheme based on USE_SSL setting."""
        use_ssl = air_drf_relation_settings.get('USE_SSL', False)
        return 'https' if use_ssl else 'http'


def set_empty_request_in_kwargs(kwargs):
    """
    Set an empty request instance in kwargs context.

    This function is used to provide a request context when one is not
    available, particularly useful for DRF serializers that need a request
    object for context.

    Args:
        kwargs (dict): Keyword arguments dictionary to modify.

    Returns:
        None: Modifies kwargs in place.
    """
    if not isinstance(kwargs, dict):
        return

    try:
        kwargs['context'] = {'request': AirEmptyRequest()}
    except (TypeError, AttributeError):
        # Silently fail if kwargs cannot be modified
        pass
