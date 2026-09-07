import inspect

from django.urls import path
from rest_framework import filters, pagination, viewsets

from drf_spectacular.utils import extend_schema, extend_schema_view
from tests import generate_schema
from tests.models import SimpleModel, SimpleSerializer


class SyncViewset(viewsets.GenericViewSet):
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id']

    def list(self, request):
        pass  # pragma: no cover

    def create(self, request):
        pass  # pragma: no cover

    def retrieve(self, request, pk):
        pass  # pragma: no cover

    def update(self, request, pk):
        pass  # pragma: no cover

    def partial_update(self, request, pk):
        pass  # pragma: no cover

    def destroy(self, request, pk):
        pass  # pragma: no cover


# mimics the "a"-prefixed action naming convention used by async viewsets (e.g. adrf)
class AsyncViewset(viewsets.GenericViewSet):
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id']

    async def alist(self, request):
        pass  # pragma: no cover

    async def acreate(self, request):
        pass  # pragma: no cover

    async def aretrieve(self, request, pk):
        pass  # pragma: no cover

    async def aupdate(self, request, pk):
        pass  # pragma: no cover

    async def partial_aupdate(self, request, pk):
        pass  # pragma: no cover

    async def adestroy(self, request, pk):
        pass  # pragma: no cover


def build_patterns(viewset, prefix=''):
    return [
        path('x/', viewset.as_view({
            'get': f'{prefix}list',
            'post': f'{prefix}create',
        })),
        path('x/<int:pk>/', viewset.as_view({
            'get': f'{prefix}retrieve',
            'put': f'{prefix}update',
            'patch': f'partial_{prefix}update',
            'delete': f'{prefix}destroy',
        })),
    ]


def test_async_actions_generate_same_schema_as_sync_actions(no_warnings):
    sync_schema = generate_schema(None, patterns=build_patterns(SyncViewset))
    async_schema = generate_schema(None, patterns=build_patterns(AsyncViewset, prefix='a'))

    # sanity check that the list detection is actually exercised
    list_operation = sync_schema['paths']['/x/']['get']
    assert list_operation['operationId'] == 'x_list'
    assert {p['name'] for p in list_operation['parameters']} == {'limit', 'offset', 'ordering'}
    assert sync_schema['paths']['/x/']['post']['responses'].keys() == {'201'}

    assert async_schema == sync_schema


def test_extend_schema_view_on_async_actions(no_warnings):
    @extend_schema_view(
        alist=extend_schema(description='async list description'),
        aretrieve=extend_schema(description='async retrieve description'),
    )
    class XViewset(AsyncViewset):
        pass

    schema = generate_schema(None, patterns=build_patterns(XViewset, prefix='a'))
    assert schema['paths']['/x/']['get']['description'] == 'async list description'
    assert schema['paths']['/x/{id}/']['get']['description'] == 'async retrieve description'


def test_extend_schema_view_keeps_async_handlers_async(no_warnings):
    @extend_schema_view(alist=extend_schema(description='async list description'))
    class XViewset(AsyncViewset):
        pass

    # the derived method must be isolated from the parent, but stay a coroutine function
    # so that async dispatch mechanics (e.g. adrf) keep working at runtime.
    assert XViewset.alist is not AsyncViewset.alist
    assert inspect.iscoroutinefunction(XViewset.alist)
