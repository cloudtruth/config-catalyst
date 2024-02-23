import json
from re import compile
from re import sub
from typing import Dict

from dynamic_importer.processors import BaseProcessor


class JSONProcessor(BaseProcessor):
    def __init__(self, file_path):
        try:
            with open(file_path, "r") as fp:
                self.raw_data: Dict = json.load(fp)
        except json.JSONDecodeError:
            raise ValueError(
                f"Attempt to decode {file_path} as JSON failed. Is it valid JSON?"
            )

    def encode_template_references(self, template: dict, config_data: dict) -> str:
        template_body = json.dumps(template, indent=4)
        for _, data in config_data.items():
            if data["type"] != "string":
                # JSON strings use double quotes
                reference = f'"(\\{{\\{{\s+cloudtruth.parameters.{data["param_name"]}\\s+\\}}\\}})"'
                template_body = sub(compile(reference), r"\1", template_body)

        return template_body
