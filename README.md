# Air DRF Relation

[![PyPI version](https://badge.fury.io/py/air-drf-relation.svg)](https://badge.fury.io/py/air-drf-relation)
[![Python Support](https://img.shields.io/pypi/pyversions/air-drf-relation.svg)](https://pypi.org/project/air-drf-relation/)
[![Django Support](https://img.shields.io/badge/django-4.2%2B-blue.svg)](https://pypi.org/project/air-drf-relation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Enhanced Django REST Framework serializers with advanced relation handling and queryset optimization.**

Air DRF Relation provides a comprehensive set of enhanced serializers and fields for Django REST Framework that significantly improve performance and developer experience through advanced features like automatic queryset optimization and intelligent preloading.

## ✨ Features

- 🚀 **Automatic Queryset Optimization** - Intelligent `select_related` and `prefetch_related` based on serializer structure
- ⚡ **Smart Object Preloading** - Eliminate N+1 queries with automatic batch loading
- 🔧 **Enhanced Field Types** - Extended relation fields with advanced configuration options
- 🎯 **Action-Based Configuration** - Different serializer behavior per DRF ViewSet action
- 📊 **Performance Monitoring** - Built-in tools for analyzing serialization performance
- 🎨 **Dynamic Serializers** - Runtime field configuration for flexible APIs

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

## 🚀 Quick Start

### Basic Usage

Replace your regular DRF serializers with Air serializers:

```python
from air_drf_relation import AirModelSerializer, AirRelatedField

class AuthorSerializer(AirModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email']

class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn']
```

### Advanced Relation Handling

```python
class BookSerializer(AirModelSerializer):
    # Return full serialized object
    author = AirRelatedField(AuthorSerializer)

    # Return only primary key
    category = AirRelatedField(CategorySerializer, pk_only=True)

    # Hidden field (not included in output)
    internal_id = AirRelatedField(InternalSerializer, hidden=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category']
```

### Action-Based Configuration

Configure different behavior for different ViewSet actions:

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'created_at', 'updated_at']

        # Different read-only fields per action
        action_read_only_fields = {
            'create': ['created_at', 'updated_at'],
            'update': ['created_at'],
            'list': ['created_at', 'updated_at', 'author'],
        }

        # Hide fields for specific actions
        action_hidden_fields = {
            'list': ['updated_at'],
        }

        # Different extra_kwargs per action
        action_extra_kwargs = {
            'create': {
                'author': {'pk_only': True},
            },
            'list': {
                'author': {'pk_only': False},
            }
        }
```

### Custom Queryset Filtering

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author']

    def queryset_author(self, queryset):
        """Custom queryset filtering for author field"""
        if self.user and not self.user.is_staff:
            # Non-staff users can only see active authors
            return queryset.filter(is_active=True)
        return queryset
```

## 📚 Comprehensive Documentation

### Core Components

#### AirModelSerializer

Enhanced ModelSerializer with advanced features:

```python
class BookSerializer(AirModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author']

        # Automatically optimize querysets
        optimize_queryset = True  # Default: True

        # Hide fields from serialization
        hidden_fields = ['internal_field']

        # Enhanced extra_kwargs with custom options
        extra_kwargs = {
            'author': {
                'pk_only': True,
                'queryset_function_name': 'custom_author_queryset'
            }
        }
```

#### AirRelatedField

Advanced relation field with multiple display modes:

```python
# Basic usage - returns serialized object
author = AirRelatedField(AuthorSerializer)

# Primary key only mode
author = AirRelatedField(AuthorSerializer, pk_only=True)

# Hidden field mode
author = AirRelatedField(AuthorSerializer, hidden=True)

# Custom queryset function
author = AirRelatedField(
    AuthorSerializer,
    queryset_function_name='filter_authors'
)

# Disable queryset filtering
author = AirRelatedField(
    AuthorSerializer,
    queryset_function_disabled=True
)
```

#### Dynamic Serializers

Create serializers with runtime field configuration:

```python
from air_drf_relation import AirDynamicSerializer
from rest_framework import fields

dynamic_fields = {
    'name': fields.CharField(),
    'age': fields.IntegerField(),
    'email': fields.EmailField()
}

serializer = AirDynamicSerializer(
    data=request.data,
    values=dynamic_fields
)
```

#### Dataclass Support

Full support for Python dataclasses:

```python
from dataclasses import dataclass
from air_drf_relation import AirDataclassSerializer

@dataclass
class UserProfile:
    name: str
    age: int
    email: str

class UserProfileSerializer(AirDataclassSerializer):
    class Meta:
        dataclass = UserProfile
```

### Performance Features

#### Automatic Queryset Optimization

Air DRF Relation automatically analyzes your serializer structure and applies appropriate `select_related` and `prefetch_related` optimizations:

```python
class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)
    categories = AirRelatedField(CategorySerializer, many=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'categories']

# Automatically generates:
# Book.objects.select_related('author').prefetch_related('categories')
```

#### Smart Preloading

Eliminate N+1 queries with intelligent batch loading:

```python
# When validating multiple books, related objects are preloaded in batches
serializer = BookSerializer(data=books_data, many=True)
if serializer.is_valid():
    # All authors and categories are loaded in minimal queries
    serializer.save()
```

### Configuration Options

#### Global Settings

```python
# settings.py
AIR_DRF_RELATION = {
    'USE_PRELOAD': True,  # Enable preloading (default: True)
}
```

#### Per-Serializer Settings

```python
class BookSerializer(AirModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title']
        optimize_queryset = False  # Disable optimization for this serializer
```

#### Runtime Configuration

```python
# Disable preloading for specific instance
serializer = BookSerializer(data=data, preload_objects=False)

# Pass custom user context
serializer = BookSerializer(data=data, user=request.user)

# Specify action manually
serializer = BookSerializer(data=data, action='custom_action')
```

## ⚡ Performance Benefits

### Query Optimization

Air DRF Relation can reduce database queries by 70-90% in typical scenarios:

```python
# Before: N+1 queries (1 + N author queries)
books = Book.objects.all()
for book in books:
    print(book.author.name)  # Database hit for each book

# After: 2 queries total (1 book query + 1 author query)
books = BookSerializer(Book.objects.all(), many=True).data
```

### Memory Efficiency

Smart preloading reduces memory usage by avoiding duplicate object loading:

```python
# Automatically deduplicates and batches related object queries
# Memory usage scales linearly, not exponentially
```

## 🧪 Testing

Run the test suite with Django's test runner:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run Django tests
python manage.py test

# Run with specific app
python manage.py test air_drf_relation
```

## 🛠️ Development

Set up development environment:

```bash
# Clone repository
git clone git@github.com:bubaley/air-drf-relation.git
cd air-drf-relation

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run linting and formatting
ruff check .
ruff format .

# Run security checks
bandit -r air_drf_relation/
```

## 📋 Requirements

- **Python**: 3.9+
- **Django**: 4.2+
- **Django REST Framework**: 3.14+
- **Python Libraries**: See [pyproject.toml](pyproject.toml) for complete list

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **PyPI**: [https://pypi.org/project/air-drf-relation/](https://pypi.org/project/air-drf-relation/)
- **Source Code**: [https://github.com/bubaley/air-drf-relation](https://github.com/bubaley/air-drf-relation)
- **Bug Reports**: [https://github.com/bubaley/air-drf-relation/issues](https://github.com/bubaley/air-drf-relation/issues)

## 💫 Support

If you find this package useful, please consider:

- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 📖 Improving documentation
- 🤝 Contributing code

---

**Built with ❤️ for the Django REST Framework community**
