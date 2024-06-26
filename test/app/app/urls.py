"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.urls import path
from hybridrouter import HybridRouter
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView
from rest_framework.routers import DefaultRouter
from hybridroutertest.views import ServerConfigView, ClientModsView, ServerModsView, ServerConfigViewSet

router = HybridRouter(enable_intermediate_apiviews=True)
router.register_view(r'^server-config', ServerConfigView, name='server-config')
router.register_view(r'^mods/client', ClientModsView, name='mods-client')
router.register_view(r'^mods/server', ServerModsView, name='mods-server')
router.register_view(r'^coucou/client', ClientModsView, name='coucou-client')
router.register_view(r'^coucou/server', ServerModsView, name='coucou-server')
router.register_viewset(r'coucou', ServerConfigViewSet, basename='coucou')


urlpatterns = [
    path('', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
