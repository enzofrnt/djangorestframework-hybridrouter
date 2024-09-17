import sys


def list_urls(urlpatterns, prefix=""):
    sys.stdout.write("\n")
    for pattern in urlpatterns:
        if hasattr(pattern, "url_patterns"):  # Si c'est un include
            list_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            url = prefix + str(pattern.pattern)
            name = pattern.name if pattern.name else "None"
            sys.stdout.write(f"{url} -> {name}\n")
