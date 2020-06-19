# DRF Improved Relations

## What does it do?

This package allows you to set relation from API request by primary key, object's dict, list of PKs, list of dicts of mixed list.

*For example*

```json5
{
	"name": "Quentin Tarantino",
	"person_type": {"id": 10, "name": "Director"},  // dict (field ID is only required)
	"city": 15,  // primary key
	"movies": [  // list
		15431,  // can be primary key
		{"id": 31123},  // can be dict
		{"id": 21100, "name": "Pulp Fiction"}
	]
}
```

## How to use it?

### RelatedField

`RelatedField` is class implemented of `PrimaryKeyRelatedField`.

It has:
- `serializer` *Serializer class used for serializing objects (list, retrieve...)*
- `fail_on_not_found` *Raise NotFound exception if object not found*
- `extra_filter` *Extra fields added to `.filter()`*

```python
class PersonSerializer(ModelSerializer):
	person_type = RelatedField(serializer=TypeSerializer)
	city = RelatedField(serializer=CitySerializer, required=False, fail_on_null=False, fail_on_not_found=False, 						extra_filter={'country': Country.objects.filter(name='USA')})
	movies = RelatedField(serializer=MovieSerilizer, many=True)

	class Meta(object):
		model = Person
		fields = ('id', 'name', 'person_type', 'city', 'movies')
```

### get_related_object

```python
get_related_object(search, model, fail_on_null=True, create_on_null=False, fail_on_not_found=True, extra_filter=None)
```

This function searches `model` instance by `search` (which would be primary key, dict with "id" field or list).

Attributes:

- `search` *Primary key, dict with "id" field or list of primary keys*
- `model` *Model to search in*
- `fail_on_null` *Raise ValidationError if search is None or incorrect
- `fail_on_not_found` *Raise ValidationError if an instance was now found (does not work with list)*
- `create_on_null` *Try to create a new object*
- `extra_filter` *Extra fields added to `.filter()`*

### get_relation_from_request

```python
get_relation_from_request(request, key: str, data: dict, model, fail_on_empty=False, fail_on_null=True,
                              fail_on_not_found=True, create_on_null=False, types=None, extra_filter=None)
```

This function gets value from `request`, search instance by `get_related_object()` and put it to `data`.

Attributes:

- `request` *HttpRequest*
- `key` *Key to get value from request data*
- `data` *Dict to put gotten instance in*
- `model` *Model to search in*
- `fail_on_empty` *Raise ValidationError if there is no `key` in `request`*
- `fail_on_null` *Raise ValidationError if search is None or incorrect
- `fail_on_not_found` *Raise ValidationError if an instance was now found (does not work with list)*
- `create_on_null` *Try to create a new object*
- `types` *List of allowed value types*
- `extra_filter` *Extra fields added to `.filter()`*

How to use it:

```python
def perform_create(self, serializer):
	data = dict()
	get_relation_from_request(self.request, 'person_type', data, PersonType)
	get_relation_from_request(self.request, 'city', data, City, fail_on_empty=False, 
							  extra_fields={'country': Country.objects.filter(name='USA')})
	get_relation_from_request(self.request, 'movies', data, Movie)
	serializer.save(**data)
```
