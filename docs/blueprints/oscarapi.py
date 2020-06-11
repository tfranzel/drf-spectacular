from rest_framework import serializers

from drf_spectacular.extensions import (
    OpenApiSerializerExtension, OpenApiSerializerFieldExtension, OpenApiViewExtension
)
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field


class Fix1(OpenApiViewExtension):
    target_class = 'oscarapi.views.root.api_root'

    def view_replacement(self):
        return extend_schema(responses=OpenApiTypes.OBJECT)(self.target_class)


class Fix2(OpenApiViewExtension):
    target_class = 'oscarapi.views.product.ProductAvailability'

    def view_replacement(self):
        from oscarapi.serializers.product import AvailabilitySerializer

        class Fixed(self.target_class):
            serializer_class = AvailabilitySerializer
        return Fixed


class Fix3(OpenApiViewExtension):
    target_class = 'oscarapi.views.product.ProductPrice'

    def view_replacement(self):
        from oscarapi.serializers.checkout import PriceSerializer

        class Fixed(self.target_class):
            serializer_class = PriceSerializer
        return Fixed


class Fix4(OpenApiViewExtension):
    target_class = 'oscarapi.views.checkout.UserAddressDetail'

    def view_replacement(self):
        from oscar.apps.address.models import UserAddress

        class Fixed(self.target_class):
            queryset = UserAddress.objects.none()
        return Fixed


class Fix5(OpenApiViewExtension):
    target_class = 'oscarapi.views.product.CategoryList'

    def view_replacement(self):
        class Fixed(self.target_class):
            @extend_schema(parameters=[
                OpenApiParameter(name='breadcrumbs', type=OpenApiTypes.STR, location=OpenApiParameter.PATH)
            ])
            def get(self, request, *args, **kwargs):
                pass

        return Fixed


class Fix6(OpenApiSerializerExtension):
    target_class = 'oscarapi.serializers.checkout.OrderSerializer'

    def map_serializer(self, auto_schema, direction):
        from oscarapi.serializers.checkout import OrderOfferDiscountSerializer, OrderVoucherOfferSerializer

        class Fixed(self.target_class):
            @extend_schema_field(OrderOfferDiscountSerializer(many=True))
            def get_offer_discounts(self):
                pass

            @extend_schema_field(OpenApiTypes.URI)
            def get_payment_url(self):
                pass

            @extend_schema_field(OrderVoucherOfferSerializer(many=True))
            def get_voucher_discounts(self):
                pass

        return auto_schema._map_serializer(Fixed, direction)


class Fix7(OpenApiSerializerFieldExtension):
    target_class = 'oscarapi.serializers.fields.CategoryField'

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class Fix8(OpenApiSerializerFieldExtension):
    target_class = 'oscarapi.serializers.fields.AttributeValueField'

    def map_serializer_field(self, auto_schema, direction):
        return {
            'oneOf': [
                build_basic_type(OpenApiTypes.STR),
            ]
        }


class Fix9(OpenApiSerializerExtension):
    target_class = 'oscarapi.serializers.basket.BasketSerializer'

    def map_serializer(self, auto_schema, direction):
        class Fixed(self.target_class):
            is_tax_known = serializers.SerializerMethodField()

            def get_is_tax_known(self) -> bool:
                pass

        return auto_schema._map_serializer(Fixed, direction)


class Fix10(Fix9):
    target_class = 'oscarapi.serializers.basket.BasketLineSerializer'
