"""
Air DRF Relation - Enhanced Django REST Framework serializers with advanced relation handling.

This package provides enhanced serializers and fields for Django REST Framework
with features like queryset optimization and preloading.
"""

from .fields import AirAnyField, AirDataclassField, AirRelatedField
from .filters import AirModelMultipleChoiceField, AirModelMultipleFilter
from .serializers import (
    AirDataclassSerializer,
    AirDynamicSerializer,
    AirEmptySerializer,
    AirListSerializer,
    AirModelSerializer,
    AirSerializer,
)
from .settings import air_drf_relation_settings

try:
    from .__about__ import __version__
except ImportError:
    __version__ = '0.0.0'

# Django app configuration
default_app_config = 'air_drf_relation.apps.AirDrfRelationConfig'

__all__ = [
    # Core serializers
    'AirSerializer',
    'AirModelSerializer',
    'AirListSerializer',
    'AirEmptySerializer',
    'AirDynamicSerializer',
    'AirDataclassSerializer',
    # Fields
    'AirRelatedField',
    'AirAnyField',
    'AirDataclassField',
    # Filters
    'AirModelMultipleChoiceField',
    'AirModelMultipleFilter',
    # Settings
    'air_drf_relation_settings',
    # Version
    '__version__',
]
