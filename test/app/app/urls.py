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
    2. Add a URL to urlpatterns:  path('', Home, name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.urls import path
from hybridrouter import HybridRouter
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView
from hybridroutertest.views import ServerConfigView, ClientModsView, ServerModsView, ServerConfigViewSet, Auto, Auto1, Auto2, Auto3        


router = HybridRouter()
router.register('server-config/', ServerConfigView, basename='server-config')
router.register('coucou/client/', ClientModsView, basename='coucou-client')
router.register('coucou/server/', ServerModsView, basename='coucou-server')
router.register('coucou/', ServerConfigViewSet, basename='coucou')

# Nouveau cas
router.register('auto/1/',Auto1, basename='auto1')
router.register('auto/2/',Auto2, basename='auto2')
router.register('auto/3/',Auto3, basename='auto3')

router.register('auto/3/coucou/',ServerConfigViewSet, basename='auto3coucou')
router.register('auto/3/coucou/1/',ServerConfigViewSet, basename='auto3coucou')
router.register('auto/3/coucou/2/',ServerConfigViewSet, basename='auto3coucou')

router.register('auto/3/caca/1/',ServerConfigViewSet, basename='auto3caca')
router.register('auto/3/caca/2/',ServerConfigViewSet, basename='auto3caca')


# router.register('autotkt/',Auto, basename='autotkt')
router.register('autotkt/1/',Auto1, basename='autotkt1')
router.register('autotkt/2/',Auto2, basename='autotkt2')

from hybridroutertest.viewsets import AutoModelViewSet
router.register('modelviewset/', AutoModelViewSet, basename='modelviewset')
router.register('modelviewset/<int:id>/couco1/',Auto1, basename='autotkt12')
router.register('modelviewset/1/couco2/',Auto2, basename='autotkt22')

from rest_framework.response import Response
from rest_framework.decorators import api_view
@api_view(['GET'])
def votre_vue(request, id): #Need to work on this
    return Response({'id': id}, status=200) 

from rest_framework.views import APIView

class VotreVue(APIView):
    def get(self, request, id):
        return Response({'id': id}, status=200)

router.register('me/<int:id>/', VotreVue, basename='me')

# Créer un routeur imbriqué pour 'mods/'
mods_router = HybridRouter()
mods_router.register('client/', ClientModsView, basename='mods-client')
mods_router.register('server/', ServerModsView, basename='mods-server')

# Enregistrer le routeur imbriqué sous le préfixe 'mods'
router.register_nested_router('mods', mods_router)



urlpatterns = [
    path('', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('objet/<int:id>/', votre_vue, name='nom_de_la_vue'),
]
