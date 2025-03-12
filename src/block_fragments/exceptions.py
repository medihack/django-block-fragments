from django.template.base import TemplateSyntaxError


class BlockNotFound(TemplateSyntaxError):
    """The expected block was not found."""
