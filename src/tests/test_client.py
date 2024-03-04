from __future__ import annotations

import os
from unittest import mock
from unittest import TestCase

from dynamic_importer.api.client import CTClient
from dynamic_importer.api.client import DEFAULT_API_HOST
from dynamic_importer.api.exceptions import ResourceNotFoundError
from tests.fixtures.requests import mocked_requests_get
from tests.fixtures.requests import mocked_requests_patch
from tests.fixtures.requests import mocked_requests_post
from tests.fixtures.requests import mocked_requests_upsert_get


class TestClient(TestCase):
    def test_client_init(self):
        mock_api_key = "super-secret-api-key11!!"
        client = CTClient(mock_api_key)
        self.assertEqual(client.base_url, f"https://{DEFAULT_API_HOST}/api/v1")
        self.assertEqual(client.headers, {"Authorization": f"Api-Key {mock_api_key}"})
        self.assertEqual(client.cache, {})

    @mock.patch.dict(os.environ, {"CLOUDTRUTH_API_HOST": "localhost:8000"})
    def test_client_init_with_host_override(self):
        client = CTClient("super-secret-api-key11!!")
        self.assertEqual(client.base_url, "https://localhost:8000/api/v1")

    @mock.patch(
        "dynamic_importer.api.client.requests.get", side_effect=mocked_requests_get
    )
    def test_client_get(self, mock_get):
        client = CTClient("super-secret-api-key11!!")

        # projects
        self.assertEqual(client.get_project_id("myproj"), "1")
        self.assertEqual(mock_get.call_count, 1)
        self.assertDictEqual(
            client.cache["projects"]["myproj"], {"id": "1", "url": "/projects/1/"}
        )
        self.assertEqual(client.get_project_id("myproj"), "1")
        self.assertEqual(mock_get.call_count, 1)

        # environments
        self.assertEqual(client.get_environment_id("production"), "2")
        self.assertEqual(mock_get.call_count, 2)
        self.assertDictEqual(
            client.cache["environments"]["production"],
            {"id": "2", "url": "/environments/2/"},
        )
        self.assertEqual(client.get_environment_url("production"), "/environments/2/")
        self.assertEqual(mock_get.call_count, 2)

        # parameter
        self.assertDictEqual(
            client.get_parameter("myproj", "param1"),
            {"id": "1", "url": "/projects/1/parameters/1/"},
        )
        self.assertEqual(mock_get.call_count, 3)
        self.assertDictEqual(
            client.cache["parameters"]["myproj/param1"],
            {"id": "1", "url": "/projects/1/parameters/1/"},
        )
        self.assertEqual(client.get_parameter_id("myproj", "param1"), "1")
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(
            client.get_parameter("myproj", "param1"),
            {"id": "1", "url": "/projects/1/parameters/1/"},
        )
        self.assertEqual(mock_get.call_count, 3)

        # template
        self.assertDictEqual(
            client.get_template("myproj", "template1"),
            {"id": "1", "url": "/projects/1/templates/1/"},
        )
        self.assertEqual(mock_get.call_count, 4)
        self.assertDictEqual(
            client.cache["templates"]["myproj/template1"],
            {"id": "1", "url": "/projects/1/templates/1/"},
        )
        self.assertDictEqual(
            client.get_template("myproj", "template1"),
            {"id": "1", "url": "/projects/1/templates/1/"},
        )
        self.assertEqual(mock_get.call_count, 4)

        # values
        self.assertDictEqual(
            client.get_value("myproj", "param1", "production"),
            {"id": "1", "url": "/projects/1/parameters/1/values/1/"},
        )
        self.assertEqual(mock_get.call_count, 5)
        self.assertDictEqual(
            client.cache["values"]["myproj/param1/production"],
            {"id": "1", "url": "/projects/1/parameters/1/values/1/"},
        )
        self.assertDictEqual(
            client.get_value("myproj", "param1", "production"),
            {"id": "1", "url": "/projects/1/parameters/1/values/1/"},
        )
        self.assertEqual(mock_get.call_count, 5)

        # types
        self.assertEqual(client.get_type_id("string"), "1")
        self.assertEqual(mock_get.call_count, 6)
        self.assertDictEqual(
            client.cache["types"]["string"], {"id": "1", "url": "/types/1/"}
        )
        self.assertEqual(client.get_type_url("string"), "/types/1/")
        self.assertEqual(mock_get.call_count, 6)

        # errors
        with self.assertRaises(ResourceNotFoundError):
            client.get_project_id("invalid")
        self.assertEqual(mock_get.call_count, 7)
        with self.assertRaises(ResourceNotFoundError):
            client.get_environment_id("invalid")
        self.assertEqual(mock_get.call_count, 8)
        with self.assertRaises(ResourceNotFoundError):
            client.get_environment_url("invalid"), None
        self.assertEqual(mock_get.call_count, 9)
        with self.assertRaises(ResourceNotFoundError):
            client.get_parameter("invalid", "invalid")
        self.assertEqual(mock_get.call_count, 10)
        with self.assertRaises(ResourceNotFoundError):
            client.get_parameter_id("invalid", "invalid")
        self.assertEqual(mock_get.call_count, 11)
        with self.assertRaises(ResourceNotFoundError):
            client.get_template("invalid", "invalid")
        self.assertEqual(mock_get.call_count, 12)
        with self.assertRaises(ResourceNotFoundError):
            client.get_value("invalid", "invalid", "invalid")
        self.assertEqual(mock_get.call_count, 13)
        with self.assertRaises(ResourceNotFoundError):
            client.get_type_id("invalid")
        self.assertEqual(mock_get.call_count, 14)
        with self.assertRaises(ResourceNotFoundError):
            client.get_type_url("invalid")
        self.assertEqual(mock_get.call_count, 15)

        # generic failure
        with self.assertRaises(RuntimeError):
            client._make_request("invalid", "GET")

    @mock.patch(
        "dynamic_importer.api.client.requests.get", side_effect=mocked_requests_get
    )
    @mock.patch(
        "dynamic_importer.api.client.requests.post", side_effect=mocked_requests_post
    )
    def test_client_create(self, mock_post, mock_get):
        client = CTClient("time-to-create-the-things")
        client.create_project("myproj")
        mock_post.assert_called_once()
        client.create_environment("production")
        self.assertEqual(mock_post.call_count, 2)
        client.create_parameter("myproj", "param1")
        self.assertEqual(mock_post.call_count, 3)
        client.create_template("myproj", "template1", "wooooooooo template!")
        self.assertEqual(mock_post.call_count, 4)
        client.create_value("myproj", "param1", "production", "important value")
        self.assertEqual(mock_post.call_count, 5)

    @mock.patch(
        "dynamic_importer.api.client.requests.get",
        side_effect=mocked_requests_upsert_get,
    )
    @mock.patch(
        "dynamic_importer.api.client.requests.patch", side_effect=mocked_requests_patch
    )
    @mock.patch(
        "dynamic_importer.api.client.requests.post", side_effect=mocked_requests_post
    )
    def test_client_upsert_create_dependencies(self, mock_post, mock_patch, mock_get):
        client = CTClient("lets-get-upserting")
        client.upsert_template(
            "proj2", "template1", "wooooooooo template!", create_dependencies=True
        )
        # created project and template
        self.assertEqual(mock_post.call_count, 2)
        client.upsert_value(
            "proj3",
            "param1",
            "development",
            "important value",
            create_dependencies=True,
        )
        # created project parameter and value
        self.assertEqual(mock_post.call_count, 6)
        client.upsert_parameter("proj5", "param10", create_dependencies=True)
        self.assertEqual(mock_post.call_count, 8)

    @mock.patch(
        "dynamic_importer.api.client.requests.get", side_effect=mocked_requests_get
    )
    @mock.patch(
        "dynamic_importer.api.client.requests.patch", side_effect=mocked_requests_patch
    )
    @mock.patch(
        "dynamic_importer.api.client.requests.post", side_effect=mocked_requests_post
    )
    def test_client_upsert_no_create_dependencies(
        self, mock_post, mock_patch, mock_get
    ):
        client = CTClient("lets-get-updating")
        client.upsert_template(
            "myproj", "template1", "wooooooooo template!", create_dependencies=False
        )
        self.assertEqual(mock_patch.call_count, 1)
        client.upsert_value(
            "myproj",
            "param1",
            "production",
            "important value",
            create_dependencies=False,
        )
        self.assertEqual(mock_patch.call_count, 2)

    @mock.patch(
        "dynamic_importer.api.client.requests.get", side_effect=mocked_requests_get
    )
    def test_client_upsert_raises(self, mock_get):
        client = CTClient("time-to-error-out!")
        with self.assertRaises(ResourceNotFoundError):
            client.upsert_template(
                "proj2", "template1", "wooooooooo template!", create_dependencies=False
            )
        with self.assertRaises(ResourceNotFoundError):
            client.upsert_parameter("proj5", "param10", create_dependencies=False)
        with self.assertRaises(ResourceNotFoundError):
            client.upsert_value(
                "proj3",
                "param3",
                "development",
                "important value",
                create_dependencies=False,
            )
        with self.assertRaises(ResourceNotFoundError):
            client.upsert_value(
                "myproj",
                "param3",
                "production",
                "important value",
                create_dependencies=False,
            )
        with self.assertRaises(ResourceNotFoundError):
            client.upsert_value(
                "myproj",
                "param1",
                "development",
                "important value",
                create_dependencies=False,
            )
