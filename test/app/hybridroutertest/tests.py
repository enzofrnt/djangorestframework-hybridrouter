from django.test import TestCase, override_settings
from django.urls import reverse, NoReverseMatch
from rest_framework.test import APIClient
from hybridrouter import HybridRouter
from hybridroutertest.views import ServerConfigView, ClientModsView, ServerModsView, ServerConfigViewSet
from django.urls import path, include

urlpatterns = []

class HybridRouterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.router.register_view(r'^server-config', ServerConfigView, name='server-config')
        cls.router.register_view(r'^mods/client', ClientModsView, name='mods-client')
        cls.router.register_view(r'^mods/server', ServerModsView, name='mods-server')
        cls.router.register_view(r'^coucou/client', ClientModsView, name='coucou-client')
        cls.router.register_view(r'^coucou/server', ServerModsView, name='coucou-server')
        cls.router.register_viewset(r'coucou', ServerConfigViewSet, basename='coucou')

        cls.client = APIClient()

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
        
@override_settings(ROOT_URLCONF='hybridroutertest.tests')
class HybridRouterTestCaseWithIntermediaryViews(CommonHybridRouterTests, HybridRouterTests):
    @classmethod
    def setUpTestData(cls):
        cls.router = HybridRouter(enable_intermediate_apiviews=True)
        super().setUpTestData()
        global urlpatterns
        urlpatterns =[
            path('', include(cls.router.urls)),
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

@override_settings(ROOT_URLCONF='hybridroutertest.tests')
class HybridRouterTestCaseWithoutIntermediaryViews(CommonHybridRouterTests, HybridRouterTests):
    @classmethod
    def setUpTestData(cls):
        cls.router = HybridRouter(enable_intermediate_apiviews=False)
        super().setUpTestData()
        global urlpatterns
        urlpatterns =[
            path('', include(cls.router.urls)),
        ] 

    def test_intermediary_view_not_present(self):
        with self.assertRaises(NoReverseMatch):
            reverse('mods')

        # viewset_url = reverse('coucou-list')
        # viewset_response = self.client.get(viewset_url)
        # self.assertEqual(viewset_response.status_code, 200)
        # attended_data = {'a': 'b'}
        # self.assertEqual(viewset_response.data, attended_data)