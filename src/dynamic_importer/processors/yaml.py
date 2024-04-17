from __future__ import annotations

from re import sub
from typing import Dict
from typing import Optional

import yaml
from dynamic_importer.processors import BaseProcessor
from liquid import Environment


class YAMLProcessor(BaseProcessor):
    def __init__(self, env_values: Dict) -> None:
        # Due to an unknown bug, self.parameters_and_values can persist between
        # Processor instances. Therefore, we reset it here.
        self.parameters_and_values: Dict = {}
        for env, file_path in env_values.items():
            try:
                with open(file_path, "r") as fp:
                    self.raw_data[env] = yaml.safe_load(fp)
            except yaml.YAMLError:
                raise ValueError(
                    f"Attempt to decode {file_path} as YAML failed. Is it valid YAML?"
                )

    def guess_type(self, value):
        base_type = super().guess_type(value)
        if base_type == "string":
            try:
                template = Environment().from_string(value)
                analysis = template.analyze()
                if analysis.variables:
                    return "template"
            except Exception:
                pass

        return base_type

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        template_body = yaml.safe_dump(template, width=1000)
        if config_data:
            for _, data in config_data.items():
                if data["type"] != "string":
                    # YAML strings use single quotes
                    reference = rf"'(\{{\{{\s+cloudtruth.parameters.{data['param_name']}\s+\}}\}})'"
                    template_body = sub(reference, r"\1", template_body)
                default_value = data.get("values", {}).get("default")
                if default_value and data["type"] == "string":
                    if default_value.startswith("'") and default_value.endswith("'"):
                        reference = rf"'(\{{\{{\s+cloudtruth.parameters.{data['param_name']}\s+\}}\}})'"
                        template_body = sub(reference, r'"\1"', template_body)

        return template_body
