# type: ignore
from unittest import mock

import pytest
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.renderers import JSONRenderer

from drf_spectacular.helpers import lazy_serializer
from tests import assert_schema, generate_schema

try:
    from polymorphic.models import PolymorphicModel
    from rest_polymorphic.serializers import PolymorphicSerializer
except ImportError:
    class PolymorphicModel(models.Model):
        pass

    class PolymorphicSerializer(serializers.Serializer):
        pass


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


class PersonSerializer(PolymorphicSerializer):
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


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@pytest.mark.contrib('polymorphic', 'rest_polymorphic')
def test_rest_polymorphic(no_warnings):
    assert_schema(
        generate_schema('persons', PersonViewSet),
        'tests/contrib/test_rest_polymorphic.yml'
    )


@pytest.mark.contrib('polymorphic', 'rest_polymorphic')
@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_rest_polymorphic_split_request_with_ro_serializer(no_warnings):
    schema = generate_schema('persons', PersonViewSet)
    components = schema['components']['schemas']
    assert 'NomadicPersonRequest' not in components  # All fields were read-only.
    assert 'PatchedNomadicPersonRequest' not in components  # All fields were read-only.
    assert components['Person']['oneOf'] == [
        {'$ref': '#/components/schemas/LegalPerson'},
        {'$ref': '#/components/schemas/NaturalPerson'},
        {'$ref': '#/components/schemas/NomadicPerson'}
    ]
    assert components['Person']['discriminator']['mapping'] == {
        'legal': '#/components/schemas/LegalPerson',
        'natural': '#/components/schemas/NaturalPerson',
        'nomadic': '#/components/schemas/NomadicPerson'
    }
    assert components['PersonRequest']['oneOf'] == [
        {'$ref': '#/components/schemas/LegalPersonRequest'},
        {'$ref': '#/components/schemas/NaturalPersonRequest'},
    ]
    assert components['PersonRequest']['discriminator']['mapping'] == {
        'legal': '#/components/schemas/LegalPersonRequest',
        'natural': '#/components/schemas/NaturalPersonRequest',
    }


@pytest.mark.contrib('polymorphic', 'rest_polymorphic')
@pytest.mark.django_db
def test_model_setup_is_valid():
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
