**AIR-DRF-RELATION**

# Table of Contents

1. [Instalation](#instalation)
2. [About](#about)
3. [RelatedField](#relatedfield)
    1. [pk_only](#pk_only)
    2. [hidden](#hidden)
4. [AirModelSerializer](#airmodelserializer)
    1. [user](#coming) - docs coming soon
    2. [extra_kwargs](#coming) - docs coming soon
    3. [action_read_only_fields](#coming) - docs coming soon
    4. [action_hidden_fields](#coming) - docs ccming soon
    5. [action_extra_kwargs](#coming) - docs coming soon
    6. [queryset_related_field](#coming) - docs coming soon
    7. [nested_save_fields_fields](#coming) - docs coming soon

# Instalation

`$ pip install air-drf-relation`

# About

Add folder **models** in src. Add a file to the directory that will contain the model, for example **user**.

# RelatedField

Used to extend the functionality of the `PrimaryKeyRelatedField`

```python
class BookSerializer(ModelSerializer):
    # author = PrimaryKeyRelatedField(queryset=Author.objects) - default usage
    author = RelatedField(AuthorSerializer)
    city = RelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
```

`RelatedField` allows you to get not only pk but also an object with pk, which will be searched.
```json
{
    "name": "demo",
    "author": { 
        "id": 1
    },
    "city": 1
}
```
#### pk_only
Automatically RelatedField returns a serialized object. If you only want to use pk, you must specify the `pk_only` key.

```python
author = RelatedField(AuthorSerializer, pk_only=True)
```

#### hidden
Hidden fields are not used for serialization and validation. The data will be returned without fields. Usually used together in `AirModelSerializer`

```python
author = RelatedField(AuthorSerializer, hidden=True)
```

### extra_kwargs
You cannot use `hidden` and `pk_only` in ModelSerializer and with extra_kwargs

# AirModelSerializer

Used to extend the functionality of the `ModelSerializer`

```python
class BookSerializer(AirModelSerializer): # full example
    author = RelatedField(AuthorSerializer)
    city = RelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
        hidden_fields = () # list of hidden fields
        read_only_fields = () # default read_only_fields
        extra_kwargs = {} # default extra_kwargs with support custom keys
        action_read_only_fields = { # set read_only_fields by action
            'create': {},
            '_': {} # used for other actions
        },
        action_hidden_fields = { # set hidden_fields by action
            'create': (),
            '_': () # used for other actions
        }
        action_extra_kwargs = { # set extra_kwargs by action
            'list': {},
            '_': {} # used for other actions
        }
        nested_save_fields = () # used for save nested objects
        
```
