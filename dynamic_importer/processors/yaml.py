import yaml
from re import compile
from re import sub
from typing import Dict

from dynamic_importer.processors import BaseProcessor


class YAMLProcessor(BaseProcessor):
    def __init__(self, file_path):
        try:
            with open(file_path, "r") as fp:
                self.raw_data: Dict = yaml.safe_load(fp)
        except yaml.YAMLError:
            raise ValueError(
                f"Attempt to decode {file_path} as YAML failed. Is it valid YAML?"
            )

    def encode_template_references(self, template: Dict, config_data: Dict) -> str:
        template_body = yaml.safe_dump(template, width=1000)
        for _, data in config_data.items():
            if data["type"] != "string":
                # YAML strings use single quotes
                reference = (
                    f"'(\\{{\\{{\s+cloudtruth.parameters.{data['param_name']}\\s+\\}}\\}})'"
                )
                template_body = sub(compile(reference), r"\1", template_body)

        return template_body