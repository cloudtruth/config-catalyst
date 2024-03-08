from __future__ import annotations

import os
from re import sub
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import hcl2
from dynamic_importer.processors import BaseProcessor


class TFProcessor(BaseProcessor):
    data_keys = {"type", "default"}

    def __init__(self, env_values: Dict) -> None:
        # Due to an unknown bug, self.parameters_and_values can persist between
        # Processor instances. Therefore, we reset it here.
        self.parameters_and_values: Dict = {}
        for env, file_path in env_values.items():
            if not os.path.isfile(file_path):
                raise ValueError(
                    f"Path to environment values file {file_path} could not be accessed."
                )
            try:
                with open(file_path, "r") as fp:
                    # hcl2 does not support dumping to a string/file,
                    # so we need to store the raw file for template generation
                    self.raw_file = fp.read()
                    fp.seek(0)
                    self.raw_data[env] = hcl2.load(fp)
            except Exception as e:
                raise ValueError(
                    f"Attempt to decode {file_path} as HCL failed: {str(e)}"
                )

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        template_body = self.raw_file
        environment = "default"
        if config_data:
            for _, data in config_data.items():
                value = str(data["values"][environment])
                reference = f'{{{{ cloudtruth.parameters.{data["param_name"]} }}}}'
                template_body = sub(value, reference, template_body)

        return template_body

    def _traverse_data(
        self,
        path: str,
        obj: Union[Dict, List, str],
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
                    path + f"[{i}]", subnode, env, hints=hints
                )
                obj[i] = template_value
                params_and_values.update(ct_data)
            return obj, params_and_values
        elif isinstance(obj, dict):
            if set(obj.keys()) >= self.data_keys:
                if not hints:
                    param_name = self.path_to_param_name(path)
                    return f"{{{{ cloudtruth.parameters.{param_name} }}}}", {
                        path: {
                            "values": {env: obj["default"]},
                            "param_name": param_name,
                            "description": obj.get("description", ""),
                            "type": obj["type"],
                            "secret": obj.get("sensitive", False),
                        }
                    }

                if existing_data := hints.get(path):
                    param_name = existing_data["param_name"]
                    return (
                        f"{{{{ cloudtruth.parameters.{param_name} }}}}",
                        existing_data,
                    )

            for k, v in obj.items():
                template_value, ct_data = self._traverse_data(
                    path + f"[{k}]", v, env, hints=hints
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
