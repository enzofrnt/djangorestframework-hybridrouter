# routers.py

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.urls.exceptions import NoReverseMatch

class HybridRouter(DefaultRouter):
    # ... Votre code existant ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_urls = []
        self.extra_views = []
        self.nested_routers = {}  # Dictionnaire pour les routeurs imbriqués
        
    def register_view(self, route, view, name=None):
        """
        Enregistre une vue classique.

        Arguments:
            route (str): Le chemin URL.
            view (callable): La vue à appeler.
            name (str, optionnel): Le nom de la route.
        """
        if not name:
            name = view.__name__.lower()
        self.extra_urls.append(path(route, view, name=name))
        self.extra_views.append({'name': name, 'route': route})

    def get_urls(self):
        # Obtenir les URLs du DefaultRouter
        urls = super().get_urls()
        # Ajouter les URLs des vues classiques
        urls += self

    def register_nested_router(self, prefix, router):
        """
        Enregistre un routeur imbriqué sous un certain préfixe.
        """
        self.nested_routers[prefix] = router

    def get_urls(self):
        # Obtenir les URLs du DefaultRouter
        urls = super().get_urls()

        # Ajouter les URLs des vues classiques
        urls += self.extra_urls

        # Ajouter les URLs des routeurs imbriqués
        for prefix, router in self.nested_routers.items():
            urls.append(path(f'{prefix}/', include((router.urls, 'nested'), namespace=prefix)))

        return urls

    def get_api_root_view(self, api_urls=None):
        # Initialiser api_root_dict avant la définition de la classe APIRoot
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name

        # Inclure les ViewSets enregistrés
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        # Inclure les vues basiques enregistrées
        for view in self.extra_views:
            api_root_dict[view['name']] = view['name']

        # Inclure les préfixes des routeurs imbriqués
        for prefix in self.nested_routers.keys():
            api_root_dict[prefix] = f'{prefix}-api-root'

        class APIRoot(APIView):
            _ignore_model_permissions = True

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = request.resolver_match.namespace

                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name_full = f"{namespace}:{url_name}"
                    else:
                        url_name_full = url_name
                    try:
                        ret[key] = reverse(url_name_full, request=request, format=kwargs.get('format'))
                    except NoReverseMatch:
                        ret[key] = request.build_absolute_uri(f'{key}/')
                return Response(ret)

        return APIRoot.as_view()