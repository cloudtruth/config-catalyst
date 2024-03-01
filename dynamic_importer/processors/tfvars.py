from __future__ import annotations

from re import sub
from typing import Dict
from typing import Optional

import hcl2

from dynamic_importer.processors import BaseProcessor


class TFVarsProcessor(BaseProcessor):
    def __init__(self, env_values: Dict) -> None:
        for env, file_path in env_values.items():
            try:
                with open(file_path, "r") as fp:
                    # hcl2 does not support dumping to a string/file,
                    # so we need to store the raw file for template generation
                    self.raw_file = fp.read()
                    # scroll it back
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
                value = data["values"][environment]
                reference = f'{{{{ cloudtruth.parameters.{data["param_name"]} }}}}'
                template_body = sub(value, reference, template_body)

        return template_body
