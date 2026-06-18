# type: ignore
import importlib
from unittest import mock

import pytest
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.renderers import JSONRenderer

from drf_spectacular.helpers import lazy_serializer
from tests import assert_schema, generate_schema

try:
    from polymorphic.models import PolymorphicModel
except ImportError:
    class PolymorphicModel(models.Model):
        pass


@pytest.fixture(params=[
    'rest_polymorphic.serializers',
    'polymorphic.contrib.drf.serializers'
], ids=['rest_polymorphic', 'django_polymorphic_builtin'])
def polymorphic_serializer_class(request):
    """Fixture that yields PolymorphicSerializer from different modules."""
    try:
        module = importlib.import_module(request.param)
        return module.PolymorphicSerializer
    except ImportError:
        pytest.skip(f"Module {request.param} not available")


class Person(PolymorphicModel):
    address = models.CharField(max_length=30)


class LegalPerson(Person):
    company_name = models.CharField(max_length=30)
    board = models.ManyToManyField('Person', blank=True, related_name='board')


class NaturalPerson(Person):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    supervisor = models.ForeignKey('NaturalPerson', blank=True, null=True, on_delete=models.CASCADE)


class NomadicPerson(Person):
    pass


def create_serializers(polymorphic_serializer_base):
    """Factory function to create serializers with the given PolymorphicSerializer base class."""

    class PersonSerializer(polymorphic_serializer_base):
        model_serializer_mapping = {
            LegalPerson: lazy_serializer('tests.contrib.test_rest_polymorphic.LegalPersonSerializer'),
            NaturalPerson: lazy_serializer('tests.contrib.test_rest_polymorphic.NaturalPersonSerializer'),
            NomadicPerson: lazy_serializer('tests.contrib.test_rest_polymorphic.NomadicPersonSerializer'),
        }

        def to_resource_type(self, model_or_instance):
            # custom name for mapping the polymorphic models
            return model_or_instance._meta.object_name.lower().replace('person', '')

    class LegalPersonSerializer(serializers.ModelSerializer):
        # notice that introduces a recursion loop
        board = PersonSerializer(many=True, read_only=True)

        class Meta:
            model = LegalPerson
            fields = ('id', 'company_name', 'address', 'board')

    class NaturalPersonSerializer(serializers.ModelSerializer):
        # special case: PK related field pointing to a field that has 2 properties
        #  - primary_key=True
        #  - OneToOneField to base model (person_ptr_id)
        supervisor_id = serializers.PrimaryKeyRelatedField(queryset=NaturalPerson.objects.all(), allow_null=True)

        class Meta:
            model = NaturalPerson
            fields = ('id', 'first_name', 'last_name', 'address', 'supervisor_id')

    class NomadicPersonSerializer(serializers.ModelSerializer):
        # special case: all fields are read-only.
        address = serializers.CharField(max_length=30, read_only=True)

        class Meta:
            model = NomadicPerson
            fields = ('id', 'address')

    return PersonSerializer, LegalPersonSerializer, NaturalPersonSerializer, NomadicPersonSerializer


# Module-level serializer setup for lazy_serializer references
# These will be updated by each test to use the correct base class
PersonSerializer = None
LegalPersonSerializer = None
NaturalPersonSerializer = None
NomadicPersonSerializer = None


def _setup_module_serializers(polymorphic_serializer_base):
    """Set up module-level serializers for lazy_serializer references."""
    global \
        PersonSerializer, \
        LegalPersonSerializer, \
        NaturalPersonSerializer, \
        NomadicPersonSerializer
    (
        PersonSerializer,
        LegalPersonSerializer,
        NaturalPersonSerializer,
        NomadicPersonSerializer,
    ) = create_serializers(polymorphic_serializer_base)


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()

    @property
    def serializer_class(self):
        return PersonSerializer


@pytest.mark.contrib('polymorphic', 'rest_polymorphic')
def test_rest_polymorphic(no_warnings, polymorphic_serializer_class):
    _setup_module_serializers(polymorphic_serializer_class)
    assert_schema(
        generate_schema('persons', PersonViewSet),
        'tests/contrib/test_rest_polymorphic.yml'
    )


@pytest.mark.contrib('polymorphic', 'rest_polymorphic')
@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_rest_polymorphic_split_request_with_ro_serializer(no_warnings, polymorphic_serializer_class):
    _setup_module_serializers(polymorphic_serializer_class)
    schema = generate_schema('persons', PersonViewSet)
    components = schema['components']['schemas']
    assert 'NomadicPersonRequest' not in components  # All fields were read-only.
    assert 'PatchedNomadicPersonRequest' not in components  # All fields were read-only.
    assert components['Person']['oneOf'] == [
        {'$ref': '#/components/schemas/LegalPersonTyped'},
        {'$ref': '#/components/schemas/NaturalPersonTyped'},
        {'$ref': '#/components/schemas/NomadicPersonTyped'}
    ]
    assert components['Person']['discriminator']['mapping'] == {
        'legal': '#/components/schemas/LegalPersonTyped',
        'natural': '#/components/schemas/NaturalPersonTyped',
        'nomadic': '#/components/schemas/NomadicPersonTyped'
    }
    assert components['PersonRequest']['oneOf'] == [
        {'$ref': '#/components/schemas/LegalPersonTypedRequest'},
        {'$ref': '#/components/schemas/NaturalPersonTypedRequest'},
        {'$ref': '#/components/schemas/NomadicPersonTypedRequest'},
    ]
    assert components['PersonRequest']['discriminator']['mapping'] == {
        'legal': '#/components/schemas/LegalPersonTypedRequest',
        'natural': '#/components/schemas/NaturalPersonTypedRequest',
        'nomadic': '#/components/schemas/NomadicPersonTypedRequest',
    }
    assert components['NomadicPersonTypedRequest'] == {
        'properties': {'resourcetype': {'type': 'string'}},
        'required': ['resourcetype'],
        'type': 'object',
    }


@pytest.mark.contrib('polymorphic', 'rest_polymorphic')
@pytest.mark.django_db
def test_model_setup_is_valid(polymorphic_serializer_class):
    _setup_module_serializers(polymorphic_serializer_class)
    peter = NaturalPerson(first_name='Peter', last_name='Parker')
    peter.save()
    may = NaturalPerson(first_name='May', last_name='Parker')
    may.save()
    parker_inc = LegalPerson(company_name='Parker Inc', address='NYC')
    parker_inc.save()
    parker_inc.board.add(peter, may)

    spidey_corp = LegalPerson(company_name='Spidey Corp.', address='NYC')
    spidey_corp.save()
    spidey_corp.board.add(peter, parker_inc)

    JSONRenderer().render(
        PersonSerializer(spidey_corp).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
