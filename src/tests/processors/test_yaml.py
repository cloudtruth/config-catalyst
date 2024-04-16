from __future__ import annotations

import pathlib
from unittest import TestCase

from dynamic_importer.processors.yaml import YAMLProcessor


class YamlTestCase(TestCase):
    def test_yaml_with_embedded_templates(self):
        current_dir = pathlib.Path(__file__).parent.resolve()
        processor = YAMLProcessor(
            {"default": f"{current_dir}/../../../samples/advanced/values.yaml"}
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
        current_dir = pathlib.Path(__file__).parent.resolve()
        processor = YAMLProcessor(
            {"default": f"{current_dir}/../../../samples/advanced/app-config.yaml.hbs"}
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
