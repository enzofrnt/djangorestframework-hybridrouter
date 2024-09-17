import types

from django.test import override_settings
from django.urls import include, path, reverse
from django.urls.resolvers import get_resolver
from rest_framework import status
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIClient

from .conftest import recevoir_test_url_resolver
from .models import Item
from .views import ItemView
from .viewsets import ItemViewSet, SlugItemViewSet


def create_urlconf(router):
    module = types.ModuleType("temporary_urlconf")
    module.urlpatterns = [
        path("", include(router.urls)),
    ]
    return module


@override_settings()
def test_register_views_and_viewsets(hybrid_router):
    # Enregistrer des vues simples
    hybrid_router.register("items-view", ItemView, basename="item-view")

    # Enregistrer des ViewSets
    hybrid_router.register("items-set", ItemViewSet, basename="item-set")

    # Créer un module temporaire pour les URLs
    urlconf = create_urlconf(hybrid_router)

    # Définir ROOT_URLCONF sur le module temporaire
    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier que les URL sont correctement générées
        view_url = reverse("item-view")
        list_url = reverse("item-set-list")
        detail_url = reverse("item-set-detail", kwargs={"pk": 1})

        assert view_url == "/items-view/"
        assert list_url == "/items-set/"
        assert detail_url == "/items-set/1/"


@override_settings()
def test_url_patterns(hybrid_router, db):
    hybrid_router.register("items", ItemViewSet, basename="item")

    # Créer un module temporaire pour les URLs
    urlconf = create_urlconf(hybrid_router)

    # Définir ROOT_URLCONF sur le module temporaire
    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier que les patterns d'URL sont correctement générés
        list_url = reverse("item-list")
        detail_url = reverse("item-detail", kwargs={"pk": 1})

        assert list_url == "/items/"
        assert detail_url == "/items/1/"

        # Créer un item pour le test
        Item.objects.create(id=1, name="Test Item", description="Item for testing.")

        # Vérifier que les URL fonctionnent avec le client de test
        client = APIClient()
        response = client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK


@override_settings()
def test_custom_lookup_field(hybrid_router, db):
    hybrid_router.register("slug-items", SlugItemViewSet, basename="slug-item")

    # Créer un module temporaire pour les URLs
    urlconf = create_urlconf(hybrid_router)

    # Définir ROOT_URLCONF sur le module temporaire
    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Créer un item avec un nom unique
        item = Item.objects.create(
            name="unique-name", description="Item with unique name."
        )

        # Vérifier que l'URL utilise le champ de recherche personnalisé
        detail_url = reverse("slug-item-detail", kwargs={"name": "unique-name"})
        assert detail_url == "/slug-items/unique-name/"

        client = APIClient()
        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK


# def test_api_root_view(hybrid_router, db): #NEED MORE TEST CASE
#     hybrid_router.include_root_view = True  # Is by default True


#     urlconf = create_urlconf(hybrid_router)

#     with


def test_no_api_root_view(hybrid_router, db):
    hybrid_router.include_root_view = False

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        response = APIClient().get("/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_intermediary_view(hybrid_router, db):  # NEED MORE TEST CASE
    hybrid_router.include_intermediate_views = True  # Is by default True

    hybrid_router.register("items/1/", ItemView, basename="item_1")
    hybrid_router.register("items/2/", ItemView, basename="item_2")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        response = APIClient().get("/items/1/")
        assert response.status_code == status.HTTP_200_OK

        response = APIClient().get("/items/2/")
        assert response.status_code == status.HTTP_200_OK

        # Is the intermediary view available

        response = APIClient().get("/items/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "1": "http://testserver/items/1/",
            "2": "http://testserver/items/2/",
        }


def test_no_intermediary_view(hybrid_router, db):
    hybrid_router.include_intermediate_views = False

    hybrid_router.register("items/1/", ItemView, basename="item_1")
    hybrid_router.register("items/2/", ItemView, basename="item_2")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        response = APIClient().get("/items/1/")
        assert response.status_code == status.HTTP_200_OK

        response = APIClient().get("/items/2/")
        assert response.status_code == status.HTTP_200_OK

        # Is the intermediary view available

        response = APIClient().get("/items/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@override_settings()
def test_register_nested_router(hybrid_router, db):
    nested_router = DefaultRouter()
    nested_router.register("items/", ItemViewSet, basename="item")

    hybrid_router.register_nested_router("nested/", nested_router)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        print("get_resolver:", resolver)

        # Assigner à la variable globale via la fonction
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier que la valeur est bien assignée
        # from .conftest import test_url_resolver

        # print("test_url_resolver après assignation:", test_url_resolver)

        response = APIClient().get("/nested/")
        assert response.status_code == status.HTTP_200_OK

        # response = APIClient().get(reverse("item"))
        # # response = APIClient().get("/nested/items/")
        # assert response.status_code == status.HTTP_200_OK


# TEST REGISTER ROOTER DIRECTK
# TEST URLS OF REGISTERED ROOTER
# TEST NO API ROOT
# TEST NO INTERMEDIRAY WIEW
# TEST INTERMEDIARY VIEW IN DIFERENT CONTEXT

# TEST ERROR WHEN SAME BASENAME
