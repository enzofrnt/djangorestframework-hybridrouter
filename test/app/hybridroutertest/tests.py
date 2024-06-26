import unittest
import sys
import importlib
import os

from django import setup
from django.conf import settings

if settings.configured is False:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    setup()

from unittest.mock import patch
from hybridrouter import HybridRouter
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from hybridroutertest.views import ServerConfigView, ClientModsView, ServerModsView, ServerConfigViewSet
from django.urls import path, include, reverse, NoReverseMatch

urlpatterns = []

class HybridRouterTests(TestCase):
    
    def setUp(self):
        self.router.register_view(r'^server-config', ServerConfigView, name='server-config')
        self.router.register_view(r'^mods/client', ClientModsView, name='mods-client')
        self.router.register_view(r'^mods/server', ServerModsView, name='mods-server')
        self.router.register_view(r'^coucou/client', ClientModsView, name='coucou-client')
        self.router.register_view(r'^coucou/server', ServerModsView, name='coucou-server')
        self.router.register_viewset(r'coucou', ServerConfigViewSet, basename='coucou')
        
        self.router.register_view('prefix1', ServerConfigView, 'basename1')
        self.router.register_viewset('prefix2', ServerConfigViewSet, 'basename2')
        self.router.register('prefix3', ServerConfigViewSet, 'basename3')
        self.router.register('prefix4', ServerConfigView, 'basename4')
        
        
        self.client = APIClient()

class CommonHybridRouterTests:
    def test_server_config_view(self):
        url = reverse('server-config')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'config': 'server'})

    def test_client_mods_view(self):
        url = reverse('mods-client')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'mods': 'client'})

    def test_server_mods_view(self):
        url = reverse('mods-server')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'mods': 'server'})

    def test_coucou_client_view(self):
        url = reverse('coucou-client')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'mods': 'client'})

    def test_coucou_server_view(self):
        url = reverse('coucou-server')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'mods': 'server'})

    def test_coucou_viewset_list(self):
        url = reverse('coucou-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'a': 'b'})
        
    def test_router_regsiter_view(self):
        url = reverse('basename1')
        repsonse = self.client.get(url)
        self.assertEqual(repsonse.status_code, 200)
        self.assertEqual(repsonse.data, {'config': 'server'})
            
    def test_router_regsiter_viewset(self):
        url = reverse('basename2-list')
        repsonse = self.client.get(url)
        self.assertEqual(repsonse.status_code, 200)
        self.assertEqual(repsonse.data, {'a': 'b'})
        
    def test_router_regsiter_a_viewset(self):
        url = reverse('basename3-list')
        repsonse = self.client.get(url)
        self.assertEqual(repsonse.status_code, 200)
        self.assertEqual(repsonse.data, {'a': 'b'})
        
            
    def test_router_resgister_an_api_view(self):
        url = reverse('basename4')
        repsonse = self.client.get(url)
        self.assertEqual(repsonse.status_code, 200)
        self.assertEqual(repsonse.data, {'config': 'server'})
            
    def test_router_resgister_not_api_view_not_viewset(self):
        class TestNotApiViewNotViewSet() :
            pass
        with self.assertRaises(ValueError):
            self.router.register('prefix', TestNotApiViewNotViewSet, 'basename')
        
@override_settings(ROOT_URLCONF='hybridroutertest.tests')
class HybridRouterTestCaseWithIntermediaryViews(CommonHybridRouterTests, HybridRouterTests):
    
    def setUp(self, router=None):
        if not router :
            self.router = HybridRouter(enable_intermediate_apiviews=True)
        else :
            self.router = router
            
        super().setUp()
        
        global urlpatterns
        urlpatterns =[
            path('', include(self.router.urls)),
        ] 

    def test_view_not_overridden_by_intermediary_view(self):
        url = reverse('coucou')
        response = self.client.get(url)
        attended_data = {'a': 'b'}
        self.assertEqual(response.data, attended_data)
        
    def test_intermediary_view_present(self):
        url = reverse('mods')
        response = self.client.get(url)
        attended_data = {
            'mods-client': response.wsgi_request.build_absolute_uri(reverse('mods-client')),
            'mods-server': response.wsgi_request.build_absolute_uri(reverse('mods-server'))
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, attended_data)
    
    def test_api_root_view(self):
        url = reverse('api-root')
        response = self.client.get(url)
        attended_data = {
            'basename1': response.wsgi_request.build_absolute_uri(reverse('basename1')),
            'basename4': response.wsgi_request.build_absolute_uri(reverse('basename4')),
            'server-config': response.wsgi_request.build_absolute_uri(reverse('server-config')),
            'mods': response.wsgi_request.build_absolute_uri(reverse('mods')),
            'coucou': response.wsgi_request.build_absolute_uri(reverse('coucou')),
            'coucou-client': response.wsgi_request.build_absolute_uri(reverse('coucou-client')),
            'coucou-server': response.wsgi_request.build_absolute_uri(reverse('coucou-server')),
            
            'prefix2': response.wsgi_request.build_absolute_uri(reverse('basename2-list')),
            'prefix3': response.wsgi_request.build_absolute_uri(reverse('basename3-list')),
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, attended_data)

@override_settings(ROOT_URLCONF='hybridroutertest.tests')
class HybridRouterTestCaseWithoutIntermediaryViews(CommonHybridRouterTests, HybridRouterTests):
    
    def setUp(self, router=None):
        if not router :
            self.router = HybridRouter(enable_intermediate_apiviews=False)
        else :
            self.router = router
            
        super().setUp()
        
        global urlpatterns
        urlpatterns =[
            path('', include(self.router.urls)),
        ] 

    def test_intermediary_view_not_present(self):
        with self.assertRaises(NoReverseMatch):
            reverse('mods')
            
    def test_api_root_view(self):
        url = reverse('api-root')
        response = self.client.get(url)
        attended_data = {
            'basename1': response.wsgi_request.build_absolute_uri(reverse('basename1')),
            'basename4': response.wsgi_request.build_absolute_uri(reverse('basename4')),
            'mods-client': response.wsgi_request.build_absolute_uri(reverse('mods-client')),
            'mods-server': response.wsgi_request.build_absolute_uri(reverse('mods-server')),

            'server-config': response.wsgi_request.build_absolute_uri(reverse('server-config')),
            'coucou': response.wsgi_request.build_absolute_uri(reverse('coucou-list')),
            'coucou-client': response.wsgi_request.build_absolute_uri(reverse('coucou-client')),
            'coucou-server': response.wsgi_request.build_absolute_uri(reverse('coucou-server')),            
            'prefix2': response.wsgi_request.build_absolute_uri(reverse('basename2-list')),
            'prefix3': response.wsgi_request.build_absolute_uri(reverse('basename3-list')),
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, attended_data)            

class TestHybridRouterWithoutSpectacular(unittest.TestCase):
    
    def setUp(self):
        super().setUp()
        modules_to_remove = [
            'hybridrouter', 'hybridrouter.hybridrouter', 'drf_spectacular', 'drf_spectacular.utils'
        ]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]

    @patch.dict('sys.modules', {'drf_spectacular': None})
    def test_import_error(self):
        from hybridrouter import hybridrouter
        importlib.reload(hybridrouter)
        self.assertTrue(hasattr(hybridrouter, 'DRF_SPECTACULAR'))
        self.assertFalse(getattr(hybridrouter, 'DRF_SPECTACULAR'))
        
class HybridRouterTestCaseWithIntermediaryViewsWithoutSpectacular(TestHybridRouterWithoutSpectacular, HybridRouterTestCaseWithIntermediaryViews):
    def setUp(cls):
        super().setUp()

class   HybridRouterTestCaseWithoutIntermediaryViewsWithoutSpectacular(TestHybridRouterWithoutSpectacular, HybridRouterTestCaseWithoutIntermediaryViews):
    def setUp(cls):
        super().setUp()
            