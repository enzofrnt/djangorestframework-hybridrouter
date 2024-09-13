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
from hybridroutertest.views import ServerConfigView, ClientModsView, ServerModsView, ServerConfigViewSet, Auto, Auto1, Auto2, Auto3

router = HybridRouter()
router.register_view('server-config/', ServerConfigView.as_view(), basename='server-config')
router.register_view('coucou/client/', ClientModsView.as_view(), basename='coucou-client')
router.register_view('coucou/server/', ServerModsView.as_view(), basename='coucou-server')
router.register('coucou/', ServerConfigViewSet, basename='coucou')

# Nouveau cas
router.register_view('auto/1/',Auto1.as_view(), basename='auto1')
router.register_view('auto/2/',Auto2.as_view(), basename='auto2')
router.register_view('auto/3/',Auto3.as_view(), basename='auto3')

router.register('auto/3/coucou/',ServerConfigViewSet, basename='auto3coucou')
router.register('auto/3/coucou/1/',ServerConfigViewSet, basename='auto3coucou')
router.register('auto/3/coucou/2/',ServerConfigViewSet, basename='auto3coucou')

router.register('auto/3/caca/1/',ServerConfigViewSet, basename='auto3caca')
router.register('auto/3/caca/2/',ServerConfigViewSet, basename='auto3caca')


router.register_view('autotkt/',Auto.as_view(), basename='autotkt')
router.register_view('autotkt/1/',Auto1.as_view(), basename='autotkt1')
router.register_view('autotkt/2/',Auto2.as_view(), basename='autotkt2')

# Créer un routeur imbriqué pour 'mods/'
mods_router = HybridRouter()
mods_router.register_view('client/', ClientModsView.as_view(), basename='mods-client')
mods_router.register_view('server/', ServerModsView.as_view(), basename='mods-server')

# Enregistrer le routeur imbriqué sous le préfixe 'mods'
router.register_nested_router('mods', mods_router)


urlpatterns = [
    path('', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
