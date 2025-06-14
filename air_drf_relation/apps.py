"""Django app configuration for air_drf_relation."""

from django.apps import AppConfig


class AirDrfRelationConfig(AppConfig):
    """Configuration for the air_drf_relation Django app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'air_drf_relation'
    verbose_name = 'Air DRF Relation'

    def ready(self) -> None:
        """
        Perform initialization when Django is ready.
        This method is called when Django has finished loading all apps.
        """
        # Import here to avoid circular imports and ensure Django is ready
        from .preload_objects_manager import PreloadObjectsManager
        from .settings import air_drf_relation_settings

        # Auto-enable preloading if configured
        if air_drf_relation_settings.use_preload:
            PreloadObjectsManager.enable_search_for_preloaded_objects()
