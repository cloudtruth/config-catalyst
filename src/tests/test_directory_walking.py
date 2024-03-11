from __future__ import annotations

import os
import pathlib

import pytest
from click.testing import CliRunner
from dynamic_importer.main import import_config

"""
Hey-o! Warren here. walk-directories prompts the user for information
for every file in the supplied directory to walk. Therefore, the tests
MUST supply input for the prompts. Otherwise, your tests will just
hang indefinitely.
"""


@pytest.mark.usefixtures("tmp_path")
def test_walk_directories_one_file_type(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()

    prompt_responses = [
        "",
        "myproj",
        "default",
        "",
        "",
        "development",
        "",
        "",
        "production",
        "",
        "",
        "staging",
    ]
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "walk-directories",
                "-t",
                "dotenv",
                "-c",
                f"{current_dir}/../samples/dotenvs",
                "--output-dir",
                td,
            ],
            input="\n".join(prompt_responses),
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        assert pathlib.Path(f"{td}/.env.default.ctconfig").exists()
        assert pathlib.Path(f"{td}/.env.default.cttemplate").exists()
        assert os.path.getsize(f"{td}/.env.default.ctconfig") > 0
        assert os.path.getsize(f"{td}/.env.default.cttemplate") > 0


@pytest.mark.usefixtures("tmp_path")
def test_walk_directories_multiple_file_types(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()

    prompt_responses = [
        "",
        "myproj",
        "default",
        "",
        "",
        "",
        "default",
        "",
        "",
        "",
        "default",
        "",
        "dotty",
        "default",
        "",
        "",
        "development",
        "",
        "",
        "production",
        "",
        "",
        "staging",
    ]
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(
            import_config,
            [
                "walk-directories",
                "-t",
                "dotenv",
                "-t",
                "json",
                "-c",
                f"{current_dir}/../samples",
                "--output-dir",
                td,
            ],
            input="\n".join(prompt_responses),
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        assert pathlib.Path(f"{td}/.env.default.ctconfig").exists()
        assert pathlib.Path(f"{td}/.env.default.cttemplate").exists()
        assert os.path.getsize(f"{td}/.env.default.ctconfig") > 0
        assert os.path.getsize(f"{td}/.env.default.cttemplate") > 0

        assert pathlib.Path(f"{td}/.env.ctconfig").exists()
        assert pathlib.Path(f"{td}/.env.cttemplate").exists()
        assert os.path.getsize(f"{td}/.env.ctconfig") > 0
        assert os.path.getsize(f"{td}/.env.cttemplate") > 0

        assert pathlib.Path(f"{td}/short.ctconfig").exists()
        assert pathlib.Path(f"{td}/short.cttemplate").exists()
        assert os.path.getsize(f"{td}/short.ctconfig") > 0
        assert os.path.getsize(f"{td}/short.cttemplate") > 0

        assert not pathlib.Path(f"{td}/variables.ctconfig").exists()
        assert not pathlib.Path(f"{td}/variables.cttemplate").exists()
