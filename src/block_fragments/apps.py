"""
django-block-fragments

App configuration to set up a block fragments loader automatically.
"""

from contextlib import suppress

import django.contrib.admin
import django.template
from django.apps import AppConfig
from django.conf import settings


def wrap_loaders(name):
    for template_config in settings.TEMPLATES:
        engine_name = template_config.get("NAME")
        if not engine_name:
            engine_name = template_config["BACKEND"].split(".")[-2]
        if engine_name == name:
            loaders = template_config.setdefault("OPTIONS", {}).get("loaders", [])
            already_configured = (
                loaders
                and isinstance(loaders, (list, tuple))
                and isinstance(loaders[0], tuple)
                and loaders[0][0] == "block_fragments.loader.Loader"
            )
            if not already_configured:
                template_config.pop("APP_DIRS", None)
                default_loaders = [
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ]
                cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]
                fragment_loaders = [("block_fragments.loader.Loader", cached_loaders)]
                template_config["OPTIONS"]["loaders"] = fragment_loaders
            break

    # Force re-evaluation of settings.TEMPLATES because EngineHandler caches it.
    with suppress(AttributeError):
        del django.template.engines.templates
        django.template.engines._engines = {}


class LoaderAppConfig(AppConfig):
    """
    This, the default configuration, does the automatic setup of a partials loader.
    """

    name = "block_fragments"
    default = True

    def ready(self):
        wrap_loaders("django")


class SimpleAppConfig(AppConfig):
    """
    This, the non-default configuration, allows the user to opt-out of the automatic configuration.
    They just need to add "block_fragments.apps.SimpleAppConfig" to INSTALLED_APPS instead of
    "block_fragments".
    """

    name = "block_fragments"
