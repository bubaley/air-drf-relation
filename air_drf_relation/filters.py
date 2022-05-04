from django_filters import ModelMultipleChoiceFilter
from django_filters.fields import ModelMultipleChoiceField
import re


class AirModelMultipleChoiceField(ModelMultipleChoiceField):
    def _check_values(self, value):
        formatted_value = []
        for i, v in enumerate(value):
            if type(v) == str and ',' in v:
                formatted_value += re.split(' *, *', v)
            else:
                formatted_value.append(v)
        value = list(set(v for v in formatted_value if v))

        return super(AirModelMultipleChoiceField, self)._check_values(value)


class AirModelMultipleFilter(ModelMultipleChoiceFilter):
    field_class = AirModelMultipleChoiceField
