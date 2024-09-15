import re
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.urls.exceptions import NoReverseMatch
from rest_framework.viewsets import ViewSetMixin
from .utils import logger

class TreeNode:
    def __init__(self, name=None):
        self.name = name
        self.children = {}
        self.view = None  # Peut être une vue ou un ViewSet
        self.basename = None
        self.is_viewset = False
        self.is_nested_router = False
        self.router = None  # Pour les routeurs imbriqués manuellement
        self.url_name = None  # Nom unique pour la résolution des URLs

class HybridRouter(DefaultRouter):
    include_intermediate_views = True  # Contrôle les vues intermédiaires

    def __init__(self):
        super().__init__()
        self.root_node = TreeNode()
        self.used_url_names = set()  # Ensemble des noms d'URL utilisés

    def _sanitize_path_part(self, part):
        # Supprime les paramètres d'URL tels que <int:id> ou <str:name>
        return re.sub(r'<[^>]*>', '', part)

    def _generate_url_name(self, basename, path_parts):
        # Nettoyer les parties du chemin pour supprimer les paramètres d'URL
        sanitized_parts = [self._sanitize_path_part(part) for part in path_parts]
        # Supprimer les chaînes vides résultant du nettoyage
        sanitized_parts = [part for part in sanitized_parts if part]
        # Utiliser uniquement le basename pour le nom d'URL
        original_url_name = basename
        url_name = original_url_name

        # Vérifier si le nom d'URL est déjà utilisé
        counter = 1
        while url_name in self.used_url_names:
            if counter == 1:
                logger.warning(
                    f"Le nom d'URL '{original_url_name}' est déjà utilisé. Génération d'un nom unique."
                )
            # Générer un nom d'URL unique en ajoutant un suffixe numérique
            url_name = f"{original_url_name}_{counter}"
            counter += 1

        # Ajouter le nom d'URL à l'ensemble des noms utilisés
        self.used_url_names.add(url_name)

        return url_name

    def _add_route(self, path_parts, view, basename=None):
        # Déterminer si c'est un ViewSet ou une vue classique
        try:
            is_viewset = issubclass(view, ViewSetMixin)
        except TypeError:
            is_viewset = False

        node = self.root_node
        for part in path_parts:
            if part not in node.children:
                node.children[part] = TreeNode(name=part)
            node = node.children[part]

        # Générer un nom d'URL unique
        url_name = self._generate_url_name(basename, path_parts)

        node.view = view
        node.basename = basename
        node.is_viewset = is_viewset
        node.url_name = url_name

    def register(self, prefix, view, basename=None):
        """
        Enregistre un ViewSet ou une vue avec le préfixe spécifié.
        """
        if basename is None:
            basename = self.get_default_basename(view)
        path_parts = prefix.strip('/').split('/')
        self._add_route(path_parts, view, basename=basename)

    def register_nested_router(self, prefix, router):
        """
        Enregistre un routeur imbriqué sous un certain préfixe.
        """
        node = self.root_node
        path_parts = prefix.strip('/').split('/')
        for part in path_parts:
            if part not in node.children:
                node.children[part] = TreeNode(name=part)
            node = node.children[part]
        node.is_nested_router = True
        node.router = router

    def get_urls(self):
        urls = []
        self._build_urls(self.root_node, '', urls)
        return urls

    def _build_urls(self, node, prefix, urls):
        if node.is_nested_router:
            # Inclure le routeur imbriqué manuellement
            urls.append(
                path(
                    f'{prefix}',
                    include((node.router.urls, node.basename), namespace=node.basename)
                )
            )
        elif node.view:
            if node.is_viewset:
                # Utiliser DefaultRouter pour les ViewSets
                router = DefaultRouter()
                router.include_root_view = False  # Ne pas inclure la vue racine pour les routeurs imbriqués
                router.register('', node.view, basename=node.url_name)
                urls.append(path(f'{prefix}', include(router.urls)))
            else:
                # Ajouter la vue basique avec le nom unique
                urls.append(path(f'{prefix}', node.view.as_view(), name=node.url_name))
        if node.children:
            # Si on n'est pas à la racine et que les vues intermédiaires sont activées
            if prefix and self.include_intermediate_views:
                api_root_view = self._get_api_root_view(node, prefix)
                if api_root_view:
                    urls.append(path(f'{prefix}', api_root_view))
            for child in node.children.values():
                child_prefix = f'{prefix}{child.name}/'
                self._build_urls(child, child_prefix, urls)

    def _get_api_root_view(self, node, prefix):
        api_root_dict = OrderedDict()
        has_children = False

        for child_name, child_node in node.children.items():
            has_children = True
            if child_node.is_viewset or child_node.view:
                url_name = child_node.url_name
            elif child_node.is_nested_router:
                url_name = f'{prefix}{child_name}-api-root'
            else:
                url_name = f'{prefix}{child_name}-api-root'
            api_root_dict[child_name] = url_name

        if not has_children:
            return None

        class APIRoot(APIView):
            _ignore_model_permissions = True
            schema = None  # Exclure du schéma si nécessaire

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = request.resolver_match.namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name_full = f"{namespace}:{url_name}"
                    else:
                        url_name_full = url_name
                    try:
                        ret[key] = reverse(url_name_full, request=request)
                    except NoReverseMatch:
                        ret[key] = request.build_absolute_uri(f'{key}/')
                return Response(ret)

        return APIRoot.as_view()

    def get_api_root_view(self, api_urls=None):
        """
        Surcharge la vue API Root principale pour respecter la logique de
        `include_root_view` du DefaultRouter.
        """
        if not self.include_root_view:
            return None
        return self._get_api_root_view(self.root_node, '')

    @property
    def urls(self):
        urls = self.get_urls()
        if self.include_root_view:
            urls.append(path('', self.get_api_root_view(), name=self.root_view_name))
        return urls