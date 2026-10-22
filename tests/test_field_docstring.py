"""A custom field class's docstring becomes its schema description.

Serializers get their OpenAPI description from their class docstring.
Fields only had help_text, so a field implemented as a subclass of a
DRF field (e.g. a ChoiceField with fixed choices) could not document
itself the same way (issue #1476).
"""
import pytest
from rest_framework import serializers, viewsets
from rest_framework.routers import SimpleRouter

from tests import generate_schema


class ColorField(serializers.ChoiceField):
    """The color to paint the widget."""

    def __init__(self, **kwargs):
        kwargs.setdefault("choices", [("r", "red"), ("g", "green")])
        super().__init__(**kwargs)


class PlainField(serializers.CharField):
    # no docstring: must not gain a description
    pass


class WidgetSerializer(serializers.Serializer):
    color = ColorField()
    name = PlainField()
    explicit = ColorField(choices=[("s", "small"), ("l", "large")], help_text="explicit help wins")


class WidgetViewSet(viewsets.ViewSet):
    serializer_class = WidgetSerializer

    def list(self, request):
        pass  # pragma: no cover


router = SimpleRouter()
router.register("widgets", WidgetViewSet, basename="widgets")
urlpatterns = router.urls


@pytest.mark.urls(__name__)
def test_field_docstring_becomes_description(no_warnings):
    schema = generate_schema("widgets", WidgetViewSet)
    props = schema["components"]["schemas"]["Widget"]["properties"]
    # the docstring is the description; the enum choices are appended
    # to it by the usual ChoiceField description handling
    assert props["color"]["description"].startswith("The color to paint the widget.")
    assert "description" not in props["name"]
    # help_text on the instance still takes precedence over the docstring
    assert props["explicit"]["description"].startswith("explicit help wins")
