**AIR-DRF-RELATION**

# Table of Contents

1. [Instalation](#instalation)
2. [About](#about)
3. [AirRelatedField](#airrelatedfield)
    1. [pk_only](#pk_only)
    2. [hidden](#hidden)
4. [AirModelSerializer](#airmodelserializer)
    1. [user](#user)
    2. [extra_kwargs](#extra_kwargs)
    3. [hidden_fields](#hidden_fields)
    4. [Kwargs by actions](#kwargs-by-actions)
        1. [action_read_only_fields](#action_read_only_fields)
        2. [action_hidden_fields](#action_hidden_fields)
        3. [action_extra_kwargs](#action_extra_kwargs)
    4. [Priority extra_kwargs](#priority-extra_kwargs)
    5. [Filter nested querysets](#filter-nested-querysets)

# Instalation

`$ pip install air-drf-relation`

# About

`air-drf-relation` adds flexibility and convenience in working with ModelSerializer.

# AirRelatedField

Used to extend the functionality of the `PrimaryKeyRelatedField`

```python
class BookSerializer(ModelSerializer):
    # author = PrimaryKeyRelatedField(queryset=Author.objects) - default usage
    author = AirRelatedField(AuthorSerializer)
    city = AirRelatedField(CitySerializer)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
```

`AirRelatedField` allows you to get not only pk but also an object with pk, which will be searched.
```json
{
    "name": "demo",
    "author": { 
        "id": 1
    },
    "city": 1
}
```
## pk_only
Automatically AirRelatedField returns a serialized object. If you only want to use pk, you must specify the `pk_only` key.

```python
author = AirRelatedField(AuthorSerializer, pk_only=True)
```

## hidden
Hidden fields are not used for serialization and validation. The data will be returned without fields. Usually used together in `AirModelSerializer`

```python
author = AirRelatedField(AuthorSerializer, hidden=True)
```

## Important
You cannot use `hidden` and `pk_only` in ModelSerializer and with extra_kwargs

# AirModelSerializer

Used to extend the functionality of the `ModelSerializer`

```python
class BookSerializer(AirModelSerializer): # full example
    author = AirRelatedField(AuthorSerializer)
    city = AirRelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
        hidden_fields = ()
        read_only_fields = () # default read_only_fields
        extra_kwargs = {} # default extra_kwargs with support custom keys
        action_read_only_fields = {
            'create': {},
            '_': {} # used for other actions
        },
        action_hidden_fields = {
            'create': (),
            '_': ()
        }
        action_extra_kwargs = {
            'list': {},
            '_': {}
        }
        nested_save_fields = ()
```

## user
User is automatically put from the `request` if available. You can also set the user manually.

```python
class DemoSerializer(AirModelSerializer):
    class Meta:
        fields = ('id', 'name')
    
    validate_name(self, value):
        if not self.user:
            return None
        return value
```
Manually set user.
```python
serializer = DemoSerializer(data={'name': 'demo'}, user=request.user)
```

## extra_kwargs
Extends the standard work with `extra_kwargs` by adding work with additional attributes. You can also transfer `extra_kwargs` manually.

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)
    
    class Meta:
        fields = ('id', 'name', 'author')
        extra_kwargs = {
            'author': {'pk_only': True},
            'name': {'hidden': True}
        }
```
## hidden_fields
Hides fields for validation and seralization.
```python
class BookSerializer(AirModelSerializer):
    class Meta:
        fields = ('id', 'name', 'author')
        hidden_fields = ('name', 'author')
```
## Kwargs by actions
Kwargs by actions is used only when the event. You can pass acions separated by `,`.
For events that don't match, you can use `_` key. It is used if action **is passed**.
Action is set automatically from the ViewSet, or it can be passed manually.

```python
class DemoViewSet(ModelViewSet):
    queryset = Demo.objects.all()
    serializer_class = DemoSerializer
    
    def perform_create(serializer, request):
        action = serializer.action # action is 'create'
        serializer.save()
    
    @action(methods=['POST'], detail=False)
    def demo_action(self, request):
        serializer = self.get_serializer_class()
        action = serializer.action # action is 'demo_action'
```

Manually set action.
```python
serializer = DemoSerializer(data={'name': 'demo'}, action='custom_action')
action = serializer.action # action is 'custom_action'
```

### action_read_only_fields
Sets `read_only_fields` by action in serializer.

```python
class BookSerializer(AirModelSerializer):
    class Meta:
        fields = ('id', 'name', 'author')
        action_read_only_fields = {
            'create,update': ('name', 'author')
        }
```

### action_hidden_fields
Sets `hidden_fields` by action in serializer.

```python
class BookSerializer(AirModelSerializer):
    class Meta:
        fields = ('id', 'name', 'author')
        action_hidden_fields = {
            'custom_action': ('author', ),
            '_': ('id', )
        }
```

### action_extra_kwargs
Expand `extra_kwargs` by action in serializer.

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer, pk_only=True, null=True)
    
    class Meta:
        fields = ('id', 'name', 'author')
        action_extra_kwargs = {
            'create,custom_update': {
                'author': {'pk_only': False, 'null'=True}
            }
        }
```

## Priority extra_kwargs
Below are the priorities of the extra_kwargs extension in ascending order
1. extra_kwargs `in Meta`
2. hidden_fields
3. action_hidden_fields
4. action_read_only_fields
5. action_extra_kwargs
6. extra_kwargs `manually transmitted`

## Filter nested querysets
AirModelSerializer allows you to filter the queryset by nested fields.
```python
class BookSerializer(AirModelSerializer):
    city = AirRelatedField(CitySerializer, queryset_function_name='custom_filter')

    def queryset_author(self, queryset):
        return queryset.filter(active=True, created_by=self.user)

    def filter_city_by_active(self, queryset):
        return queryset.filter(active=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
```
