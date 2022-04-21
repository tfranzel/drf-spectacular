from docutils.nodes import Text
from sphinx.util import logging


logger = logging.getLogger(__name__)


def setup(app):
    app.add_role("default-role-error", default_role_error)
    return {"parallel_read_safe": True}


# Inspired by equivalent code in Django's Sphinx extension.
# https://github.com/django/django/blob/6b53114d/docs/_ext/djangodocs.py#L393
def default_role_error(
    name, rawtext, text, lineno, inliner, options=None, content=None
):
    logger.warning(
        (
            f"Default role used (`single backticks`): {rawtext}. Did you mean to use "
            "two backticks for ``code``, or miss an underscore for a `link`_ ?"
        ),
        location=(inliner.document.current_source, lineno),
    )
    return [Text(text)], []
