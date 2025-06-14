# Air DRF Relation

[![PyPI version](https://badge.fury.io/py/air-drf-relation.svg)](https://badge.fury.io/py/air-drf-relation)
[![Python Support](https://img.shields.io/pypi/pyversions/air-drf-relation.svg)](https://pypi.org/project/air-drf-relation/)
[![Django Support](https://img.shields.io/badge/django-4.2%2B-blue.svg)](https://pypi.org/project/air-drf-relation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Advanced Django REST Framework enhancement that automatically optimizes your API performance and eliminates the N+1 queries problem with minimal code changes.**

Transform your DRF APIs into lightning-fast endpoints by default. Air DRF Relation reduces database load by up to **90%** and provides intelligent relation handling that just works.

---

## 📋 Table of Contents

### 🔥 Core Features

1. **[AirModelSerializer N+1 Queries Optimization](#1-airmodelserializer-n1-queries-optimization)** - Automatic select_related/prefetch_related optimization based on serializer structure
2. **[AirModelSerializer Intelligent Batch Preloading](#2-airmodelserializer-intelligent-batch-preloading)** - Smart batch loading during validation to eliminate duplicate queries
3. **[AirRelatedField](#3-airrelatedfield)** - Advanced relation field combining PrimaryKeyRelatedField flexibility with full serialized output
4. **[AirModelSerializer Extra kwargs](#4-airmodelserializer-extra-kwargs)** - Action-based field configuration and dynamic behavior control
5. **[Custom Serializers](#5-custom-serializers)** - AirSerializer, AirDataclassSerializer, AirDynamicSerializer for specialized use cases

### Additional Topics

- [📦 Installation](#-installation)
- [🚀 Quick Start](#-quick-start)
- [⚡ Performance Benefits](#-performance-benefits)
- [🛠️ Development](#️-development)
- [📋 Requirements](#-requirements)
- [🤝 Contributing](#-contributing)

---

## 1. AirModelSerializer N+1 Queries Optimization

### Overview

The most common performance killer in Django REST Framework is the N+1 queries problem. AirModelSerializer automatically analyzes your serializer structure and applies optimal `select_related` and `prefetch_related` optimizations without any manual configuration.

### Problem Solution

```python
# ❌ Standard DRF - N+1 queries nightmare
class BookSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects)
    publisher = serializers.PrimaryKeyRelatedField(queryset=Publisher.objects)

    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'publisher')

# Fetching 1000 books results in:
# 1 query for books + 1000 queries for authors + 1000 queries for publishers = 2001 queries!
books = Book.objects.all()
serializer = BookSerializer(books, many=True)
```

```python
# ✅ Air DRF Relation - Automatic optimization
class BookSerializer(AirModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects)
    publisher = serializers.PrimaryKeyRelatedField(queryset=Publisher.objects)

    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'publisher')

# Same 1000 books now result in just 3 queries!
# 1 query for books with select_related for author and publisher
books = Book.objects.all()
serializer = BookSerializer(books, many=True)
```

### How It Works

AirModelSerializer automatically detects:

- **ForeignKey relationships** → applies `select_related()`
- **ManyToMany and reverse ForeignKey relationships** → applies `prefetch_related()`
- **Nested serializers** → recursively optimizes related querysets
- **Automatic Integration**: Works seamlessly with Django REST Framework ViewSets during representation

### Advanced Usage

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)
    categories = AirRelatedField(CategorySerializer, many=True)
    reviews = AirRelatedField(ReviewSerializer, many=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'categories', 'reviews']

# Automatically generates optimized queryset:
# Book.objects.select_related('author').prefetch_related('categories', 'reviews__user')
```

### Manual Control

```python
class BookSerializer(AirModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author']
        optimize_queryset = False  # Disable automatic optimization
```

---

## 2. AirModelSerializer Intelligent Batch Preloading

### Overview

During validation of bulk data (e.g., creating multiple objects), Air DRF Relation intelligently preloads all related objects in batches, eliminating thousands of individual database queries.

### Problem Solution

```python
# ❌ Without batch preloading - Validation nightmare
from air_drf_relation import PreloadObjectsManager

# Creating 300 tables with 5 legs each = 1500 leg objects
data = [
    {
        'name': f'Table {i}',
        'material': material_id,
        'color': color_id,
        'legs': [
            {'color': leg_color_id, 'name': f'Leg {j}', 'code': j}
            for j in range(5)
        ],
    }
    for i in range(300)
]

PreloadObjectsManager.disable_search_for_preloaded_objects()
serializer = TableSerializer(data=data, many=True)
serializer.is_valid(raise_exception=True)
# Result: 2000+ database queries during validation!
```

```python
# ✅ With intelligent batch preloading
PreloadObjectsManager.enable_search_for_preloaded_objects()  # Default behavior
serializer = TableSerializer(data=data, many=True)
serializer.is_valid(raise_exception=True)
# Result: Just 2 database queries during validation!
```

### How Batch Preloading Works

- **Analysis Phase**: Collects all foreign key values from input data
- **Batch Loading**: Loads all related objects in single queries
- **Smart Caching**: Reuses loaded objects during validation
- **Automatic Integration**: Works seamlessly with Django REST Framework ViewSets during validation

### Configuration

```python
# settings.py
AIR_DRF_RELATION = {
    'USE_PRELOAD': True,  # Enable preloading (default: True)
}

# Per-serializer control
serializer = TableSerializer(data=data, preload_objects=False)
```

### Performance Impact

- **Before**: O(n×m) queries where n=objects, m=relations per object
- **After**: O(r) queries where r=unique relation types

---

## 3. AirRelatedField

### Overview

AirRelatedField is the swiss-army knife of relation fields. It combines the flexibility of `PrimaryKeyRelatedField` with the power of full serialized output, while providing multiple display modes and intelligent optimization.

### Basic Usage

```python
class AuthorSerializer(AirModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'bio']

class BookSerializer(AirModelSerializer):
    # Returns full serialized author object
    author = AirRelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn']

# Input:
{
    "title": "Django Guide",
    "author": 1,  # Just the author ID or {"id": 1}
    "isbn": "978-1234567890"
}

# Output (full serialized object):
{
    "id": 1,
    "title": "Django Guide",
    "author": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "bio": "Expert developer"
    },
    "isbn": "978-1234567890"
}
```

### Modes

#### 1. Primary Key + Full Serialized Output (Default)

```python
AirRelatedField(AuthorSerializer)
# Returns: {"author": {"id": 1, "name": "John", "email": "john@example.com"}}
```

#### 2. Primary Key Only Mode

```python
AirRelatedField(AuthorSerializer, pk_only=True)
# Returns: {"author": 1}
```

#### 3. Hidden Field Mode

```python
AirRelatedField(AuthorSerializer, hidden=True)
# Field fully excluded: ignored for both input and output
```

#### 4. REST Framework Functionality

```python
AirRelatedField(AuthorSerializer, as_serializer=True)
# Disables AirRelatedField functionality. Behaves like a nested serializer
```

### Advanced Features

---

## 4. AirModelSerializer Extra kwargs

### Overview

AirModelSerializer extends Django REST Framework's `extra_kwargs` with action-based configuration, allowing different field behavior for different ViewSet actions and custom queryset filtering.

### Full Configuration Example

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)
    city = AirRelatedField(CitySerializer, queryset_function_name='filter_city_by_user')

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city', 'created_at')
        extra_kwargs = {}  # default extra_kwargs with support custom keys

        hidden_fields = ()
        read_only_fields = ('created_at',)  # default read_only_fields

        action_read_only_fields = {
            'create': ('uuid',),
            '_': ()  # used for other actions
        }
        action_hidden_fields = {
            'create': (),
            '_': () # used for other actions
        }
        action_extra_kwargs = {
            'custom_action': {'author': {'pk_only': True}},
            '_': {'name': {'read_only': True}} # used for other actions
        }

    def queryset_author(self, queryset):
        """Custom filtering for author field - works for any field type"""
        if self.user and not self.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset

    def filter_city_by_user(self, queryset):
        """Custom filtering for city field"""
        if self.user:
            return queryset.filter(country=self.user.country)
        return queryset
```

### Custom Queryset Filtering

```python
class BookSerializer(AirModelSerializer):
    # Works with AirRelatedField
    author = AirRelatedField(AuthorSerializer)

    # Also works with standard DRF fields!
    publisher = serializers.PrimaryKeyRelatedField(queryset=Publisher.objects.all())

    def queryset_author(self, queryset):
        """Filter authors based on user permissions"""
        if self.user and self.user.is_staff:
            return queryset.all()
        return queryset.filter(is_active=True, verified=True)

    def queryset_publisher(self, queryset):
        """Filter publishers - works even with PrimaryKeyRelatedField"""
        return queryset.filter(is_active=True)
```

### Runtime Configuration with User Context

```python
# Pass user context and dynamic configuration
serializer = BookSerializer(
    data=data,
    user=request.user,  # User context for queryset filtering
    action='create',    # Action context
    extra_kwargs={
        'author': {'pk_only': True},
        'city': {'hidden': True}
    } # have priority over static configuration in Meta
)
```

---

## 5. Custom Serializers

### Overview

Air DRF Relation provides specialized serializers for different use cases beyond standard Django models.

### AirSerializer

Base serializer with Air DRF Relation enhancements:

```python

class CustomDataSerializer(AirSerializer):
    name = fields.CharField()
    age = fields.IntegerField()
    city = AirRelatedField(CitySerializer)

    def validate_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Age cannot be negative")
        return value
```

### AirDataclassSerializer

Support Python dataclasses by `rest_framework_dataclasses`:

```python
@dataclass
class UserProfile:
    name: str
    age: int
    email: str
    is_active: bool = True

class UserProfileSerializer(AirDataclassSerializer):
    class Meta:
        dataclass = UserProfile

# Usage
data = {'name': 'John', 'age': 30, 'email': 'john@example.com'}
serializer = UserProfileSerializer(data=data)
if serializer.is_valid():
    profile = serializer.save()  # Returns UserProfile dataclass instance
```

### AirDynamicSerializer

Create serializers with runtime field configuration:

```python
from air_drf_relation import AirDynamicSerializer
from rest_framework import fields

# Define fields dynamically
dynamic_fields = {
    'name': fields.CharField(max_length=100),
    'age': fields.IntegerField(min_value=0),
    'email': fields.EmailField(),
    'tags': fields.ListField(child=fields.CharField()),
}

# Create serializer with dynamic fields
serializer = AirDynamicSerializer(
    data=request.data,
    values=dynamic_fields
)

if serializer.is_valid():
    validated_data = serializer.validated_data
```

#### Dynamic Relations

```python
dynamic_fields = {
    'name': fields.CharField(),
    'author': AirRelatedField(AuthorSerializer),
    'categories': AirRelatedField(CategorySerializer, many=True, pk_only=True),
}

serializer = AirDynamicSerializer(
    data=data,
    values=dynamic_fields,
    action='create'  # Action-based configuration still works
)
```

---

## 📦 Installation

```bash
pip install air-drf-relation
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ... your apps
    'air_drf_relation',
]

# Optional configuration
AIR_DRF_RELATION = {
    'USE_PRELOAD': True,  # Enable automatic preloading (default: True)
}
```

---

## 🚀 Quick Start

### 1. Replace Standard Serializers

```python
# Before
from rest_framework import serializers

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author']

# After
from air_drf_relation.serializers import AirModelSerializer

class BookSerializer(AirModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author']
```

### 2. Use AirRelatedField for Relations

```python
from air_drf_relation.serializers import AirModelSerializer
from air_drf_relation.fields import AirRelatedField

class AuthorSerializer(AirModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email']

class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author']
```

---

## ⚡ Performance Benefits

### Query Reduction

- **Standard DRF**: O(n) queries for n related objects
- **Air DRF Relation**: O(1) queries regardless of object count
- **Real-world impact**: 70-90% query reduction in typical scenarios

---

## 🛠️ Development

Set up development environment:

```bash
# Clone repository
git clone git@github.com:bubaley/air-drf-relation.git
cd air-drf-relation

# Create virtual environment with Python 3.13
uv venv --python 3.13

# Install dependencies
uv sync

# Run tests
python manage.py test

# Run pre-commit checks
pre-commit run --all-files
```

---

## 📋 Requirements

- **Python**: 3.9+
- **Django**: 4.2+
- **Django REST Framework**: 3.14+
- **Python Libraries**: See [pyproject.toml](pyproject.toml) for complete list

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with appropriate tests
4. Run the linting checks (`ruff check . && ruff format .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please ensure your code follows our style guidelines and includes appropriate tests.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **PyPI**: [https://pypi.org/project/air-drf-relation/](https://pypi.org/project/air-drf-relation/)
- **Source Code**: [https://github.com/bubaley/air-drf-relation](https://github.com/bubaley/air-drf-relation)
- **Bug Reports**: [https://github.com/bubaley/air-drf-relation/issues](https://github.com/bubaley/air-drf-relation/issues)

---

## 💫 Support

If you find this package useful, please consider:

- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 📖 Improving documentation
- 🤝 Contributing code

---

**Built with ❤️ for the Django REST Framework community**
