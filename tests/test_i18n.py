from unittest import mock

import pytest
import yaml
from django.db import models
from django.urls import include, path
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from rest_framework import __version__ as DRF_VERSION  # type: ignore[attr-defined]
from rest_framework import mixins, routers, serializers, viewsets
from rest_framework.test import APIClient

from drf_spectacular.utils import extend_schema
from drf_spectacular.validation import validate_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from tests import assert_schema, generate_schema

TRANSPORT_CHOICES = (
    ('car', _('Car')),
    ('bicycle', _('Bicycle')),
)


class I18nModel(models.Model):
    field_str = models.TextField()
    field_choice = models.CharField(max_length=10, choices=TRANSPORT_CHOICES)

    class Meta:
        verbose_name = _("Internationalization")
        verbose_name_plural = _('Internationalizations')


class XSerializer(serializers.ModelSerializer):
    class Meta:
        model = I18nModel
        fields = '__all__'


class XViewset(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    __doc__ = _("""
        More lengthy explanation of the view
    """)  # type: ignore

    serializer_class = XSerializer
    queryset = I18nModel.objects.none()

    @extend_schema(
        summary=_('Main endpoint for creating X'),
        responses=None
    )
    def create(self, request, *args, **kwargs):
        pass  # pragma: no cover


router = routers.SimpleRouter()
router.register('x', XViewset, basename='x')
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view()),
]


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.DESCRIPTION',
    _('Lazy translated description with missing translation')
)
@pytest.mark.skipif(DRF_VERSION < '3.16.1', reason='DRF updated translations')
def test_i18n_strings(no_warnings):
    with translation.override('de-de'):
        schema = generate_schema(None, patterns=urlpatterns)
        assert_schema(schema, 'tests/test_i18n.yml')


@pytest.mark.parametrize(['url', 'header', 'translated'], [
    ('/api/schema/', {}, False),
    ('/api/schema/?lang=de', {}, True),
    ('/api/schema/', {'HTTP_ACCEPT_LANGUAGE': 'de-de'}, True)
])
@pytest.mark.urls(__name__)
def test_i18n_schema(no_warnings, url, header, translated):
    response = APIClient().get(url, **header)
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)

    operation = schema['paths']['/api/x/']['post']
    if translated:
        assert 'Eine laengere Erklaerung' in operation['description']
        assert 'Hauptendpunkt fuer' in operation['summary']
        assert 'Kein Inhalt' in operation['responses']['201']['description']
    else:
        assert 'More lengthy explanation' in operation['description']
        assert 'Main endpoint' in operation['summary']
        assert 'No response body' in operation['responses']['201']['description']


@pytest.mark.urls(__name__)
def test_i18n_schema_ui(no_warnings):
    response = APIClient().get('/api/schema/swagger-ui/?lang=de')
    assert b'/api/schema/?lang\\u003Dde' in response.content


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'SpecialLanguageEnum': TRANSPORT_CHOICES
})
@pytest.mark.urls(__name__)
def test_lazily_translated_enum_overrides(no_warnings, clear_caches):
    schema_de = yaml.load(APIClient().get('/api/schema/?lang=de').content, Loader=yaml.SafeLoader)
    schema_en = yaml.load(APIClient().get('/api/schema/').content, Loader=yaml.SafeLoader)

    assert 'SpecialLanguageEnum' in schema_de['components']['schemas']
    assert 'SpecialLanguageEnum' in schema_en['components']['schemas']
