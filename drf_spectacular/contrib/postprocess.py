import json


def camelize_result(result, generator, request, public):
    from djangorestframework_camel_case.render import CamelCaseJSONRenderer  # type: ignore

    render = CamelCaseJSONRenderer()
    result = render.render(result).decode()

    return json.loads(result)
