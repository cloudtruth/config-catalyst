from __future__ import annotations

from unittest import TestCase

from click.testing import CliRunner
from dynamic_importer.main import import_config


class TestCLI(TestCase):
    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(import_config, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn(
            """Usage: import-config [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.
""",
            result.output,
        )

    def test_cli_process_configs(self):
        runner = CliRunner()
        result = runner.invoke(
            import_config,
            [
                "process-configs",
                "-t",
                "dotenv",
                "--default-values",
                "samples/.env.sample",
            ],
        )
        self.assertEqual(0, result.exit_code)
