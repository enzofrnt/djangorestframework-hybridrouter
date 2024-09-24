import django
import pytest
from django.urls import get_resolver

from .utils import list_urls

test_url_resolver = None


def recevoir_test_url_resolver(url_resolver):
    global test_url_resolver
    test_url_resolver = url_resolver


def pytest_exception_interact(node, call, report):
    global test_url_resolver  # Rendre la variable globale

    print("test_url_resolver lors de l'exception:", test_url_resolver)

    if report.failed:
        print("test_url_resolver lors de l'exception:", test_url_resolver)

        if test_url_resolver:
            all_urls = test_url_resolver
        else:
            all_urls = get_resolver().url_patterns

        def collect_urls(urlpatterns, prefix="http://localhost/"):
            urls = []
            for pattern in urlpatterns:
                if hasattr(pattern, "url_patterns"):
                    urls.extend(
                        collect_urls(
                            pattern.url_patterns, prefix + str(pattern.pattern)
                        )
                    )
                else:
                    url = prefix + str(pattern.pattern)
                    name = pattern.name if pattern.name else "None"
                    urls.append(f"{url} -> {name}")
            return urls

        urls_list = list_urls(all_urls, prefix="http://localhost/")
        # urls_list = collect_urls(all_urls)
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
