import re
from typing import Any, List

from django_filters import ModelMultipleChoiceFilter
from django_filters.fields import ModelMultipleChoiceField


class AirModelMultipleChoiceField(ModelMultipleChoiceField):
    """
    Enhanced ModelMultipleChoiceField that supports comma-separated values in strings.
    Automatically splits comma-separated strings into individual values and removes duplicates.
    """

    def _check_values(self, value: List[Any]) -> List[Any]:
        """
        Process and validate the input values.

        Splits comma-separated strings into individual values and removes duplicates.

        Args:
            value: List of values to process

        Returns:
            List of processed and validated values
        """
        formatted_values = self._parse_comma_separated_values(value)
        unique_values = self._remove_duplicates_and_empty(formatted_values)

        return super()._check_values(unique_values)

    def _parse_comma_separated_values(self, value: List[Any]) -> List[Any]:
        """
        Parse comma-separated strings in the value list.

        Args:
            value: List of values that may contain comma-separated strings

        Returns:
            List with comma-separated strings split into individual values
        """
        formatted_values = []

        for item in value:
            if isinstance(item, str) and ',' in item:
                # Split by comma and strip whitespace
                split_values = re.split(r'\s*,\s*', item)
                formatted_values.extend(split_values)
            else:
                formatted_values.append(item)

        return formatted_values

    def _remove_duplicates_and_empty(self, values: List[Any]) -> List[Any]:
        """
        Remove duplicates and empty values from the list while preserving order.

        Args:
            values: List of values to process

        Returns:
            List with duplicates and empty values removed
        """
        seen = set()
        result = []

        for value in values:
            # Convert to string for comparison, but keep original type
            value_str = str(value).strip() if value is not None else ''

            if value_str and value_str not in seen:
                seen.add(value_str)
                # Keep original value type
                result.append(value)

        return result


class AirModelMultipleFilter(ModelMultipleChoiceFilter):
    """
    Enhanced ModelMultipleChoiceFilter that uses AirModelMultipleChoiceField
    for advanced comma-separated value parsing.
    """

    field_class = AirModelMultipleChoiceField
