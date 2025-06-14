from typing import Any, Dict

from django.conf import settings


class AirDrfRelationSettings:
    """
    Configuration class for air-drf-relation package settings.
    Manages default settings and provides type-safe access to configuration values.
    """

    DEFAULT_SETTINGS: Dict[str, Any] = {
        'USE_PRELOAD': True,
    }

    def _load_settings(self) -> Dict[str, Any]:
        """
        Load settings from Django configuration with defaults.
        Always reads fresh from Django settings.

        Returns:
            Dictionary containing all air-drf-relation settings
        """
        user_settings = getattr(settings, 'AIR_DRF_RELATION', {})

        if not isinstance(user_settings, dict):
            user_settings = {}

        # Merge defaults with user settings
        merged_settings = {**self.DEFAULT_SETTINGS, **user_settings}
        return merged_settings

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value by key.

        Args:
            key: Setting key to retrieve
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        current_settings = self._load_settings()
        return current_settings.get(key, default)

    @property
    def use_preload(self) -> bool:
        """Whether to use preloading functionality."""
        current_settings = self._load_settings()
        return current_settings.get('USE_PRELOAD', True)


# Global settings instance
air_drf_relation_settings = AirDrfRelationSettings()
