from django.conf import settings

air_drf_relation_settings = settings.AIR_DRF_RELATION if hasattr(settings, 'AIR_DRF_RELATION') else {}
if 'USE_PRELOAD' not in air_drf_relation_settings:
    air_drf_relation_settings['USE_PRELOAD'] = True
