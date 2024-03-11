from __future__ import annotations

import pathlib
from unittest import mock
from unittest import TestCase

import pytest
from click.testing import CliRunner
from dynamic_importer.main import import_config
from tests.fixtures.requests import mocked_requests_localhost_get
from tests.fixtures.requests import mocked_requests_localhost_post


class TestCLI(TestCase):
    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(import_config, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            """Usage: import-config [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.
""",
            result.output,
        )

    def test_process_configs_no_args(self):
        runner = CliRunner()
        result = runner.invoke(
            import_config, ["process-configs", "-t", "dotenv", "-p", "testproj"]
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIn(
            "Error: At least one of --default-values and --env-values must be provided",
            result.output,
        )

    def test_regenerate_template_no_args(self):
        runner = CliRunner()
        result = runner.invoke(
            import_config, ["regenerate-template", "-t", "dotenv", "-d", "test"]
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIn(
            "Error: At least one of --default-values and --env-values must be provided",
            result.output,
        )


@pytest.mark.usefixtures("tmp_path")
def test_cli_process_configs_dotenv(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "dotenv",
                "-p",
                "testproj",
                "--default-values",
                f"{current_dir}/../../samples/.env.sample",
                "--output-dir",
                td,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


@pytest.mark.usefixtures("tmp_path")
def test_cli_process_configs_json(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "json",
                "-p",
                "testproj",
                "--default-values",
                f"{current_dir}/../../samples/short.json",
                "--output-dir",
                td,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


@pytest.mark.usefixtures("tmp_path")
def test_cli_process_configs_tf(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "tf",
                "-p",
                "testproj",
                "--default-values",
                f"{current_dir}/../../samples/variables.tf",
                "--output-dir",
                td,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


@pytest.mark.usefixtures("tmp_path")
def test_cli_process_configs_tfvars(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "tfvars",
                "-p",
                "testproj",
                "--default-values",
                f"{current_dir}/../../samples/terraform.tfvars",
                "--output-dir",
                td,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


@pytest.mark.usefixtures("tmp_path")
def test_cli_process_configs_yaml(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "yaml",
                "-p",
                "testproj",
                "--default-values",
                f"{current_dir}/../../samples/azureTRE.yaml",
                "--output-dir",
                td,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        result = runner.invoke(
            import_config,
            [
                "regenerate-template",
                "-t",
                "yaml",
                "--default-values",
                f"{current_dir}/../../samples/azureTRE.yaml",
                "--data-file",
                f"{td}/testproj-yaml.ctconfig",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


@mock.patch(
    "dynamic_importer.api.client.requests.get",
    side_effect=mocked_requests_localhost_get,
)
@mock.patch(
    "dynamic_importer.api.client.requests.post",
    side_effect=mocked_requests_localhost_post,
)
@pytest.mark.usefixtures("tmp_path")
def test_cli_import_data_json(mock_get, mock_post, tmp_path):
    runner = CliRunner(
        env={"CLOUDTRUTH_API_HOST": "localhost:8000", "CLOUDTRUTH_API_KEY": "test"}
    )
    current_dir = pathlib.Path(__file__).parent.resolve()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "json",
                "-p",
                "testproj",
                "--default-values",
                f"{current_dir}/../../samples/short.json",
                "-o",
                td,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        result = runner.invoke(
            import_config,
            [
                "create-data",
                "-d",
                f"{td}/testproj-json.ctconfig",
                "-m",
                f"{td}/testproj-json.cttemplate",
                "-p",
                "testproj",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
