from unittest.mock import Mock

from drf_spectacular.hooks import postprocess_exclude_non_public_endpoints


class TestPostProcessExcludeNonPublicEndpoints:
    result = {
        "paths": {
            "/some/path/": {
                "get": {"tags": ["Public", "Sign up"]},
                "patch": {"tags": ["Clean up inactive users"]}
            },
            "/internal/some/path/": {
                "get": {"tags": ["Internal"]}
            },
        }
    }

    def test_exclude_non_public_endpoints_for_anonymous_users(self):
        request = Mock(user=Mock(is_staff=False, is_authenticated=False))
        actual = postprocess_exclude_non_public_endpoints(self.result, None, request, True)
        expected = {
            "paths": {
                "/some/path/": {
                    "get": {"tags": ["Sign up"]},
                },
                "/internal/some/path/": {},
            }
        }
        assert actual == expected

    def test_exclude_non_public_endpoints_for_non_staff(self):
        user = Mock(is_staff=False)
        request = Mock(user=user)
        actual = postprocess_exclude_non_public_endpoints(self.result, None, request, True)
        expected = {
            "paths": {
                "/some/path/": {
                    "get": {"tags": ["Sign up"]},
                },
                "/internal/some/path/": {},
            }
        }
        assert actual == expected

    def test_return_all_endpoints_for_staff(self):
        request = Mock(user=Mock(is_staff=True))
        actual = postprocess_exclude_non_public_endpoints(self.result, None, request, True)
        expected = {
            "paths": {
                "/some/path/": {
                    "get": {"tags": ["Sign up"]},
                    "patch": {"tags": ["Clean up inactive users"]}
                },
                "/internal/some/path/": {
                    "get": {"tags": ["Internal"]}
                },
            }
        }
        assert actual == expected
