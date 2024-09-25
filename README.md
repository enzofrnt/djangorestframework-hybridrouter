# djangorestframework-hybridrouter

A router for ViewSets and APIViews, with a better browsable API and support for nested routers!

***Inspired by [this topic](https://stackoverflow.com/questions/18817988/using-django-rest-frameworks-browsable-api-with-apiviews/78459183#78459183).***

## Overview

The `HybridRouter` class is an extension of Django REST Framework's `DefaultRouter` that allows you to register both `ViewSet`s and `APIView`s. It provides more flexibility in managing your URL routes, offers a better browsable API experience, and supports nested routers.

## Features

- Register both `ViewSet`s and `APIView`s using a unified interface.
- Simplified URL patterns for better readability.
- Automatic creation of intermediate API views for grouped endpoints (configurable).
- Support for nested routers.
- Automatic conflict resolution for basenames.

## Installation

```bash
pip install djangorestframework-hybridrouter
```

## Usage

Here’s an example of how to use the `HybridRouter`:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.urls import path, include
from hybrid_router import HybridRouter

class ServerConfigViewSet(ViewSet):
    def list(self, request):
        return Response({'a': 'b'})

class ServerConfigView(APIView):
    def get(self, request):
        return Response({'config': 'server'})

class ClientModsView(APIView):
    def get(self, request):
        return Response({'mods': 'client'})

class ServerModsView(APIView):
    def get(self, request):
        return Response({'mods': 'server'})

router = HybridRouter()
router.include_intermediate_views = True  # Enable intermediate API views

# Register APIViews
router.register('server-config', ServerConfigView, basename='server-config')
router.register('mods/client', ClientModsView, basename='mods-client')
router.register('mods/server', ServerModsView, basename='mods-server')

# Register a ViewSet
router.register('coucou', ServerConfigViewSet, basename='coucou')

# Register more APIViews under 'coucou' prefix
router.register('coucou/client', ClientModsView, basename='coucou-client')
router.register('coucou/server', ServerModsView, basename='coucou-server')

urlpatterns = [
    path('', include(router.urls)),
]
```

This configuration will generate URLs for both APIViews and ViewSets, and include intermediate API views for grouped endpoints.

## Documentation

**HybridRouter**

-   `register(prefix, view, basename=None)`

    Registers an `APIView` or `ViewSet` with the specified prefix.

    -   `prefix`: URL prefix for the view or viewset.
    -   `view`: The `APIView `or `ViewSet` class.
    -   `basename`: The base name for the view or viewset (optional). If not provided, it will be automatically generated.
-   `register_nested_router(prefix, router)`

    Registers a nested router under a specific prefix.

    -   `prefix`: URL prefix under which the nested router will be registered.
    -   `router`: The DRF router instance to be nested.

**Attributes**

-   `include_intermediate_views` (default True)

    Controls whether intermediate API views are automatically created for grouped endpoints. When set to True, the router will generate intermediate views that provide a browsable API listing of all endpoints under a common prefix.

**Notes**

-   Automatic Basename Conflict Resolution

    The `HybridRouter` automatically handles conflict resolution for `basenames`. If you register multiple `views` or `viewsets` with the same `basename`, it will assign unique `basenames` and log a warning.

-   Trailing Slash

    The `HybridRouter` uses a configurable trailing_slash attribute, defaulting to "/?" to match DRF’s `SimpleRouter` behavior.


## Advanced Features

### Custom Intermediary API Views

The `HybridRouter` can automatically create custom intermediary API views for grouped endpoints. This feature improves the organization of your API and provides a cleaner browsable interface.

**Example:**

```python
router = HybridRouter()
router.include_intermediate_views = True  # Enable intermediate API views

router.register('server-config', ServerConfigView, basename='server-config')
router.register('server-config/map', ServerConfigView, basename='server-config')
router.register('server-config/health', ServerConfigView, basename='server-config')
router.register('mods/client', ClientModsView, basename='mods-client')
router.register('mods/server', ServerModsView, basename='mods-server')
```

With `include_intermediate_views` set to True, the router will create intermediate views at the `mods/` prefix, providing a browsable API that lists both `client` and `server` endpoints under `mods/`. Also note that here for `server-config/` endpoints an intermediate view will not be created because it's already registered.

### Nested Routers

You can register nested routers under a specific prefix using `register_nested_router`. This allows you to include routers from other apps or create a complex URL structure.

**Example:**

```python
from rest_framework.routers import DefaultRouter

nested_router = DefaultRouter()
nested_router.register('items', ItemViewSet, basename='item')

router = HybridRouter()
router.register_nested_router('nested/', nested_router)

urlpatterns = [
    path('', include(router.urls)),
]
```


In this example, all routes from nested_router will be available under the `nested/` prefix.

## Experimental Features

The automatic creation of intermediary API views is a feature that improves the browsable API experience. This feature is still in development and may not work as expected in all cases. Please report any issues or suggestions.

```python
router = HybridRouter(enable_intermediate_apiviews=False)

router.register('server-config', ServerConfigView, name='server-config')
router.register('mods/client', ClientModsView, name='mods-client')
router.register('mods/server', ServerModsView, name='mods-server')
router.register('coucou/client', ClientModsView, name='coucou-client')
router.register('coucou/server', ServerModsView, name='coucou-server')
router.register('coucou', ServerConfigViewSet, basename='coucou')
```

With this configuration of the router with `enable_intermediate_apiviews`set to `False`, the intermediary API views will not be created. So the browsable API will look like on a `DefaultRouter` :

![image](./docs/imgs/Before.png)

But if you set `enable_intermediate_apiviews` to `True`, the intermediary API views will be created and the browsable API will look like this:

```python
router = HybridRouter(enable_intermediate_apiviews=True)
```

![image](./docs/imgs/After_1.png)
![image](./docs/imgs/After_2.png)

This improves the readability and the logic of the browsable API and provides a better user experience.

And as you can see that will not interfere with other already existing views. **Here, the `ServerConfigViewSet` is still accessible through the `coucou` endpoint and as not been overridden by an intermediary API view.**

## Testing

The package includes comprehensive tests to ensure reliability. Here are some highlights:

- Registering Views and ViewSets
Tests registering both APIViews and ViewSets, ensuring that URLs are correctly generated and accessible.

- Intermediate Views
Tests the creation of intermediate views when include_intermediate_views is enabled or disabled.

- Nested Routers
Tests registering nested routers and ensuring that their routes are correctly included under the specified prefix.

- Basename Conflict Resolution
Tests automatic conflict resolution when multiple views or viewsets are registered with the same basename.

## Notes

- Compatibility

    The HybridRouter is designed to work seamlessly with Django REST Framework and is compatible with existing DRF features like schema generation.

- Spectacular Support

    Will be added in the future.
