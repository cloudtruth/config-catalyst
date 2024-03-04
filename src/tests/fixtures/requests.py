from __future__ import annotations


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def text(self):
            return self.json_data

    get_url = args[0]
    if get_url == "https://api.cloudtruth.io/api/v1/projects/":
        return MockResponse(
            {"results": [{"id": "1", "url": "/projects/1/", "name": "myproj"}]}, 200
        )
    elif get_url == "https://api.cloudtruth.io/api/v1/types/":
        return MockResponse(
            {"results": [{"id": "1", "url": "/types/1/", "name": "string"}]}, 200
        )
    elif get_url == "https://api.cloudtruth.io/api/v1/environments/":
        return MockResponse(
            {
                "results": [
                    {"id": "1", "url": "/environments/1/", "name": "default"},
                    {"id": "2", "url": "/environments/2/", "name": "production"},
                ]
            },
            200,
        )
    elif get_url == "https://api.cloudtruth.io/api/v1/projects/1/parameters/":
        return MockResponse(
            {
                "results": [
                    {"id": "1", "url": "/projects/1/parameters/1/", "name": "param1"}
                ]
            },
            200,
        )
    elif get_url == "https://api.cloudtruth.io/api/v1/projects/1/templates/":
        return MockResponse(
            {
                "results": [
                    {"id": "1", "url": "/projects/1/templates/1/", "name": "template1"}
                ]
            },
            200,
        )
    elif get_url == "https://api.cloudtruth.io/api/v1/projects/1/parameters/1/values/":
        return MockResponse(
            {
                "results": [
                    {
                        "id": "1",
                        "url": "/projects/1/parameters/1/values/1/",
                        "environment_name": "production",
                    }
                ]
            },
            200,
        )

    return MockResponse(None, 404)


def mocked_requests_patch(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def text(self):
            return self.json_data

    url = args[0]
    if url == "https://api.cloudtruth.io/api/v1/projects/1/":
        return MockResponse({"id": "1", "url": "/projects/1/", "name": "myproj"}, 200)
    elif url == "https://api.cloudtruth.io/api/v1/environments/2/":
        return MockResponse(
            {"id": "2", "url": "/environments/2/", "name": "production"}, 200
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/1/parameters/1/":
        return MockResponse(
            {"id": "1", "url": "/projects/1/parameters/1/", "name": "param1"}, 200
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/1/templates/1/":
        return MockResponse(
            {"id": "1", "url": "/projects/1/templates/1/", "name": "template1"}, 200
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/1/parameters/1/values/1/":
        return MockResponse(
            {
                "id": "1",
                "url": "/projects/1/parameters/1/values/1/",
                "environment_name": "production",
            },
            200,
        )

    return MockResponse(None, 404)


def mocked_requests_upsert_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def text(self):
            return self.json_data

    url = args[0]
    if url == "https://api.cloudtruth.io/api/v1/projects/":
        return MockResponse(
            {"results": [{"id": "1", "url": "/projects/1/", "name": "myproj"}]}, 200
        )
    elif url == "https://api.cloudtruth.io/api/v1/types/":
        return MockResponse(
            {"results": [{"id": "1", "url": "/types/1/", "name": "string"}]}, 200
        )
    elif url == "https://api.cloudtruth.io/api/v1/environments/":
        return MockResponse(
            {
                "results": [
                    {"id": "1", "url": "/environments/1/", "name": "default"},
                    {"id": "2", "url": "/environments/2/", "name": "production"},
                ]
            },
            200,
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/1/parameters/1/":
        return MockResponse(
            {
                "results": [
                    {"id": "1", "url": "/projects/1/parameters/1/", "name": "param1"}
                ]
            },
            200,
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/1/templates/1/":
        return MockResponse(
            {
                "results": [
                    {"id": "1", "url": "/projects/1/templates/1/", "name": "template1"}
                ]
            },
            200,
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/1/parameters/1/values/1/":
        return MockResponse(
            {
                "results": [
                    {
                        "id": "1",
                        "url": "/projects/1/parameters/1/values/1/",
                        "environment_name": "production",
                    }
                ]
            },
            200,
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/2/parameters/":
        return MockResponse({"results": []}, 200)
    elif url == "https://api.cloudtruth.io/api/v1/projects/2/templates/":
        return MockResponse({"results": []}, 200)
    elif url == "https://api.cloudtruth.io/api/v1/projects/2/parameters/2/values/":
        return MockResponse({"results": []}, 200)

    return MockResponse(None, 404)


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def text(self):
            return self.json_data

    url = args[0]
    if url == "https://api.cloudtruth.io/api/v1/projects/":
        return MockResponse(
            {"id": "2", "url": "/projects/2/", "name": kwargs["json"]["name"]}, 201
        )
    elif url == "https://api.cloudtruth.io/api/v1/types/":
        return MockResponse(
            {"id": "2", "url": "/types/2/", "name": kwargs["json"]["name"]}, 201
        )
    elif url == "https://api.cloudtruth.io/api/v1/environments/":
        return MockResponse(
            {"id": "3", "url": "/environments/3/", "name": kwargs["json"]["name"]}, 201
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/2/parameters/":
        return MockResponse(
            {
                "id": "2",
                "url": "/projects/2/parameters/2/",
                "name": kwargs["json"]["name"],
            },
            201,
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/2/templates/":
        return MockResponse(
            {
                "id": "2",
                "url": "/projects/2/templates/2/",
                "name": kwargs["json"]["name"],
            },
            201,
        )
    elif url == "https://api.cloudtruth.io/api/v1/projects/2/parameters/2/values/":
        return MockResponse(
            {
                "id": "2",
                "url": "/projects/2/parameters/2/values/2/",
                "environment_name": "production",
            },
            201,
        )

    return MockResponse(None, 404)
