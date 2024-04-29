# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

from re import sub
from typing import Any
from typing import Dict
from typing import Optional

from dynamic_importer.processors import BaseProcessor
from dynamic_importer.util import StringableYAML
from liquid import Environment
from ruamel.yaml import YAMLError

yaml = StringableYAML()


class YAMLProcessor(BaseProcessor):
    def __init__(
        self, env_values: Dict, should_parse_description: bool = False
    ) -> None:
        self.should_parse_description = should_parse_description
        # Due to an unknown bug, self.parameters_and_values can persist between
        # Processor instances. Therefore, we reset it here.
        self.parameters_and_values: Dict = {}
        for env, file_path in env_values.items():
            try:
                with open(file_path, "r") as fp:
                    self.raw_data[env] = yaml.load(fp)
            except YAMLError:
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

    def _parse_description(self, obj: Any, value: Any) -> str | None:
        comment_strings = []
        if comments := obj.ca.items.get(value, None):
            for c in comments:
                if c and not isinstance(c, list) and c.value:
                    comment_strings.append(c.value.lstrip().strip().lstrip("# "))
            return "\n".join(comment_strings)

        return None

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        template_body = yaml.dump(template, stream=None)
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
