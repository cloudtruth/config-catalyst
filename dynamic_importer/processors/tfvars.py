from re import sub
from typing import Dict
from typing import Optional

import hcl2
from dynamic_importer.processors import BaseProcessor


class TFVarsProcessor(BaseProcessor):
    def __init__(self, file_path):
        try:
            with open(file_path, "r") as fp:
                # hcl2 does not support dumping to a string/file,
                # so we need to store the raw file for template generation
                self.raw_file = fp.read()
                # scroll it back
                fp.seek(0)
                self.raw_data: Dict = hcl2.load(fp)
        except Exception as e:
            raise ValueError(f"Attempt to decode {file_path} as HCL failed: {str(e)}")

    def encode_template_references(self, template: dict, config_data: dict) -> str:
        template_body = self.raw_file
        environment = "default"
        for _, data in config_data.items():
            value = data["values"][environment]
            reference = f'{{{{ cloudtruth.parameters.{data["param_name"]} }}}}'
            template_body = sub(value, reference, template_body)

        return template_body
