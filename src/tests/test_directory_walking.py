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


@pytest.mark.usefixture("tmp_path")
@pytest.mark.timeout(30)
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
                f"{current_dir}/../../samples/dotenvs",
                "--output-dir",
                td,
            ],
            input="\n".join(prompt_responses),
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        assert pathlib.Path(f"{td}/myproj-dotenv.ctconfig").exists()
        assert pathlib.Path(f"{td}/myproj-dotenv.cttemplate").exists()
        assert os.path.getsize(f"{td}/myproj-dotenv.ctconfig") > 0
        assert os.path.getsize(f"{td}/myproj-dotenv.cttemplate") > 0


@pytest.mark.timeout(30)
@pytest.mark.usefixtures("tmp_path")
def test_walk_directories_multiple_file_types(tmp_path):
    runner = CliRunner()
    current_dir = pathlib.Path(__file__).parent.resolve()

    prompt_responses = [
        "",  # processing dotenv file
        "myproj",
        "default",
        "",  # skipping yaml file
        "",  # skipping json file
        "",  # skipping tfvars file
        "",  # skipping tf file
        "",  # processing dotenv dir
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
                "-c",
                f"{current_dir}/../../samples",
                "--output-dir",
                td,
            ],
            input="\n".join(prompt_responses),
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        assert pathlib.Path(f"{td}/dotty-dotenv.ctconfig").exists()
        assert pathlib.Path(f"{td}/dotty-dotenv.cttemplate").exists()
        assert os.path.getsize(f"{td}/dotty-dotenv.ctconfig") > 0
        assert os.path.getsize(f"{td}/dotty-dotenv.cttemplate") > 0

        assert pathlib.Path(f"{td}/myproj-dotenv.ctconfig").exists()
        assert pathlib.Path(f"{td}/myproj-dotenv.cttemplate").exists()
        assert os.path.getsize(f"{td}/myproj-dotenv.ctconfig") > 0
        assert os.path.getsize(f"{td}/myproj-dotenv.cttemplate") > 0

        assert not pathlib.Path(f"{td}/myproj-json.ctconfig").exists()
        assert not pathlib.Path(f"{td}/myproj-json.cttemplate").exists()
        # assert os.path.getsize(f"{td}/myproj-json.ctconfig") > 0
        # assert os.path.getsize(f"{td}/myproj-json.cttemplate") > 0

        assert not pathlib.Path(f"{td}/myproj-tf.ctconfig").exists()
        assert not pathlib.Path(f"{td}/myproj-tf.cttemplate").exists()
