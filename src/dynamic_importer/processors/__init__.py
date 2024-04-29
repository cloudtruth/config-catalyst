# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import importlib
import os
import pkgutil
import re
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

RE_WORDS = "(pas+wo?r?d|pass(phrase)?|pwd|token|secrete?|api(\\W|_)?key)"
RE_CANDIDATES = re.compile("(^{0}$|_{0}_|^{0}_|_{0}$)".format(RE_WORDS), re.IGNORECASE)


def get_processor_class(file_type: str) -> BaseProcessor:
    ft_lower = file_type.lower()
    try:
        processor_module = importlib.import_module(
            f"dynamic_importer.processors.{ft_lower}"
        )
    except ModuleNotFoundError:
        raise ValueError(f"No processor found for file type: {file_type}")

    for subclass in BaseProcessor.__subclasses__():
        if subclass.__name__.lower() == f"{ft_lower}processor":
            return getattr(processor_module, subclass.__name__)

    raise ValueError(f"No processor found for file type: {file_type}")


def get_supported_formats() -> List[str]:
    for module_loader, name, ispkg in pkgutil.iter_modules([os.path.dirname(__file__)]):
        importlib.import_module("." + name, __package__)
    return [
        c.__name__.removesuffix("Processor").lower()
        for c in BaseProcessor.__subclasses__()
    ]


class BaseProcessor:
    default_values = None
    parameters = None
    parameters_and_values: Dict = {}
    raw_data: Dict = {}
    should_parse_description = False
    template: Dict = {}
    values = None

    def __init__(
        self, env_values: Dict, should_parse_description: bool = False
    ) -> None:
        raise NotImplementedError("Subclasses must implement the __init__ method")

    def is_param_secret(self, param_name: str) -> bool:
        return bool(RE_CANDIDATES.search(param_name))

    def guess_type(self, value):
        """
        Guess the type of the value and return it as a string.
        NOTE: CloudTruth only supports int, bool, and str types.
              No attempt is made to determine custom types.
        """
        if value is None:
            # We don't want to coerce null to a string
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        return "string"

    def path_to_param_name(self, path):
        return path.replace("[", "_").replace("]", "").replace("'", "").lstrip("_")

    def process(
        self, hints: Optional[Dict] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.extract_parameters_and_values(hints)
        return self.template, self.parameters_and_values

    def extract_parameters_and_values(self, hints: Optional[Dict] = None) -> None:
        self.template = deepcopy(self.raw_data["default"])
        for env, data in self.raw_data.items():
            template, environment_values = self._traverse_data(
                "", data, env, hints=hints
            )
            self.template.update(template)

            for path, config_data in environment_values.items():
                if path not in self.parameters_and_values.keys():
                    self.parameters_and_values[path] = config_data
                else:
                    self.parameters_and_values[path]["values"].update(
                        config_data["values"]
                    )

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        raise NotImplementedError(
            "Subclasses must implement the encode_template_references method"
        )

    def generate_template(self, hints: Optional[Dict] = None):
        hints = hints or self.parameters_and_values
        return self.encode_template_references(self.template, hints)

    def _parse_description(self, obj: Union[List, Dict], value: Any) -> Optional[str]:
        return None

    def _traverse_data(
        self,
        path: str,
        obj: Union[List, Dict, str],
        env: Optional[str] = "default",
        hints: Optional[Dict] = None,
    ) -> Tuple[Any, Dict]:
        """
        Traverse obj recursively and construct every path / value pair.

        Inspired by: https://github.com/jabbalaci/JSON-path/blob/master/jsonpath.py
        """
        params_and_values = {}
        if isinstance(obj, list):
            for i, subnode in enumerate(obj):
                sub_path = path + f"[{i}]"
                template_value, ct_data = self._traverse_data(
                    sub_path, subnode, env, hints=hints
                )
                obj[i] = template_value

                if sub_path in ct_data and self.should_parse_description:
                    ct_data[sub_path]["description"] = self._parse_description(obj, i)
                params_and_values.update(ct_data)
            return obj, params_and_values
        elif isinstance(obj, dict):
            for k, v in obj.items():
                sub_path = path + f"[{k}]"
                template_value, ct_data = self._traverse_data(
                    sub_path, v, env, hints=hints
                )
                obj[k] = template_value

                if sub_path in ct_data and self.should_parse_description:
                    ct_data[sub_path]["description"] = self._parse_description(obj, k)
                params_and_values.update(ct_data)
            return obj, params_and_values
        else:
            if not hints:
                obj_type = self.guess_type(obj)
                param_name = self.path_to_param_name(path)
                return f"{{{{ cloudtruth.parameters.{param_name} }}}}", {
                    path: {
                        "values": {env: obj},
                        "param_name": param_name,
                        "type": obj_type,
                        "secret": self.is_param_secret(param_name),
                    }
                }

            if existing_data := hints.get(path):
                param_name = existing_data["param_name"]
                return f"{{{{ cloudtruth.parameters.{param_name} }}}}", existing_data

            return obj, {}
