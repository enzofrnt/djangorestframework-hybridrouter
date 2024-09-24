import types

import pytest
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
def test_register_views_and_viewsets(hybrid_router, db):
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

        # Vérifier que les vues fonctionnent correctement
        client = APIClient()
        response = client.get(view_url)
        assert response.status_code == status.HTTP_200_OK

        Item.objects.create(id=1, name="Test Item", description="Item for testing.")

        response = client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK


@override_settings()
def test_register_only_views(hybrid_router, db):
    # Enregistrer uniquement des vues simples
    hybrid_router.register("simple-view", ItemView, basename="simple-view")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier que l'URL est correctement générée
        view_url = reverse("simple-view")
        assert view_url == "/simple-view/"

        # Vérifier que la vue fonctionne correctement
        client = APIClient()
        response = client.get(view_url)
        assert response.status_code == status.HTTP_200_OK


@override_settings()
def test_register_only_viewsets(hybrid_router, db):
    # Enregistrer uniquement des ViewSets
    hybrid_router.register("items", ItemViewSet, basename="item")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier que les URLs du ViewSet fonctionnent
        list_url = reverse("item-list")
        detail_url = reverse("item-detail", kwargs={"pk": 1})

        assert list_url == "/items/"
        assert detail_url == "/items/1/"

        # Créer un item pour le test
        Item.objects.create(id=1, name="Test Item", description="Item for testing.")

        client = APIClient()
        response = client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK


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
        Item.objects.create(name="unique-name", description="Item with unique name.")

        # Vérifier que l'URL utilise le champ de recherche personnalisé
        detail_url = reverse("slug-item-detail", kwargs={"name": "unique-name"})
        assert detail_url == "/slug-items/unique-name/"

        client = APIClient()
        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK


def test_api_root_view(hybrid_router, db):
    # include_root_view est True par défaut
    hybrid_router.register("items", ItemViewSet, basename="item")
    hybrid_router.register("users", ItemViewSet, basename="user")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        response = APIClient().get("/")
        assert response.status_code == status.HTTP_200_OK
        expected_data = {
            "items": "http://testserver/items/",
            "users": "http://testserver/users/",
        }
        assert response.json() == expected_data


def test_no_api_root_view(hybrid_router, db):
    hybrid_router.include_root_view = False

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        response = APIClient().get("/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_intermediary_view(hybrid_router, db):
    hybrid_router.include_intermediate_views = True  # Par défaut True

    hybrid_router.register("items/1/", ItemView, basename="item_1")
    hybrid_router.register("items/2/", ItemView, basename="item_2")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        client = APIClient()

        response = client.get("/items/1/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/items/2/")
        assert response.status_code == status.HTTP_200_OK

        # La vue intermédiaire est-elle disponible ?
        response = client.get("/items/")
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

        client = APIClient()

        response = client.get("/items/1/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/items/2/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/items/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_intermediary_view_multiple_levels(hybrid_router, db):
    hybrid_router.include_intermediate_views = True

    hybrid_router.register("level1/level2/level3/", ItemView, basename="item-deep")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        client = APIClient()

        response = client.get("/level1/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/level1/level2/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/level1/level2/level3/")
        assert response.status_code == status.HTTP_200_OK


def test_no_intermediary_view_multiple_levels(hybrid_router, db):
    hybrid_router.include_intermediate_views = False

    hybrid_router.register("level1/level2/level3/", ItemView, basename="item-deep")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        client = APIClient()

        response = client.get("/level1/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = client.get("/level1/level2/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = client.get("/level1/level2/level3/")
        assert response.status_code == status.HTTP_200_OK


def test_intermediary_view_with_only_viewsets(hybrid_router, db):
    hybrid_router.include_intermediate_views = True

    hybrid_router.register("items", ItemViewSet, basename="item")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        client = APIClient()

        response = client.get("/items/")
        assert response.status_code == status.HTTP_200_OK

        # Créer un item pour le test
        Item.objects.create(id=1, name="Test Item", description="Item for testing.")

        detail_url = reverse("item-detail", kwargs={"pk": 1})
        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK


def test_register_nested_router(hybrid_router, db):
    nested_router = DefaultRouter()
    nested_router.register("items", ItemViewSet, basename="item")

    hybrid_router.register_nested_router("nested/", nested_router)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        client = APIClient()

        response = client.get("/nested/items/")
        assert response.status_code == status.HTTP_200_OK


def test_register_router_directly(hybrid_router, db):
    nested_router = DefaultRouter()
    nested_router.register("items", ItemViewSet, basename="item")

    # Enregistrer le routeur imbriqué directement
    hybrid_router.register_nested_router("nested/", nested_router)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        client = APIClient()

        response = client.get("/nested/items/")
        assert response.status_code == status.HTTP_200_OK


def test_nested_router_url_patterns(hybrid_router, db):
    nested_router = DefaultRouter()
    nested_router.register("items", ItemViewSet, basename="item")

    hybrid_router.register_nested_router("api/v1/", nested_router)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        list_url = reverse("item-list")
        assert list_url == "/api/v1/items/"

        response = APIClient().get("/api/v1/items/")
        assert response.status_code == status.HTTP_200_OK


def test_no_basename_provided(hybrid_router):
    # Enregistrer un ViewSet sans fournir de basename
    hybrid_router.register("items", ItemViewSet)
    # Le basename par défaut devrait être 'item'

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Essayer de renverser les noms d'URL en utilisant le basename par défaut
        list_url = reverse("item-list")
        assert list_url == "/items/"


def test_no_basename_provided_multiple(hybrid_router):
    # Enregistrer plusieurs ViewSets sans basename
    hybrid_router.register("items1", ItemViewSet)
    hybrid_router.register("items2", ItemViewSet)
    hybrid_router.register("items3", ItemViewSet)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        list_url1 = reverse("item_1-list")
        list_url2 = reverse("item_2-list")
        list_url3 = reverse("item_3-list")

        assert list_url1 == "/items1/"
        assert list_url2 == "/items2/"
        assert list_url3 == "/items3/"


def test_no_basename_conflict(hybrid_router):
    # Enregistrer deux ViewSets de la même classe sans basename
    hybrid_router.register("items1", ItemViewSet)
    hybrid_router.register("items2", ItemViewSet)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Les basenames par défaut seront les mêmes, il devrait y avoir un conflit résolu
        list_url1 = reverse("item_1-list")
        list_url2 = reverse("item_2-list")
        assert list_url1 == "/items1/"
        assert list_url2 == "/items2/"


def test_same_basename_warning(hybrid_router, caplog):
    hybrid_router.register("items1", ItemViewSet, basename="item")
    hybrid_router.register("items2", ItemViewSet, basename="item")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier qu'un avertissement a été enregistré
        warnings = [
            record for record in caplog.records if record.levelname == "WARNING"
        ]
        assert len(warnings) >= 1
        assert (
            "The basename 'item' is used for multiple registrations"
            in warnings[0].message
        )

        # Vérifier que des basenames uniques ont été assignés
        list_url1 = reverse("item_1-list")
        list_url2 = reverse("item_2-list")
        assert list_url1 == "/items1/"
        assert list_url2 == "/items2/"


def test_same_basename_error(hybrid_router, caplog):
    # Enregistrer deux ViewSets avec le même basename explicitement
    hybrid_router.register("items1", ItemViewSet, basename="item")
    hybrid_router.register("items2", ItemViewSet, basename="item")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # Vérifier qu'un avertissement a été enregistré
        warnings_list = [
            record for record in caplog.records if record.levelname == "WARNING"
        ]
        assert len(warnings_list) >= 1
        assert (
            "The basename 'item' is used for multiple registrations"
            in warnings_list[0].message
        )

        # Vérifier que des basenames uniques ont été assignés
        list_url1 = reverse("item_1-list")
        list_url2 = reverse("item_2-list")
        assert list_url1 == "/items1/"
        assert list_url2 == "/items2/"


def test_register_with_trailing_slash_in_prefix(hybrid_router, db):
    hybrid_router.register("items/", ItemViewSet, basename="item")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        list_url = reverse("item-list")
        assert list_url == "/items/"

        # Essayer d'accéder à l'URL
        response = APIClient().get("/items/")
        assert response.status_code == status.HTTP_200_OK


def test_custom_trailing_slash(hybrid_router, db):
    # Définir trailing_slash sur une chaîne vide
    hybrid_router.trailing_slash = ""

    hybrid_router.register("items", ItemViewSet, basename="item")

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        list_url = reverse("item-list")
        assert list_url == "/items"

        # Essayer d'accéder à l'URL
        response = APIClient().get("/items")
        assert response.status_code == status.HTTP_200_OK


def test_intermediate_view_with_nested_router(hybrid_router, db):
    hybrid_router.include_intermediate_views = True

    nested_router = DefaultRouter()
    nested_router.register("subitems", ItemViewSet, basename="subitem")

    hybrid_router.register_nested_router("items/", nested_router)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # La vue intermédiaire 'items/' devrait être disponible
        response = APIClient().get("/items/")
        assert response.status_code == status.HTTP_200_OK

        # Les URLs du routeur imbriqué devraient être accessibles
        response = APIClient().get("/items/subitems/")
        assert response.status_code == status.HTTP_200_OK


def test_no_intermediate_view_with_nested_router(hybrid_router, db):
    hybrid_router.include_intermediate_views = False

    nested_router = DefaultRouter()
    nested_router.include_root_view = (
        False  # Important pour éviter la vue intermédiaire
    )
    nested_router.register("subitems", ItemViewSet, basename="subitem")

    hybrid_router.register_nested_router("items/", nested_router)

    urlconf = create_urlconf(hybrid_router)

    with override_settings(ROOT_URLCONF=urlconf):
        resolver = get_resolver(urlconf)
        recevoir_test_url_resolver(resolver.url_patterns)

        # La vue intermédiaire 'items/' ne devrait pas être disponible
        response = APIClient().get("/items/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Les URLs du routeur imbriqué devraient être accessibles
        response = APIClient().get("/items/subitems/")
        assert response.status_code == status.HTTP_200_OK
