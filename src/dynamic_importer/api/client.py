# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict
from typing import Optional

import requests
from dynamic_importer.api.exceptions import ResourceNotFoundError

DEFAULT_API_HOST = "api.cloudtruth.io"
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
                f"{method} Request to {self.base_url}{path} failed with status code {resp.status_code}: {resp.text}"
            )

        return resp.json()

    def get_project(self, project_name: str) -> Dict:
        if project_name in self.cache["projects"].keys():
            return self.cache["parameters"][project_name]
        projects = self._make_request("projects", "GET")
        for project in projects["results"]:
            self.cache["projects"][project["name"]] = {
                "url": project["url"],
                "id": project["id"],
            }

        try:
            return self.cache["projects"][project_name]
        except KeyError:
            raise ResourceNotFoundError(f"Project {project_name} not found")

    def get_project_id(self, project_name: str) -> str:
        if project_name in self.cache["projects"].keys():
            return self.cache["projects"][project_name]["id"]

        return self.get_project(project_name)["id"]

    def get_project_url(self, project_name: str) -> str:
        if project_name in self.cache["projects"].keys():
            return self.cache["projects"][project_name]["url"]

        return self.get_project(project_name)["url"]

    def _populate_environment_cache(self) -> None:
        environments = self._make_request("environments", "GET")
        for environment in environments["results"]:
            self.cache["environments"][environment["name"]] = {
                "url": environment["url"],
                "id": environment["id"],
            }

    def get_environment_id(self, environment_name: str) -> str:
        if environment_name in self.cache["environments"].keys():
            return self.cache["environments"][environment_name]["id"]
        self._populate_environment_cache()

        try:
            return self.cache["environments"][environment_name]["id"]
        except KeyError:
            raise ResourceNotFoundError(f"Environment {environment_name} not found")

    def get_environment_url(self, environment_name: str) -> str:
        if environment_name in self.cache["environments"].keys():
            return self.cache["environments"][environment_name]["url"]
        self._populate_environment_cache()

        try:
            return self.cache["environments"][environment_name]["url"]
        except KeyError:
            raise ResourceNotFoundError(f"Environment {environment_name} not found")

    def get_parameter(self, project_name: str, parameter_name: str) -> Dict:
        if f"{project_name}/{parameter_name}" in self.cache["parameters"].keys():
            return self.cache["parameters"][f"{project_name}/{parameter_name}"]
        project_id = self.get_project_id(project_name)
        parameters = self._make_request(
            f"projects/{project_id}/parameters",
            "GET",
            params={"immediate_parameters": True},
        )
        for parameter in parameters["results"]:
            self.cache["parameters"][f"{project_name}/{parameter['name']}"] = {
                "url": parameter["url"],
                "id": parameter["id"],
            }
        try:
            return self.cache["parameters"][f"{project_name}/{parameter_name}"]
        except KeyError:
            raise ResourceNotFoundError(f"Parameter {parameter_name} not found")

    def get_parameter_id(self, project_name: str, parameter_name: str) -> str:
        if f"{project_name}/{parameter_name}" in self.cache["parameters"].keys():
            return self.cache["parameters"][f"{project_name}/{parameter_name}"]["id"]

        return self.get_parameter(project_name, parameter_name)["id"]

    def get_template(self, project_name: str, template_name: str) -> Dict:
        cache_key = f"{project_name}/{template_name}"
        if cached_template := self.cache["templates"].get(cache_key):
            return cached_template
        project_id = self.get_project_id(project_name)
        templates = self._make_request(f"projects/{project_id}/templates", "GET")
        for template in templates["results"]:
            self.cache["templates"][f"{project_name}/{template['name']}"] = {
                "url": template["url"],
                "id": template["id"],
            }
        try:
            return self.cache["templates"][cache_key]
        except KeyError:
            raise ResourceNotFoundError(f"Template {template_name} not found")

    def get_value(
        self, project_name: str, parameter_name: str, environment_name: str
    ) -> Dict:
        cache_key = f"{project_name}/{parameter_name}/{environment_name}"
        if cached_value := self.cache["values"].get(cache_key):
            return cached_value
        project_id = self.get_project_id(project_name)
        parameter_id = self.get_parameter_id(project_name, parameter_name)
        environment_id = self.get_environment_id(environment_name)
        values = self._make_request(
            f"projects/{project_id}/parameters/{parameter_id}/values",
            "GET",
            params={"environment": environment_id},
        )
        for value in values["results"]:
            self.cache["values"][
                f"{project_name}/{parameter_name}/{value['environment_name']}"
            ] = {
                "url": value["url"],
                "id": value["id"],
            }
        try:
            return self.cache["values"][cache_key]
        except KeyError:
            raise ResourceNotFoundError(f"Parameter {parameter_name} not found")

    def _populate_type_cache(self) -> None:
        types = self._make_request("types", "GET")
        for ct_type in types["results"]:
            self.cache["types"][ct_type["name"]] = {
                "url": ct_type["url"],
                "id": ct_type["id"],
            }

    def get_type_id(self, type_name: str) -> str:
        if type_name in self.cache["types"].keys():
            return self.cache["types"][type_name]["id"]
        self._populate_type_cache()
        try:
            return self.cache["types"][type_name]["id"]
        except KeyError:
            raise ResourceNotFoundError(f"Type {type_name} not found")

    def get_type_url(self, type_name: str) -> str:
        if type_name in self.cache["types"].keys():
            return self.cache["types"][type_name]["url"]
        self._populate_type_cache()
        try:
            return self.cache["types"][type_name]["url"]
        except KeyError:
            raise ResourceNotFoundError(f"Type {type_name} not found")

    def create_project(
        self, name: str, description: str = "", parent: Optional[str] = None
    ) -> Dict:
        req_data = {"name": name, "description": description}
        if parent:
            parent_url = self.get_project_url(parent)
            req_data["depends_on"] = parent_url

        resp = self._make_request("projects", "POST", data=req_data)
        self.cache["projects"][resp["name"]] = {"id": resp["id"], "url": resp["url"]}
        return resp

    def create_environment(
        self, name: str, description: str = "", parent_name: str = "default"
    ) -> Dict:
        parent_url = self.get_environment_url(parent_name)
        resp = self._make_request(
            "environments",
            "POST",
            data={"name": name, "description": description, "parent": parent_url},
        )
        self.cache["environments"][resp["name"]] = {
            "id": resp["id"],
            "name": resp["name"],
        }
        return resp

    def create_parameter(
        self,
        project_name: str,
        name: str,
        description: str = "",
        type_name: str = "string",
        secret: bool = False,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            project_id = self.get_project_id(project_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            project_id = self.create_project(project_name)["id"]

        resp = self._make_request(
            f"projects/{project_id}/parameters",
            "POST",
            data={
                "name": name,
                "description": description,
                "type": type_name,
                "secret": secret,
            },
        )
        self.cache["parameters"][f"{project_name}/{name}"] = {
            "url": resp["url"],
            "id": resp["id"],
        }
        return resp

    def create_template(
        self,
        project_name: str,
        name: str,
        body: str,
        description: str = "",
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            project_id = self.get_project_id(project_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            project_id = self.create_project(project_name)["id"]
        resp = self._make_request(
            f"projects/{project_id}/templates",
            "POST",
            data={"name": name, "body": body},
        )
        self.cache["templates"][f"{project_name}/{name}"] = {
            "url": resp["url"],
            "id": resp["id"],
        }
        return resp

    def create_value(
        self,
        project_name: str,
        parameter_name: str,
        environment_name: str,
        value: str,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            project_id = self.get_project_id(project_name)
            environment_id = self.get_environment_id(environment_name)
            parameter_id = self.get_parameter_id(project_name, parameter_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            project_id = self.create_project(project_name)["id"]
            environment_id = self.create_environment(environment_name)["id"]
            parameter_id = self.create_parameter(project_name, parameter_name)["id"]

        value = str(value) if isinstance(value, bool) else value
        resp = self._make_request(
            f"projects/{project_id}/parameters/{parameter_id}/values",
            "POST",
            data={"environment": environment_id, "internal_value": value},
        )
        self.cache["values"][f"{project_name}/{parameter_name}/{environment_name}"] = {
            "url": resp["url"],
            "id": resp["id"],
        }
        return resp

    def update_value(
        self,
        project_name: str,
        parameter_name: str,
        environment_name: str,
        value_id: str,
        value: str,
    ) -> Dict:
        project_id = self.get_project_id(project_name)
        environment_id = self.get_environment_id(environment_name)
        parameter_id = self.get_parameter_id(project_name, parameter_name)

        value = str(value) if isinstance(value, bool) else value
        return self._make_request(
            f"projects/{project_id}/parameters/{parameter_id}/values/{value_id}",
            "PATCH",
            data={"environment": environment_id, "internal_value": value},
        )

    def update_parameter(
        self,
        project_name: str,
        parameter_id: str,
        name: str,
        description: str = "",
        type_name: str = "string",
    ) -> Dict:
        project_id = self.get_project_id(project_name)
        return self._make_request(
            f"projects/{project_id}/parameters/{parameter_id}",
            "PATCH",
            data={
                "name": name,
                "description": description,
                "type": type_name,
            },
        )

    def update_template(
        self,
        project_name: str,
        template_id: str,
        name: str,
        body: str,
        description: str = "",
    ) -> Dict:
        project_id = self.get_project_id(project_name)
        return self._make_request(
            f"projects/{project_id}/templates/{template_id}",
            "PATCH",
            data={"name": name, "body": body},
        )

    def upsert_project(
        self,
        name: str,
        description: str = "",
        parent: Optional[str] = None,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            return self.get_project(name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            return self.create_project(name, description, parent)

    def upsert_parameter(
        self,
        project_name: str,
        name: str,
        description: str = "",
        type_name: str = "string",
        secret: bool = False,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            self.get_project_id(project_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            self.create_project(project_name)

        try:
            parameter_id = self.get_parameter_id(project_name, name)
            return self.update_parameter(
                project_name, parameter_id, name, description, type_name
            )
        except ResourceNotFoundError:
            return self.create_parameter(
                project_name, name, description, type_name, secret, create_dependencies
            )

    def upsert_template(
        self,
        project_name: str,
        name: str,
        body: str,
        description: str = "",
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            self.get_project_id(project_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            self.create_project(project_name)

        try:
            template_id = self.get_template(project_name, name)["id"]
            return self.update_template(
                project_name, template_id, name, body, description
            )
        except ResourceNotFoundError:
            return self.create_template(
                project_name, name, body, description, create_dependencies
            )

    def upsert_value(
        self,
        project_name: str,
        parameter_name: str,
        environment_name: str,
        value: str,
        create_dependencies: bool = False,
    ) -> Dict:
        try:
            self.get_project_id(project_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            self.create_project(project_name)
        try:
            self.get_environment_id(environment_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            self.create_environment(environment_name)
        try:
            self.get_parameter_id(project_name, parameter_name)
        except ResourceNotFoundError:
            if not create_dependencies:
                raise
            self.create_parameter(project_name, parameter_name)

        try:
            value_id = self.get_value(project_name, parameter_name, environment_name)[
                "id"
            ]
            return self.update_value(
                project_name, parameter_name, environment_name, value_id, value
            )
        except ResourceNotFoundError:
            return self.create_value(
                project_name,
                parameter_name,
                environment_name,
                value,
                create_dependencies,
            )
