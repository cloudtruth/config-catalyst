from re import compile
from re import sub
from typing import Dict

from dotenv import dotenv_values
from dotenv.main import DotEnv

from dynamic_importer.processors import BaseProcessor


class DotEnvProcessor(BaseProcessor):
    def __init__(self, file_path):
        self.raw_data: Dict = dotenv_values(file_path)

    def encode_template_references(self, template: dict, config_data: dict) -> str:
        de_template = DotEnv("")
        de_template.from_dict(template)
        template_body = de_template.dumps()
        for _, data in config_data.items():
            if data["type"] != "string":
                reference = f"(\\{{\\{{\s+cloudtruth.parameters.{data['param_name']}\\s+\\}}\\}})"
                template_body = sub(compile(reference), r"\1", template_body)

        return template_body
