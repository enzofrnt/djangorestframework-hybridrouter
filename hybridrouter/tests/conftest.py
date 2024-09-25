import django
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import get_resolver

from .utils import list_urls

test_url_resolver = None


def recevoir_test_url_resolver(url_resolver):
    global test_url_resolver
    test_url_resolver = url_resolver


def pytest_exception_interact(node, call, report):
    global test_url_resolver

    print("test_url_resolver lors de l'exception:", test_url_resolver)

    if report.failed:
        print("test_url_resolver lors de l'exception:", test_url_resolver)

        if test_url_resolver:
            all_urls = test_url_resolver
        else:
            try:
                all_urls = get_resolver().url_patterns
                # Votre code ici
            except ImproperlyConfigured:
                return
            except ModuleNotFoundError as e:
                print(f"Erreur lors de l'accès au résolveur : {e}")
                return

        urls_list = list_urls(all_urls, prefix="http://localhost/")
        urls_text = "\n".join(urls_list)

        if hasattr(report, "longrepr"):
            report.longrepr = f"{report.longrepr}\n\nAvailable URLs:\n{urls_text}"


def pytest_configure():
    from django.conf import settings

    default_settings = dict(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "db.sqlite3",
                "TEST": {
                    "NAME": "db_test.sqlite3",
                },
            },
        },
        SITE_ID=1,
        SECRET_KEY="not very secret in tests",
        USE_I18N=True,
        STATIC_URL="/static/",
        ROOT_URLCONF="tests.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {
                    "debug": True,
                    "context_processors": [
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
        MIDDLEWARE=(
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ),
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "rest_framework",
            "hybridrouter.tests",
        ],
        REST_FRAMEWORK={
            "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
            "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser",),
        },
        WSGI_APPLICATION="tests.wsgi.application",
        ASGI_APPLICATION="tests.asgi.application",
        PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )

    settings.configure(**default_settings)
    django.setup()


@pytest.fixture
def hybrid_router():
    from hybridrouter.hybridrouter import HybridRouter

    return HybridRouter()
