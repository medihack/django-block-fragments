from django.template import Template
from django.template.loaders import cached
from django.template.loaders.base import Loader as BaseLoader

from .template import TemplateProxy


class Loader(BaseLoader):
    """
    A template loader that tries to resolve block fragments. If no block fragment
    is requested, it falls back to the default template loader.
    """

    def __init__(self, engine, loaders):
        self.loaders = engine.get_template_loaders(loaders)
        super().__init__(engine)

    def get_dirs(self):
        for loader in self.loaders:
            if hasattr(loader, "get_dirs"):
                yield from loader.get_dirs()

    def get_contents(self, origin):
        return origin.loader.get_contents(origin)

    def get_template(self, template_name, skip=None) -> Template:
        """
        Steps:
        - Split the template_name into template_name, block_name.
        - Use self.loaders to find the template. Raise if not found.
        - If block_name is not None then check for defined block. Raise if not found.
        """
        template_base_name, _, block_name = template_name.partition("#")

        if len(self.loaders) == 1 and isinstance(self.loaders[0], cached.Loader):
            template = self.loaders[0].get_template(template_base_name, skip)
        else:
            template = super().get_template(template_base_name, skip)

        if not block_name:
            return template

        return TemplateProxy(template, block_name)

    def get_template_sources(self, template_name):
        for loader in self.loaders:
            yield from loader.get_template_sources(template_name)

    def reset(self):
        for loader in self.loaders:
            try:
                loader.reset()
            except AttributeError:
                pass
