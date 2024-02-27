from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict
from typing import Optional

import requests

from dynamic_importer.api.exceptions import ResourceNotFoundError

DEFAULT_API_HOST = "api.cloudtruth.io"
# DEFAULT_API_HOST = "localhost:8000"
SUCCESS_CODES = {"get": 200, "post": 201, "patch": 200, "put": 200, "delete": 204}


class CTClient:
    def __init__(self, api_key, skip_ssl_validation=False):
        api_host = os.environ.get("CLOUDTRUTH_API_HOST", DEFAULT_API_HOST)
        self.base_url = f"https://{api_host}/api/v1"
        self.api_key = api_key
        self.headers = {"Authorization": f"Api-Key {self.api_key}"}
        self.skip_ssl_validation = skip_ssl_validation

        self.cache = defaultdict(dict)

    def _make_request(
        self,
        path: str,
        method: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        if not path.startswith("/"):
            path = f"/{path}"
        if not path.endswith("/"):
            path = f"{path}/"
        req = getattr(requests, method.lower())
        resp = req(
            f"{self.base_url}{path}",
            headers=self.headers,
            json=data,
            params=params,
            verify=not self.skip_ssl_validation,
        )
        success_code = SUCCESS_CODES[method.lower()]
        if resp.status_code != success_code:
            raise RuntimeError(
                f"Request to {self.base_url}{path} failed with status code {resp.status_code}: {resp.text}"
            )

        return resp.json()

    def get_project_id(self, project_str: str) -> str:
        if project_str in self.cache["projects"].keys():
            return self.cache["projects"][project_str]["id"]
        projects = self._make_request("projects", "GET")
        for project in projects["results"]:
            self.cache["projects"][project["name"]] = {
                "url": project["url"],
                "id": project["id"],
            }

        try:
            return self.cache["projects"][project_str]["id"]
        except KeyError:
            raise ResourceNotFoundError(f"Project {project_str} not found")

    def _populate_environment_cache(self) -> None:
        environments = self._make_request("environments", "GET")
        for environment in environments["results"]:
            self.cache["environments"][environment["name"]] = {
                "url": environment["url"],
                "id": environment["id"],
            }

    def get_environment_id(self, environment_str: str) -> str:
        if environment_str in self.cache["environments"].keys():
            return self.cache["environments"][environment_str]["id"]
        self._populate_environment_cache()

        try:
            return self.cache["environments"][environment_str]["id"]
        except KeyError:
            raise ResourceNotFoundError(f"Environment {environment_str} not found")

    def get_environment_url(self, environment_str: str) -> str:
        if environment_str in self.cache["environments"].keys():
            return self.cache["environments"][environment_str]["id"]
        self._populate_environment_cache()

        try:
            return self.cache["environments"][environment_str]["id"]
        except KeyError:
            raise ResourceNotFoundError(f"Environment {environment_str} not found")

    def get_parameter_id(self, project_str: str, parameter_str: str) -> str:
        if f"{project_str}/{parameter_str}" in self.cache["parameters"].keys():
            return self.cache["parameters"][f"{project_str}/{parameter_str}"]["id"]
        project_id = self.get_project_id(project_str)
        parameters = self._make_request(f"projects/{project_id}/parameters", "GET")
        for parameter in parameters["results"]:
            self.cache["parameters"][f"{project_str}/{parameter['name']}"] = {
                "url": parameter["url"],
                "id": parameter["id"],
            }
        try:
            return self.cache["parameters"][f"{project_str}/{parameter_str}"]["id"]
        except KeyError:
            raise ResourceNotFoundError(f"Parameter {parameter_str} not found")

    def _populate_type_cache(self) -> None:
        types = self._make_request("types", "GET")
        for ct_type in types["results"]:
            self.cache["types"][ct_type["name"]] = {
                "url": ct_type["url"],
                "id": ct_type["id"],
            }

    def get_type_id(self, type_str: str) -> str:
        if type_str in self.cache["types"].keys():
            return self.cache["types"][type_str]["id"]
        self._populate_type_cache()
        try:
            return self.cache["types"][type_str]["id"]
        except KeyError:
            raise ValueError(f"Type {type_str} not found")

    def get_type_url(self, type_str: str) -> str:
        if type_str in self.cache["types"].keys():
            return self.cache["types"][type_str]["url"]
        self._populate_type_cache()
        try:
            return self.cache["types"][type_str]["url"]
        except KeyError:
            raise ValueError(f"Type {type_str} not found")

    def create_project(self, name: str, description: str = "") -> Dict:
        return self._make_request(
            "projects", "POST", data={"name": name, "description": description}
        )

    def create_environment(self, name: str, description: str = "") -> Dict:
        return self._make_request(
            "environments", "POST", data={"name": name, "description": description}
        )

    def create_parameter(
        self,
        project_str: str,
        name: str,
        description: str = "",
        type_str: str = "string",
        secret: bool = False,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            project_id = self.get_project_id(project_str)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            project_id = self.create_project(project_str)["id"]
        return self._make_request(
            f"projects/{project_id}/parameters",
            "POST",
            data={
                "name": name,
                "description": description,
                "type": type_str,
                "secret": secret,
            },
        )

    def create_template(
        self,
        project_str: str,
        name: str,
        body: str,
        description: str = "",
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            project_id = self.get_project_id(project_str)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            project_id = self.create_project(project_str)["id"]
        return self._make_request(
            f"projects/{project_id}/templates",
            "POST",
            data={"name": name, "body": body},
        )

    def create_value(
        self,
        project_str: str,
        parameter_str: str,
        environment_str: str,
        value: str,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            project_id = self.get_project_id(project_str)
            environment_id = self.get_environment_id(environment_str)
            parameter_id = self.get_parameter_id(project_str, parameter_str)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            project_id = self.create_project(project_str)["id"]
            environment_id = self.create_environment(environment_str)["id"]
            parameter_id = self.create_parameter(project_str, parameter_str)["id"]

        value = str(value) if isinstance(value, bool) else value
        return self._make_request(
            f"projects/{project_id}/parameters/{parameter_id}/values",
            "POST",
            data={"environment": environment_id, "internal_value": value},
        )
