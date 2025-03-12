from copy import copy

from django.template import Context, Template
from django.template.context import RenderContext
from django.template.loader_tags import BLOCK_CONTEXT_KEY, BlockContext, BlockNode, ExtendsNode

from block_fragments.exceptions import BlockNotFound


class TemplateProxy(Template):
    """
    A template wrapper that renders a specific block from a Django template.
    """

    def __init__(self, template, block_name):
        self.template = template
        self.block_name = block_name

        self.name = template.name
        self.origin = template.origin
        self.engine = template.engine
        self.source = template.source

    def render(self, context):
        "Display stage -- can be called many times"

        # Make a copy of the context and reset the rendering state.
        # Trying to re-use a RenderContext in multiple renders can
        # lead to TemplateNotFound errors, as Django will skip past
        # any template files it thinks it has already rendered in a
        # template's inheritance stack.
        context_instance = copy(context)
        context_instance.render_context = RenderContext()

        with context_instance.render_context.push_state(self):
            if context_instance.template is None:
                with context_instance.bind_template(self):
                    context.template_name = self.name
                    return self._render(context_instance)
            else:
                return self._render(context_instance)

    def _render(self, context):
        # Before trying to render the template, we need to traverse the tree of
        # parent templates and find all blocks in them.
        self._build_block_context(self.template, context)

        return self._render_template_block(context)

    def _build_block_context(self, template: Template, context: Context) -> None:
        """
        Populate the block context with BlockNodes from this template and parent templates.
        """

        # Ensure there's a BlockContext before rendering. This allows blocks in
        # ExtendsNodes to be found by sub-templates (allowing {{ block.super }} and
        # overriding sub-blocks to work).
        if BLOCK_CONTEXT_KEY not in context.render_context:
            context.render_context[BLOCK_CONTEXT_KEY] = BlockContext()
        block_context = context.render_context[BLOCK_CONTEXT_KEY]

        # Add the template's blocks to the context.
        block_context.add_blocks(
            {n.name: n for n in template.nodelist.get_nodes_by_type(BlockNode)}
        )

        # Check parent nodes (there should only ever be 0 or 1).
        for node in template.nodelist.get_nodes_by_type(ExtendsNode):
            parent = node.get_parent(context)

            # Recurse and search for blocks from the parent.
            self._build_block_context(parent, context)

    def _render_template_block(self, context):
        """Renders a single block from a template."""
        block_node = context.render_context[BLOCK_CONTEXT_KEY].get_block(self.block_name)

        if block_node is None:
            # The wanted block_name was not found.
            raise BlockNotFound("block with name '%s' does not exist" % self.block_name)

        return block_node.render(context)
