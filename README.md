# djangorestframework-hybridrouter
A router for ViewSets and Views! And with a better browsable API!

***Inspired by [this topic](https://stackoverflow.com/questions/18817988/using-django-rest-frameworks-browsable-api-with-apiviews/78459183#78459183).***

## Overview

The `HybridRouter` class is an extension of Django REST framework's `DefaultRouter` that allows you to register both ViewSets and APIViews. This provides more flexibility in managing your URL routes and offers a better browsable API experience.

## Features

- Register both ViewSets and APIViews.
- Simplified URL patterns for better readability.
- Custom intermediary API views for grouped endpoints.
- Enhanced browsable API.

## Installation

```bash
pip install djangorestframework-hybridrouter
```

## Usage

Here’s an example of how to use the HybridRouter:
```python
from django.urls import path, include
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from hybridrouter import HybridRouter

class ServerConfigViewSet(viewsets.ViewSet):
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
router.register_view(r'^server-config/$', ServerConfigView, name='server-config')
router.register_view(r'^mods/client/$', ClientModsView, name='mods-client')
router.register_view(r'^mods/server/$', ServerModsView, name='mods-server')
router.register_viewset(r'coucou', ServerConfigViewSet, basename='coucou')

urlpatterns = [
    path('', include(router.urls)),
]
```

## Documentation

HybridRouter

register_view(url, view, name)

Registers an APIView with the specified URL pattern.

	•	url: URL pattern for the view.
	•	view: The APIView class.
	•	name: The name of the view.

register_viewset(prefix, viewset, basename=None)

Registers a ViewSet with the specified prefix.

	•	prefix: URL prefix for the viewset.
	•	viewset: The ViewSet class.
	•	basename: The base name for the viewset (optional).

*Note: This method is a wrapper around `DefaultRouter.register()`, which is now deprecated in this module.*

## Advanced Features

Custom Intermediary API Views

The HybridRouter automatically creates custom intermediary API views for grouped endpoints. This is useful for organizing your API and providing a cleaner browsable interface.
