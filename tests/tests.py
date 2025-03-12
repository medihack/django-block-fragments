import django.template
import pytest
from django.template import EngineHandler, engines

from block_fragments.apps import wrap_loaders
from block_fragments.exceptions import BlockNotFound


@pytest.fixture
def engine():
    return engines["django"]


def test_wrap_loaders(settings):
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
        },
    ]

    django.template.engines = EngineHandler()

    outermost_loader = django.template.engines["django"].engine.loaders[0][0]
    assert outermost_loader != "block_fragments.loader.Loader"

    wrap_loaders("django")

    outermost_loader = django.template.engines["django"].engine.loaders[0][0]
    assert outermost_loader == "block_fragments.loader.Loader"


def test_block(engine):
    """Test rendering an individual block."""
    template = engine.get_template("test1.html#block1")
    assert template.render() == "block1 from test1"

    template = engine.get_template("test1.html#block2")
    assert template.render() == "block2 from test1"


def test_override(engine):
    """This block is overridden in test2."""
    template = engine.get_template("test2.html#block1")
    assert template.render() == "block1 from test2"


def test_inherit(engine):
    """This block is inherited from test1."""
    template = engine.get_template("test2.html#block2")
    assert template.render() == "block2 from test1"


def test_inherit_context(engine):
    """This block is inherited from test1."""
    template = engine.get_template("test2.html#block2")
    assert template.render({"suffix2": " blah"}) == "block2 from test1 blah"


def test_multi_inherited(engine):
    """A block from an included template should be available."""
    template = engine.get_template("test4.html#block2")
    assert template.render() == "block2 from test1"


def test_multi_inherited_context(engine):
    """A block from an included template should be available."""
    template = engine.get_template("test4.html#block2")
    assert template.render({"suffix2": " blah"}) == "block2 from test1 blah"


def test_no_block(engine):
    """Check if there's no block available an exception is raised."""
    with pytest.raises(BlockNotFound) as exc:
        template = engine.get_template("test1.html#noblock")
        template.render()

    assert str(exc.value) == "block with name 'noblock' does not exist"


def test_include(engine):
    """Ensure that an include tag in a block still works."""
    template = engine.get_template("test3.html#block1")
    assert template.render() == "included template"


def test_super(engine):
    """Test that block.super works."""
    template = engine.get_template("test3.html#block2")
    assert template.render() == "block2 from test3 - block2 from test1"


def test_multi_super(engine):
    template = engine.get_template("test6.html#block2")
    assert template.render() == "block2 from test6 - block2 from test3 - block2 from test1"


def test_super_with_same_context_on_multiple_executions(engine):
    """Test that block.super works when fed the same context twice."""
    context = {}
    template = engine.get_template("test3.html#block2")
    result_one = template.render(context)
    result_two = template.render(context)

    assert result_one == result_two
    assert result_one == "block2 from test3 - block2 from test1"


def test_subblock(engine):
    """Test that a block within a block works."""
    template = engine.get_template("test5.html#block1")
    assert template.render() == "block3 from test5"

    template = engine.get_template("test5.html#block3")
    assert template.render() == "block3 from test5"


def test_subblock_no_parent(engine):
    """
    Test that a block within a block works if the parent block is only found
    in the base template.

    This is very similar to test_subblock, but the templates differ. In this
    test the sub-template does not replace the entire block from the parent
    template.
    """
    template = engine.get_template("test_sub.html#base")
    assert template.render() == "\n\nbar\n\n"

    template = engine.get_template("test_sub.html#first")
    assert template.render() == "\nbar\n"


def test_exceptions(engine):
    with pytest.raises(Exception) as e:
        template = engine.get_template("test_exception.html#exception_block")
        template.render()

    assert str(e.value) == "Exception raised in template tag."


def test_exceptions_debug(engine, settings):
    settings.DEBUG = True
    with pytest.raises(Exception) as exc:
        template = engine.get_template("test_exception.html#exception_block")
        template.render()

    assert str(exc.value) == "Exception raised in template tag."


def test_context(engine):
    """Test that a context is properly rendered in a template."""
    data = "block2 from test5"
    template = engine.get_template("test5.html#block2")
    assert template.render({"foo": data}) == data


def test_context_autoescape_off(engine):
    """Test that the user can disable autoescape by providing a Context instance."""
    data = "&'"
    template = engine.get_template("test5.html#block2")
    autoescape = template.backend.engine.autoescape
    template.backend.engine.autoescape = False
    assert template.render({"foo": data}) == data
    template.backend.engine.autoescape = autoescape


def test_request_context(engine, rf):
    """Test that a request context data are properly rendered in a template."""
    request = rf.get("/dummy-url")
    template = engine.get_template("test_request_context.html#block1")
    assert template.render({"request": request}) == "/dummy-url"


def test_include_fragment(engine):
    """Test that an include tag works with block fragments."""
    template = engine.get_template("test7.html")
    assert template.render() == "block2 from test1"


def test_multiple_include_fragment(engine):
    """Test multiple include tags that use block fragments."""
    template = engine.get_template("test8.html")
    assert template.render() == "block1 from test1\nblock1 from test2\n"


def test_include_fragment_in_block(engine):
    """Test a block that does include a fragment."""
    template = engine.get_template("test9.html#block1")
    assert template.render() == "\nblock2 from test1\nblock1 from test9\n"
