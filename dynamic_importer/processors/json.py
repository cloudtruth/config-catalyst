from __future__ import annotations

import json
import os
from re import sub
from typing import Dict
from typing import Optional

from dynamic_importer.processors import BaseProcessor


class JSONProcessor(BaseProcessor):
    def __init__(self, default_values: str, file_path: str):
        super().__init__(default_values, file_path)
        if self.default_values:
            with open(default_values, "r") as fp:
                try:
                    self.raw_data = {"default": json.load(fp)}
                except json.JSONDecodeError:
                    raise ValueError(
                        f"Attempt to decode {default_values} as JSON failed. Is it valid JSON?"
                    )

        for dirname, dirs, files in os.walk(file_path):
            for file in files:
                current_file = os.path.join(dirname, file)
                with open(current_file, "r") as fp:
                    try:
                        self.raw_data[file] = json.load(fp)
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"Attempt to decode {current_file} as JSON failed. Is it valid JSON?"
                        )
            for dir in self.dirs_to_ignore:
                if dir in dirs:
                    dirs.remove(dir)

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        template_body = json.dumps(template, indent=4)
        if config_data:
            for _, data in config_data.items():
                if data["type"] != "string":
                    # JSON strings use double quotes
                    reference = rf'"(\\{{\\{{\s+cloudtruth.parameters.{data["param_name"]}\\s+\\}}\\}})"'
                    template_body = sub(reference, r"\1", template_body)

        return template_body
