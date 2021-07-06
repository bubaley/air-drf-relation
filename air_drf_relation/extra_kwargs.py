from copy import deepcopy

from air_drf_relation.utils import create_dict_from_list


class ExtraKwargsFactory:
    def __init__(self, meta, data: dict, action=None):
        self.Meta = meta
        self.action = action
        self.extra_kwargs = None
        self._initial_data = data

        self.meta_extra_kwargs: dict = {}
        self.hidden_fields: dict = {}
        self.action_hidden_fields: dict = {}
        self.action_read_only_fields: dict = {}
        self.action_extra_kwargs: dict = {}
        self.initial_extra_kwargs: dict = self._initial_data.get('extra_kwargs', {})

    def init(self):
        self._set_meta_extra_kwargs()
        self._set_hidden_fields()
        if self.action:
            self._set_action_hidden_fields()
            self._set_action_read_only_fields()
            self._set_action_extra_kwargs()
        self._set_extra_kwargs()
        return self

    def _set_extra_kwargs(self):
        extra_kwargs_list = self._get_extra_kwargs_list()
        extra_kwargs = dict()
        for el in extra_kwargs_list:
            for field_name, field_value in el.items():
                if field_name in extra_kwargs:
                    extra_kwargs[field_name] = {**extra_kwargs[field_name], **field_value}
                else:
                    extra_kwargs[field_name] = field_value
        self.extra_kwargs = extra_kwargs

    def _set_meta_extra_kwargs(self):
        if hasattr(self.Meta, 'extra_kwargs'):
            self.meta_extra_kwargs = deepcopy(self.Meta.extra_kwargs)

    def _set_hidden_fields(self):
        if hasattr(self.Meta, 'hidden_fields'):
            self.hidden_fields = create_dict_from_list(self.Meta.hidden_fields, {'hidden': True})

    def _set_action_hidden_fields(self):
        if hasattr(self.Meta, 'action_hidden_fields'):
            remain_value = None
            _action_hidden_fields: dict = self.Meta.action_hidden_fields
            for key, value in _action_hidden_fields.items():
                keys = key.replace(' ', '').split(',')
                if self.action in keys:
                    self.action_hidden_fields = create_dict_from_list(value, {'hidden': True})
                    return
                if '_' in keys:
                    remain_value = value
            if remain_value:
                self.action_hidden_fields = create_dict_from_list(remain_value, {'hidden': True})

    def _set_action_read_only_fields(self):
        if hasattr(self.Meta, 'action_read_only_fields'):
            remain_value = None
            _action_read_only_fields: dict = self.Meta.action_read_only_fields
            for key, value in _action_read_only_fields.items():
                keys = key.replace(' ', '').split(',')
                if self.action in keys:
                    self.action_read_only_fields = create_dict_from_list(value, {'read_only': True})
                    return
                if '_' in keys:
                    remain_value = value
            if remain_value:
                self.action_read_only_fields = create_dict_from_list(remain_value, {'read_only': True})

    def _set_action_extra_kwargs(self):
        if hasattr(self.Meta, 'action_extra_kwargs'):
            remain_value = None
            _action_extra_kwargs: dict = self.Meta.action_extra_kwargs
            for key, value in _action_extra_kwargs.items():
                keys = key.replace(' ', '').split(',')
                if self.action in keys:
                    self.action_extra_kwargs = value
                    return
                if '_' in keys:
                    remain_value = value
            if remain_value:
                self.action_extra_kwargs = remain_value

    def _get_extra_kwargs_list(self) -> list[dict]:
        result = list()
        if self.meta_extra_kwargs:
            result.append(self.meta_extra_kwargs)
        if self.hidden_fields:
            result.append(self.hidden_fields)
        if self.action_hidden_fields:
            result.append(self.action_hidden_fields)
        if self.action_read_only_fields:
            result.append(self.action_read_only_fields)
        if self.action_extra_kwargs:
            result.append(self.action_extra_kwargs)
        if self.initial_extra_kwargs:
            result.append(self.initial_extra_kwargs)
        return result
