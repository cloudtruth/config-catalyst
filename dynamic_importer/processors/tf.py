from re import sub
from typing import Dict
from typing import Optional

import hcl2
from dynamic_importer.processors import BaseProcessor


class TFProcessor(BaseProcessor):
    data_keys = {"type", "default"}
    def __init__(self, file_path):
        try:
            with open(file_path, "r") as fp:
                # hcl2 does not support dumping to a string/file, 
                # so we need to store the raw file for template generation
                self.raw_file = fp.read()
                fp.seek(0)
                self.raw_data: Dict = hcl2.load(fp)
        except Exception as e:
            raise ValueError(
                f"Attempt to decode {file_path} as HCL failed: {str(e)}"
            )

    def encode_template_references(self, template: dict, config_data: dict) -> str:
        template_body = self.raw_file
        environment = "default"
        for _, data in config_data.items():
            value = data["values"][environment]
            reference = (
                f'{{{{ cloudtruth.parameters.{data["param_name"]} }}}}'
            )
            template_body = sub(value, reference, template_body)

        return template_body
    
    # TODO: override self._traverse_data to only process 'default' from raw_data
    def _traverse_data(self, path: str, obj: Dict, hints: Optional[Dict] = None) -> dict:
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
            if set(obj.keys()) >= self.data_keys:
                if not hints:
                    param_name = self.path_to_param_name(path)
                    return f"{{{{ cloudtruth.parameters.{param_name} }}}}", {
                        path: {
                            "values": {"default": obj["default"]},
                            "param_name": param_name,
                            "description": obj.get("description", ""),
                            "type": obj["type"],
                            "secret": obj.get("sensitive", False),
                        }
                    }

                if existing_data := hints.get(path):
                    param_name = existing_data["param_name"]
                    return f"{{{{ cloudtruth.parameters.{param_name} }}}}", existing_data

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
                        "values": {"default": obj},
                        "param_name": param_name,
                        "type": obj_type,
                        "secret": False,
                    }
                }

            if existing_data := hints.get(path):
                param_name = existing_data["param_name"]
                return f"{{{{ cloudtruth.parameters.{param_name} }}}}", existing_data

            return obj, {}