from copy import deepcopy
from typing import Any, Dict, List, Optional

from air_drf_relation.utils import create_dict_from_list


class ExtraKwargsFactory:
    """Factory for creating extra_kwargs for DRF serializers based on Meta class configuration."""

    def __init__(self, meta: Any, data: Dict[str, Any], action: Optional[str] = None):
        self.Meta = meta
        self.action = action
        self.extra_kwargs: Optional[Dict[str, Any]] = None
        self._initial_data = data

        self.meta_extra_kwargs: Dict[str, Any] = {}
        self.hidden_fields: Dict[str, Any] = {}
        self.action_hidden_fields: Dict[str, Any] = {}
        self.action_read_only_fields: Dict[str, Any] = {}
        self.action_extra_kwargs: Dict[str, Any] = {}
        self.initial_extra_kwargs: Dict[str, Any] = self._initial_data.get('extra_kwargs', {})

    def init(self) -> 'ExtraKwargsFactory':
        """Initialize all extra_kwargs configurations and return self."""
        self._set_meta_extra_kwargs()
        self._set_hidden_fields()

        if self.action:
            self._set_action_based_configurations()

        self._merge_extra_kwargs()
        return self

    def _set_meta_extra_kwargs(self) -> None:
        """Set extra_kwargs from Meta class."""
        if hasattr(self.Meta, 'extra_kwargs'):
            self.meta_extra_kwargs = deepcopy(self.Meta.extra_kwargs)

    def _set_hidden_fields(self) -> None:
        """Set hidden fields from Meta class."""
        if hasattr(self.Meta, 'hidden_fields'):
            self.hidden_fields = create_dict_from_list(self.Meta.hidden_fields, {'hidden': True})

    def _set_action_based_configurations(self) -> None:
        """Set all action-based configurations."""
        self._set_action_based_field_config('action_hidden_fields', {'hidden': True}, 'action_hidden_fields')
        self._set_action_based_field_config('action_read_only_fields', {'read_only': True}, 'action_read_only_fields')
        self._set_action_based_field_config('action_extra_kwargs', None, 'action_extra_kwargs')

    def _set_action_based_field_config(
        self, attr_name: str, field_config: Optional[Dict[str, Any]], target_attr: str
    ) -> None:
        """
        Generic method to set action-based field configurations.

        Args:
            attr_name: Name of the Meta attribute to check
            field_config: Configuration to apply to fields (None for direct assignment)
            target_attr: Name of the instance attribute to set
        """
        if not hasattr(self.Meta, attr_name):
            return

        config_dict = getattr(self.Meta, attr_name)
        action_config = self._find_action_config(config_dict)

        if action_config is not None:
            if field_config is None:
                # Direct assignment for action_extra_kwargs
                setattr(self, target_attr, action_config)
            else:
                # Create dict from list for field configurations
                setattr(self, target_attr, create_dict_from_list(action_config, field_config))

    def _find_action_config(self, config_dict: Dict[str, Any]) -> Optional[Any]:
        """
        Find configuration for the current action in the config dictionary.

        Args:
            config_dict: Dictionary with action keys and their configurations

        Returns:
            Configuration value for the current action or default ('_') configuration
        """
        default_config = None

        for key, value in config_dict.items():
            actions = [action.strip() for action in key.split(',')]

            if self.action in actions:
                return value

            if '_' in actions:
                default_config = value

        return default_config

    def _merge_extra_kwargs(self) -> None:
        """Merge all extra_kwargs configurations into a single dictionary."""
        configurations = self._get_configuration_list()
        merged_kwargs = {}

        for config in configurations:
            for field_name, field_config in config.items():
                if field_name in merged_kwargs:
                    merged_kwargs[field_name] = {**merged_kwargs[field_name], **field_config}
                else:
                    merged_kwargs[field_name] = field_config

        self.extra_kwargs = merged_kwargs

    def _get_configuration_list(self) -> List[Dict[str, Any]]:
        """Get list of all non-empty configurations in order of priority."""
        configurations = [
            self.meta_extra_kwargs,
            self.hidden_fields,
            self.action_hidden_fields,
            self.action_read_only_fields,
            self.action_extra_kwargs,
            self.initial_extra_kwargs,
        ]

        return [config for config in configurations if config]
