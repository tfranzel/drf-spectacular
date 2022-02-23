from drf_rw_serializers.generics import GenericAPIView as RWGenericAPIView

from drf_spectacular.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    """ Utilize custom drf_rw_serializers methods for directional serializers """

    def get_request_serializer(self):
        if isinstance(self.view, RWGenericAPIView):
            return self.view.get_write_serializer_class()()
        return self._get_serializer()

    def get_response_serializers(self):
        if isinstance(self.view, RWGenericAPIView):
            return self.view.get_read_serializer_class()()
        return self._get_serializer()
