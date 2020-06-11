from djstripe.contrib.rest_framework.serializers import (
    CreateSubscriptionSerializer, SubscriptionSerializer
)

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema


class FixDjstripeSubscriptionRestView(OpenApiViewExtension):
    target_class = 'djstripe.contrib.rest_framework.views.SubscriptionRestView'

    def view_replacement(self):
        class Fixed(self.target_class):
            serializer_class = SubscriptionSerializer

            @extend_schema(
                request=CreateSubscriptionSerializer,
                responses=CreateSubscriptionSerializer
            )
            def post(self, request, *args, **kwargs):
                pass

        return Fixed
