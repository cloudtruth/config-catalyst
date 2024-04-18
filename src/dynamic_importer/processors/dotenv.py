# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import os
from re import sub
from typing import Dict
from typing import Optional

from dotenv import dotenv_values  # type: ignore[import-not-found]
from dotenv.main import DotEnv  # type: ignore[import-not-found]
from dynamic_importer.processors import BaseProcessor


class DotEnvProcessor(BaseProcessor):
    def __init__(self, env_values: Dict) -> None:
        # Due to an unknown bug, self.parameters_and_values can persist between
        # Processor instances. Therefore, we reset it here.
        self.parameters_and_values: Dict = {}
        for env, file_path in env_values.items():
            if not os.path.isfile(file_path):
                raise ValueError(
                    f"Path to environment values file {file_path} could not be accessed."
                )
            self.raw_data[env] = dotenv_values(file_path)

    def encode_template_references(
        self, template: Dict, config_data: Optional[Dict]
    ) -> str:
        de_template = DotEnv("")
        de_template.from_dict(template)
        template_body = de_template.dumps()
        if config_data:
            for _, data in config_data.items():
                if data["type"] != "string":
                    reference = rf"(\{{\{{\s+cloudtruth.parameters.{data['param_name']}\s+\}}\}})"
                    template_body = sub(reference, r"\1", template_body)

        return template_body
