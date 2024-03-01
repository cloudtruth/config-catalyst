from __future__ import annotations

import importlib
import os
import pkgutil
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


def get_processor_class(file_type: str) -> BaseProcessor:
    ft_lower = file_type.lower()
    if processor_module := importlib.import_module(
        f"dynamic_importer.processors.{ft_lower}"
    ):
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
    dirs_to_ignore = [
        ".git",
        ".github",
        ".vscode",
        "__pycache__",
        "venv",
        "node_modules",
        "dist",
        "build",
        "target",
    ]
    parameters_and_values: Dict = {}
    parameters = None
    raw_data: Dict = {}
    values = None
    template: Dict = {}

    def __init__(self, env_values: Dict):
        raise NotImplementedError("Subclasses must implement the __init__ method")

    def guess_type(self, value):
        """
        Guess the type of the value and return it as a string.
        NOTE: CloudTruth only supports int, bool, and str types.
              No attempt is made to determine custom types.
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        return "string"

    def path_to_param_name(self, path):
        return path.replace("[", "_").replace("]", "").replace("'", "").lstrip("_")

    def process(self, hints: Optional[Dict] = None):
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
                if path not in self.parameters_and_values:
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
                template_value, ct_data = self._traverse_data(
                    path + f"[{i}]", subnode, hints=hints
                )
                obj[i] = template_value
                params_and_values.update(ct_data)
            return obj, params_and_values
        elif isinstance(obj, dict):
            for k, v in obj.items():
                template_value, ct_data = self._traverse_data(
                    path + f"[{k}]", v, hints=hints
                )
                obj[k] = template_value
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
                        "secret": False,
                    }
                }

            if existing_data := hints.get(path):
                param_name = existing_data["param_name"]
                return f"{{{{ cloudtruth.parameters.{param_name} }}}}", existing_data

            return obj, {}
