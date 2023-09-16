"""Helpers for unit tests."""


def query_widget(node, type_matcher, matcher=None):
    """Recursively searches the widget hierarchy for the widget."""
    if matcher is None:
        matcher = lambda c: True

    if hasattr(node, "layout"):
        if hasattr(node.layout, "display"):
            if node.layout.display == "none":
                return None
    if hasattr(node, "style"):
        if hasattr(node.style, "display"):
            if node.style.display == "none":
                return None

    children = getattr(node, "children", getattr(node, "nodes", None))
    if children is not None:
        for child in children:
            result = query_widget(child, type_matcher, matcher)
            if result:
                return result
    if isinstance(node, type_matcher) and matcher(node):
        return node
    return None
