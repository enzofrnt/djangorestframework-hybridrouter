from django.urls import re_path
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework.response import Response
from urllib.parse import urlsplit, urlunsplit

class HybridRouter(DefaultRouter):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_view_urls = {}
        
    def register_view(self,  url, view, name):
        path = re_path(url, view.as_view(), name=name)
        self._api_view_urls[name] = path
        
    def register_viewset(self, prefix, viewset, basename=None):
        super().register(prefix, viewset, basename)
        
    def register(self, prefix, viewset, basename=None):
        raise NotImplementedError("Use register_viewset or register_view instead.")

    def remove_api_view(self, name):
        if name in self._api_view_urls:
            del self._api_view_urls[name]

    @property
    def api_view_urls(self):
        return self._api_view_urls.copy()

    def get_urls(self):
        urls = super().get_urls()
        urls.extend(self._api_view_urls.values())

        pattern_mapping = {}
        simplified_urls = []

        for url in urls:
            # Extract the path pattern as a string
            path = url.pattern.regex.pattern if hasattr(url.pattern, 'regex') else url.pattern._route

            # Simplify the path by removing regex-specific elements
            simple_path = path.replace('^', '').replace('$', '').replace('.(?P<format>[a-z0-9]+)/?', '').replace('(?P<format>.[a-z0-9]+/?)', '')
            if "\\" not in simple_path:
                simplified_urls.append(simple_path)
                pattern_mapping[simple_path] = url.name

        # Remove duplicates while preserving order
        simplified_urls = list(dict.fromkeys(simplified_urls))

        groupes = {}
        for path in simplified_urls:
            base_path = path.split('/')[0]
            groupes.setdefault(base_path, []).append(pattern_mapping[path])

        for base_path, endpoints in groupes.items():
            if len(endpoints) > 1:
                self.create_custom_intermediary_api_view(urls, base_path, endpoints)


        return urls

    def create_custom_intermediary_api_view(self, urls, base_path, endpoints):
        class CustomIntermediaryAPIView(APIView):
            _ignore_model_permissions = True

            def get(self, request, format=None):
                ret = {endpoint: reverse(endpoint, request=request, format=format) for endpoint in self.endpoints}
                return Response(ret)

        CustomIntermediaryAPIView.endpoints = endpoints
        CustomIntermediaryAPIView.__name__ = f"API{base_path.capitalize()}"
        urls.append(re_path(rf'^{base_path}/$', CustomIntermediaryAPIView.as_view(), name=base_path))

    def get_api_root_view(self, **kwargs):
        api_root_dict = {prefix: self.routes[0].name.format(basename=basename) for prefix, viewset, basename in self.registry}
        api_view_urls = self.api_view_urls
        class APIRoot(APIView):
            _ignore_model_permissions = True
            
            def simplify_url(self, url):
                parsed_url = urlsplit(url)
                path_segments = parsed_url.path.split('/')
                new_path = f"/{path_segments[1]}/" if len(path_segments) > 1 else '/'
                return urlunsplit((parsed_url.scheme, parsed_url.netloc, new_path, '', ''))

            def get(self, request, format=None):
                ret = {}
                ret_simplify = {}
                
                for key, url_name in api_root_dict.items():
                    full_url = reverse(url_name, request=request, format=format)
                    ret[key] = full_url
                    simplify_url = self.simplify_url(full_url)
                    if simplify_url != full_url:
                        ret_simplify[key] = simplify_url
                for api_view_key in api_view_urls:
                    full_url = reverse(api_view_urls[api_view_key].name, request=request, format=format)
                    ret[api_view_key] = full_url
                    simplify_url = self.simplify_url(full_url)
                    if simplify_url != full_url:
                        ret_simplify[api_view_key] = simplify_url

                result = {}
                compteur = {}

                for url in ret_simplify.values():                  
                    compteur[url] = compteur.get(url, 0) + 1

                for name, url in ret_simplify.items():
                    if compteur[url] > 1:
                        result.setdefault(url, []).append(name)
                
                for url, names in result.items():
                    for name in names:
                        ret.pop(name)
                        new_name = url.strip('/').split('/')[-1]
                        ret[new_name] = url
                                        
                return Response(ret)
        
        return APIRoot.as_view()