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
from hybridroutertest.views import ServerConfigView, ClientModsView, ServerModsView, ServerConfigViewSet, Auto1, Auto2

router = HybridRouter()
router.register_view('server-config/', ServerConfigView.as_view(), name='server-config')
router.register_view('coucou/client/', ClientModsView.as_view(), name='coucou-client')
router.register_view('coucou/server/', ServerModsView.as_view(), name='coucou-server')
router.register(r'coucou', ServerConfigViewSet, basename='coucou')

# Nouveau cas
router.register_view('auto/1',Auto1.as_view(), name='auto1')
router.register_view('auto/2',Auto2.as_view(), name='auto2')

# Créer un routeur imbriqué pour 'mods/'
mods_router = HybridRouter()
mods_router.register_view('client/', ClientModsView.as_view(), name='mods-client')
mods_router.register_view('server/', ServerModsView.as_view(), name='mods-server')

# Enregistrer le routeur imbriqué sous le préfixe 'mods'
router.register_nested_router('mods', mods_router)


urlpatterns = [
    path('', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
