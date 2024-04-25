# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import pathlib
from unittest import TestCase

from dynamic_importer.processors.yaml import YAMLProcessor


class YamlTestCase(TestCase):
    def setUp(self) -> None:
        self.current_dir = pathlib.Path(__file__).parent.resolve()
        return super().setUp()

    def test_yaml_with_embedded_templates(self):
        processor = YAMLProcessor(
            {"default": f"{self.current_dir}/../../../samples/advanced/values.yaml"}
        )
        processed_template, processed_data = processor.process()

        sub_template_str = processed_template["projectMappings"]["root"]["context"][
            "resource_name"
        ]
        self.assertNotIn("'", sub_template_str)
        sub_template_str = processed_template["projectMappings"]["root"]["context"][
            "resource_namespace"
        ]
        self.assertNotIn("'", sub_template_str)
        sub_template_str = processed_template["projectMappings"]["root"][
            "resource_templates"
        ]["configmap"]
        self.assertNotIn("'", sub_template_str)

        self.assertEqual(
            processed_data["[projectMappings][root][context][resource_name]"]["type"],
            "template",
        )
        self.assertEqual(
            processed_data["[projectMappings][root][context][resource_namespace]"][
                "type"
            ],
            "template",
        )
        self.assertEqual(
            processed_data["[projectMappings][root][resource_templates][configmap]"][
                "type"
            ],
            "template",
        )

    def test_yaml_double_quoting(self):
        processor = YAMLProcessor(
            {
                "default": f"{self.current_dir}/../../../samples/advanced/app-config.yaml.hbs"
            }
        )
        _, processed_data = processor.process()
        template_str = processor.generate_template(processed_data)

        quoted_reference = "{{ cloudtruth.parameters.backend_csp_connect-src_0 }}"
        flipped_quoting_idx = template_str.find(quoted_reference)
        begin_idx = flipped_quoting_idx - 2
        end_idx = flipped_quoting_idx + len(quoted_reference) + 2
        self.assertNotIn(
            "'",
            template_str[begin_idx:end_idx],
        )
        self.assertEqual(template_str.count('"'), 2)

    def test_yaml_secret_masking(self):
        processor = YAMLProcessor(
            {"default": f"{self.current_dir}/../../../samples/advanced/values.yaml"}
        )
        processed_template, processed_data = processor.process()

        self.assertTrue(processed_data["[appSettings][apiKey]"]["secret"])
        self.assertTrue(
            processed_data["[projectMappings][root][resource_templates][secret]"][
                "secret"
            ]
        )
        # These shouldn't be true but "secret" in the name makes them marked as secrets
        # This is a limitation of the current implementation but users can manually override
        self.assertTrue(processed_data["[secret][create]"]["secret"])
        self.assertTrue(processed_data["[secret][name]"]["secret"])
