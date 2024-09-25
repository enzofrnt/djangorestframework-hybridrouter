from collections import OrderedDict
from typing import Optional, Type, Union, overload

from django.urls import include, path, re_path
from django.urls.exceptions import NoReverseMatch
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin

from .utils import logger


class TreeNode:
    def __init__(self, name=None):
        self.name = name
        self.children = {}
        self.view = None  # Can be a view or a ViewSet
        self.basename = None
        self.is_viewset = False
        self.is_nested_router = False
        self.router = None  # For manually nested routers


class HybridRouter(DefaultRouter):
    include_intermediate_views = True  # Controls intermediate views
    trailing_slash = "/?"  # Define trailing slash as in DRF's SimpleRouter

    def __init__(self):
        super().__init__()
        self.root_node = TreeNode()
        self.used_url_names = set()  # Set of used URL names
        self.basename_registry = {}  # Registry for basenames

    def _add_route(self, path_parts, view, basename=None):
        # Determine if it's a ViewSet or a regular view
        is_viewset = False
        if isinstance(view, type):
            is_viewset = issubclass(view, ViewSetMixin)
        else:
            is_viewset = isinstance(view, ViewSetMixin)

        node = self.root_node
        for part in path_parts:
            if part not in node.children:
                node.children[part] = TreeNode(name=part)
            node = node.children[part]

        node.view = view
        node.basename = basename
        node.is_viewset = is_viewset

    @overload
    def register(
        self, prefix: str, viewset: Type[APIView], basename: Optional[str] = None
    ) -> None:
        ...

    @overload
    def register(
        self, prefix: str, viewset: Type[ViewSetMixin], basename: Optional[str] = None
    ) -> None:
        ...

    def register(
        self,
        prefix: str,
        viewset: Union[Type[APIView], Type[ViewSetMixin]],
        basename: Optional[str] = None,
    ) -> None:
        """
        Registers an APIView or ViewSet with the specified prefix.

        Args:
            prefix (str): URL prefix for the view or viewset.
            viewset (Type[APIView] or Type[ViewSetMixin]): The APIView or ViewSet class.
            basename (str, optional): The base name for the view or viewset. Defaults to None.
        """
        if basename is None:
            basename = self.get_default_basename(viewset)
        path_parts = prefix.strip("/").split("/")

        # Register the information for conflict resolution
        if basename not in self.basename_registry:
            self.basename_registry[basename] = []
        self.basename_registry[basename].append(
            {
                "prefix": prefix,
                "view": viewset,
                "basename": basename,
                "path_parts": path_parts,
            }
        )

    def register_nested_router(self, prefix, router):
        """
        Registers a nested router under a certain prefix.
        """
        node = self.root_node
        path_parts = prefix.strip("/").split("/")
        for part in path_parts:
            if part not in node.children:
                node.children[part] = TreeNode(name=part)
            node = node.children[part]
        node.is_nested_router = True
        node.router = router

    def _resolve_basename_conflicts(self):
        """
        Resolve basename conflicts by assigning unique basenames
        and displaying a single warning message per conflicting basename.
        """
        for basename, registrations in self.basename_registry.items():
            if len(registrations) > 1:
                # Conflict detected
                prefixes = [reg["prefix"] for reg in registrations]
                logger.warning(
                    "The basename '%s' is used for multiple registrations: %s. Generating unique basenames.",
                    basename,
                    ", ".join(prefixes),
                )
                # Assign new unique basenames
                for idx, reg in enumerate(registrations, start=1):
                    unique_basename = f"{basename}_{idx}"
                    reg["basename"] = unique_basename
            # Else, the basename is unique, no need to change it

    def get_urls(self):
        # Before building the URLs, resolve basename conflicts
        self._resolve_basename_conflicts()
        # Build the tree by calling _add_route for each registration
        for registrations in self.basename_registry.values():
            for reg in registrations:
                self._add_route(
                    reg["path_parts"], reg["view"], basename=reg["basename"]
                )
        # Now, build the URLs
        urls = []
        self._build_urls(self.root_node, "", urls)
        return urls

    def _build_urls(self, node, prefix, urls):
        # If there's a view at this node, add it
        if node.view:
            if node.is_viewset:
                # Generate URL patterns directly for the ViewSet
                viewset_urls = self._get_viewset_urls(node.view, prefix, node.basename)
                urls.extend(viewset_urls)
            else:
                # Add the basic view with a unique name
                name = f"{node.basename}"
                urls.append(path(f"{prefix}", node.view.as_view(), name=name))
        # If this node is a nested router, include it
        elif node.is_nested_router:
            urls.append(
                path(
                    f"{prefix}",
                    include(node.router.urls),
                )
            )
        # Process child nodes
        if node.children:
            # Include intermediate views if enabled and there's no view at this node
            if (
                self.include_intermediate_views
                and not node.view
                and not node.is_nested_router
            ):
                if prefix:
                    api_root_view = self._get_api_root_view(node, prefix)
                    if api_root_view:
                        urls.append(path(f"{prefix}", api_root_view))
            for child in node.children.values():
                child_prefix = f"{prefix}{child.name}/"
                self._build_urls(child, child_prefix, urls)

    def _get_viewset_urls(self, viewset, prefix, basename):
        """
        Génère les URL patterns pour un ViewSet sans utiliser de sous-routeur.
        """
        routes = self.get_routes(viewset)
        urls = []
        lookup = self.get_lookup_regex(viewset)

        for route in routes:
            mapping = self.get_method_map(viewset, route.mapping)
            if not mapping:
                continue

            # Construire le pattern URL
            regex = route.url.format(
                prefix=prefix.rstrip("/"),
                lookup=lookup,
                trailing_slash=self.trailing_slash,
            )

            # Générer la vue
            view = viewset.as_view(mapping, **route.initkwargs)

            # Générer le nom de l'URL
            name = route.name.format(basename=basename) if route.name else None

            # Ajouter le pattern URL
            urls.append(re_path(regex, view, name=name))

        return urls

    def get_method_map(self, viewset, method_map):
        """
        Given a viewset and a mapping {http_method: action},
        return a new mapping dict mapping the HTTP methods
        to the corresponding viewset methods if they exist.
        """
        bound_methods = {}
        for http_method, action in method_map.items():
            if hasattr(viewset, action):
                bound_methods[http_method] = action
        return bound_methods

    def get_lookup_regex(self, viewset, lookup_prefix=""):
        """
        Return the regex pattern for the lookup field.
        """
        lookup_field = getattr(viewset, "lookup_field", "pk")
        lookup_url_kwarg = getattr(viewset, "lookup_url_kwarg", None) or lookup_field
        lookup_value = getattr(viewset, "lookup_value_regex", "[^/.]+")
        return f"(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value})"

    def _get_api_root_view(self, node, prefix):
        api_root_dict = OrderedDict()
        has_children = False

        for child_name, child_node in node.children.items():
            has_children = True
            if child_node.is_viewset or child_node.view:
                url_name = f"{child_node.basename}-list"
            elif child_node.is_nested_router:
                url_name = f"{prefix}{child_name}-api-root"
            else:
                url_name = f"{prefix}{child_name}-api-root"
            api_root_dict[child_name] = url_name

        if not has_children:
            return None

        class APIRoot(APIView):
            _ignore_model_permissions = True
            schema = None  # Exclude from schema if necessary

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
                        ret[key] = request.build_absolute_uri(f"{key}/")
                return Response(ret)

        return APIRoot.as_view()

    def get_api_root_view(self, api_urls=None):
        """
        Override the main API Root view to respect the `include_root_view`
        logic of DefaultRouter.
        """
        if not self.include_root_view:
            return None
        return self._get_api_root_view(self.root_node, "")

    @property
    def urls(self):
        urls = self.get_urls()
        if self.include_root_view:
            urls.append(path("", self.get_api_root_view(), name=self.root_view_name))
        return urls
