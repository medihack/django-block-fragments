# django-block-fragments

[![pypi](https://img.shields.io/pypi/v/django-block-fragments.svg)](https://pypi.org/project/django-block-fragments/)

Render only the content of a specific `block` of a Django template. This also works for arbitrary template inheritance or when the block is in an included template.

Rendering only a part of a template is especially useful when using Django together with libraries like HTMX, see [Template Fragments](https://htmx.org/essays/template-fragments/).

## Installation

Install with pip:

```bash
pip install django-block-fragments
```

Or with uv:

```bash
uv add django-block-fragments
```

Then add `block_fragments` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "block_fragments",
    ...,
]
```

> [!NOTE]
> `django-block-fragments` currently only supports the Django template backend.

See __Advanced configuration (below)__ for more options.

## Usage

Once installed and having a template like this:

```html
...
{% block content %}
Some content
{% endblock content %}
...
```

You can render just the "content" block in a view with:

```python
from django.shortcuts import render

def my_view(request):
    return render(request, "template.html#content", {})
```

You can also include just the "content" block in another template:

```html
{% include "template.html#content" %}
```

## Advanced configuration

By default, adding `"block_fragments"` to your `INSTALLED_APPS` will try to configure any Django template backend to use the block fragments template loader.

If you need to control this behavior, you can use the alternative `SimpleAppConfig`, which __will not__ adjust your `TEMPLATES` setting:

```python
INSTALLED_APPS = [
    "block_fragments.apps.SimpleAppConfig",
    ...,
]
```

If you use `SimpleAppConfig`, you will need to configure the template loader yourself.

A `wrap_loaders()` function is available, and can be used to configure any specific template engine instance with the block fragments loader.

You can use the backend's [`NAME`](https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-TEMPLATES-NAME) to `wrap_loaders()` to add the block fragments loader just for that backend:

```python
from block_fragments.apps import wrap_loaders

TEMPLATES = [
    ...,
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "NAME": "myname",
        "OPTIONS": {
           ...,
        },
    },
    ...,
]

wrap_loaders("myname")
```

If the `NAME` isn't provided, the penultimate element of the `BACKEND` value is used - for example, `"django.template.backends.django.DjangoTemplates"` would be equivalent to a `NAME` of `"django"`.

Under the hood, `wrap_loaders()` is equivalent to explicitly defining the `loaders` by-hand. Assuming defaults…

```python
from django.conf import settings

default_loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]
block_fragment_loaders = [("block_fragments.loader.Loader", cached_loaders)]

settings.TEMPLATES[...]['OPTIONS']['loaders'] = block_fragment_loaders
```

… where `TEMPLATES[...]` is the entry in `TEMPLATES` with the `NAME` matching
that passed to `wrap_loaders()`.

## Development

Fork, then clone the repo:

```sh
git clone git@github.com:your-username/django-block-fragments.git
```

Install dependencies (needs [uv](https://docs.astral.sh/uv/) to be installed):

```sh
uv sync
```

Then you can run the tests by using `pytest`:

```sh
uv run pytest
```

Or with coverage:

```sh
uv run pytest --cov
```

## Acknowledgements

This project is heavily inspired and uses code from [django-template-partials](https://github.com/carltongibson/django-template-partials) by Carlton Gibson and [django-render-block](https://github.com/clokep/django-render-block) by Patrick Cloke. So a big thank you to them!

## FAQ

__Why django-block-fragments when django-template-partials and django-render-block already exist?__

I was looking for a way to reuse the already existing `block` tags of the Django Template Language (like `django-render-block` does) but also wanted to have the convenience of using template loaders (like `django-template-partials` does). So `django-block-fragments` tries to combine features of both of these great projects.

__How to use `django-block-fragments` with `django-cotton`?__

When using `django-block-fragments` together with `django-cotton` the automatic loader configuration won't work (as both would overwrite each other). So you must use the `SimpleAppConfig` and configure the template loaders manually like in the example below.

```python
INSTALLED_APPS = [
    "django_cotton.apps.SimpleAppConfig",
    "block_fragments.apps.SimpleAppConfig",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "loaders": [
                (
                    "block_fragments.loader.Loader",
                    [
                        (
                            "django.template.loaders.cached.Loader",
                            [
                                "django_cotton.cotton_loader.Loader",
                                "django.template.loaders.filesystem.Loader",
                                "django.template.loaders.app_directories.Loader",
                            ],
                        )
                    ],
                )
            ],
            "context_processors": [
                # no changes
            ],
            "builtins": [
                "django_cotton.templatetags.cotton",
            ],
        },
    },
]
```

> [!NOTE]
> Because we're specifying the loaders manually, Django's APP_DIRS setting no longer has any effect. If you still want to load templates from the apps automatically, make sure to add the `django.template.loaders.app_directories.Loader` as in the example above.

## License

MIT License
