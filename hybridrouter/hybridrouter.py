from rest_framework.routers import DefaultRouter
from django.urls import path, include
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.urls.exceptions import NoReverseMatch


class TreeNode:
    def __init__(self, name=None):
        self.name = name
        self.children = {}
        self.view = None  # Peut être une vue ou un ViewSet
        self.basename = None
        self.is_viewset = False
        self.is_nested_router = False
        self.router = None  # Pour les routeurs imbriqués manuellement


class HybridRouter(DefaultRouter):
    def __init__(self):
        super().__init__()
        self.root_node = TreeNode()

    def _add_route(self, path_parts, view, basename=None, is_viewset=False):
        node = self.root_node
        for part in path_parts:
            if part not in node.children:
                node.children[part] = TreeNode(name=part)
            node = node.children[part]
        node.view = view
        node.basename = basename
        node.is_viewset = is_viewset

    def register(self, prefix, viewset, basename=None):
        """
        Enregistre un ViewSet avec le préfixe spécifié.
        """
        if basename is None:
            basename = self.get_default_basename(viewset)
        path_parts = prefix.strip('/').split('/')
        self._add_route(path_parts, viewset, basename=basename, is_viewset=True)

    def register_view(self, route, view, basename=None):
        """
        Enregistre une vue basique.
        """
        if not basename:
            basename = view.__name__.lower()
        path_parts = route.strip('/').split('/')
        self._add_route(path_parts, view, basename=basename, is_viewset=False)

    def register_nested_router(self, prefix, router):
        """
        Enregistre un routeur imbriqué sous un certain préfixe.
        """
        path_parts = prefix.strip('/').split('/')
        node = self.root_node
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
            urls.append(path(f'{prefix}', include((node.router.urls, node.basename), namespace=node.basename)))
        elif node.view:
            if node.is_viewset:
                # Utiliser DefaultRouter pour les ViewSets
                router = DefaultRouter()
                router.register('', node.view, basename=node.basename)
                urls.append(path(f'{prefix}', include(router.urls)))
            else:
                # Ajouter la vue basique
                urls.append(path(f'{prefix}', node.view, name=node.basename))
        if node.children:
            # Créer une API Root intermédiaire si le nœud a des enfants
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
            if child_node.is_viewset:
                url_name = f'{child_node.basename}-list'
            elif child_node.is_nested_router:
                url_name = f'{prefix}{child_name}-api-root'
            elif child_node.view:
                url_name = child_node.basename
            else:
                url_name = f'{prefix}{child_name}-api-root'
            api_root_dict[child_name] = url_name

        if not has_children:
            return None

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
                        ret[key] = reverse(url_name_full, request=request)
                    except NoReverseMatch:
                        ret[key] = request.build_absolute_uri(f'{key}/')
                return Response(ret)

        return APIRoot.as_view()

    def get_api_root_view(self, api_urls=None):
        # Surcharge pour la racine principale
        return self._get_api_root_view(self.root_node, '')

    @property
    def urls(self):
        return self.get_urls()