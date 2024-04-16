from __future__ import annotations

import pathlib
from unittest import mock

import pytest
from click.testing import CliRunner
from dynamic_importer.main import import_config

"""
Hey-o! Warren here. walk-directories prompts the user for information
for every file in the supplied directory to walk. Therefore, the tests
MUST supply input for the prompts. If you write a test that supplies
prompt input, please use the `@pytest.mark.timeout(30)` decorator to
avoid hanging indefinitely.
"""


@mock.patch(
    "dynamic_importer.main.CTClient",
)
@pytest.mark.timeout(30)
def test_walk_directories_one_file_type(mock_client):
    mock_client = mock.MagicMock()  # noqa: F841
    runner = CliRunner(
        env={"CLOUDTRUTH_API_HOST": "localhost:8000", "CLOUDTRUTH_API_KEY": "test"}
    )
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
    result = runner.invoke(
        import_config,
        [
            "walk-directories",
            "-t",
            "dotenv",
            "--config-dir",
            f"{current_dir}/../../samples/dotenvs",
            "-c",
            "-u",
            "-k",
        ],
        input="\n".join(prompt_responses),
        catch_exceptions=False,
    )
    try:
        assert result.exit_code == 0
    except AssertionError as e:
        print(result.output)
        raise e


@mock.patch(
    "dynamic_importer.main.CTClient",
)
@pytest.mark.timeout(30)
def test_walk_directories_multiple_file_types(mock_client):
    mock_client = mock.MagicMock()  # noqa: F841
    runner = CliRunner(
        env={"CLOUDTRUTH_API_HOST": "localhost:8000", "CLOUDTRUTH_API_KEY": "test"}
    )
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
        "",
        "",
        "",
        "",
    ]
    result = runner.invoke(
        import_config,
        [
            "walk-directories",
            "-t",
            "dotenv",
            "--config-dir",
            f"{current_dir}/../../samples",
        ],
        input="\n".join(prompt_responses),
        catch_exceptions=False,
    )
    try:
        assert result.exit_code == 0
    except AssertionError as e:
        print(result.output)
        raise e


@mock.patch(
    "dynamic_importer.main.CTClient",
)
@pytest.mark.timeout(30)
def test_walk_directories_with_exclusion(mock_client):
    mock_client = mock.MagicMock()  # noqa: F841
    runner = CliRunner(
        env={"CLOUDTRUTH_API_HOST": "localhost:8000", "CLOUDTRUTH_API_KEY": "test"},
    )
    current_dir = pathlib.Path(__file__).parent.resolve()

    prompt_responses = [
        "",  # processing dotenv file
        "myproj",
        "default",
        "",  # processing yaml file
        "",  # using myproj default
        "default",  # use default environment
        "",  # skipping json file
        "",  # skipping tfvars file
        "",  # skipping tf file
        # something is different between local and github file order
        # so we have to specify this extra prompt response and
        # tack on a few extra empty lines
        "default",
        "",
        "",
        "",
    ]
    result = runner.invoke(
        import_config,
        [
            "walk-directories",
            "-t",
            "dotenv",
            "-t",
            "yaml",
            "--config-dir",
            f"{current_dir}/../../samples",
            "--exclude-dirs",
            f"{current_dir}/../../samples/dotenvs",
            "--exclude-dirs",
            f"{current_dir}/../../samples/advanced",
        ],
        input="\n".join(prompt_responses),
        catch_exceptions=False,
    )
    try:
        assert result.exit_code == 0
    except AssertionError as e:
        print(result.output)
        raise e
