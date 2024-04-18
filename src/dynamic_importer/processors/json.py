# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import json
from re import sub
from typing import Dict
from typing import Optional

from dynamic_importer.processors import BaseProcessor


class JSONProcessor(BaseProcessor):
    def __init__(self, env_values: Dict) -> None:
        # Due to an unknown bug, self.parameters_and_values can persist between
        # Processor instances. Therefore, we reset it here.
        self.parameters_and_values: Dict = {}
        for env, file_path in env_values.items():
            with open(file_path, "r") as fp:
                try:
                    self.raw_data[env] = json.load(fp)
                except json.JSONDecodeError:
                    raise ValueError(
                        f"Attempt to decode {file_path} as JSON failed. Is it valid JSON?"
                    )

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        template_body = json.dumps(template, indent=4)
        if config_data:
            for _, data in config_data.items():
                try:
                    if data["type"] != "string":
                        # JSON strings use double quotes
                        reference = rf'"(\{{\{{\s+cloudtruth.parameters.{data["param_name"]}\s+\}}\}})"'
                        template_body = sub(reference, r"\1", template_body)
                except KeyError:
                    raise RuntimeError(f"data: {data}")

        return template_body
