from django.conf import settings as dj_settings
from .settings import air_drf_relation_settings
from air_drf_relation.preload_objects_manager import PreloadObjectsManager

if 'air_drf_relation' in dj_settings.INSTALLED_APPS:
    if air_drf_relation_settings.get('USE_PRELOAD'):
        PreloadObjectsManager.enable_search_for_preloaded_objects()
