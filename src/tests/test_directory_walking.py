# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import os
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

This gets even more confusing when running the tests in GitHub Actions.
Somehow, the order of the files processed differs between local and
GitHub. Therefore, you may have to re-order the prompt responses depending
on the running environment.

If you run into this issue, you can simulate the GitHub Actions environment
by running the docker container and executing the tests there.

```shell
docker run -it --entrypoint /bin/bash --rm -v $PWD:/app cloudtruth/config-catalyst:latest
pip install -e .[dev]
IS_GITHUB_ACTION=true pytest
```
"""
IS_GITHUB_ACTION = os.environ.get("IS_GITHUB_ACTION")


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
            "--config-dirs",
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

    local_prompt_responses = [
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
        "",  # skipping advanced/yaml
    ]

    github_prompt_responses = [
        "",  # processing dotenv file
        "myproj",
        "default",
        "",  # skipping yaml file
        "",  # skipping json file
        "",  # skipping tfvars file
        "",  # skipping tf file
        "",  # skipping advanced/yaml
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

    result = runner.invoke(
        import_config,
        [
            "walk-directories",
            "-t",
            "dotenv",
            "--config-dirs",
            f"{current_dir}/../../samples",
        ],
        input="\n".join(
            github_prompt_responses if IS_GITHUB_ACTION else local_prompt_responses
        ),
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
            "--config-dirs",
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


@mock.patch(
    "dynamic_importer.main.CTClient",
)
@pytest.mark.timeout(30)
def test_walk_directories_with_inheritance(mock_client):
    mock_client = mock.MagicMock()  # noqa: F841
    runner = CliRunner(
        env={"CLOUDTRUTH_API_HOST": "localhost:8000", "CLOUDTRUTH_API_KEY": "test"},
    )
    current_dir = pathlib.Path(__file__).parent.resolve()

    prompt_responses = [
        "",  # processing dotenv file
        "",  # accept default project
        "default",
        "",  # processing yaml file
        "",  # using myproj default
        "default",  # use default environment
        "",  # skipping json file
        "",  # skipping tfvars file
        "",  # skipping tf file
        "",  # enter samples/dotenvs
        "",  # accept default project
        "default",  # use default environment
        "",  # processing dotenv file
        "",  # accept default project
        "development",  # use development environment
        "",  # processing dotenv file
        "",  # accept default project
        "production",  # use production environment
        "",  # processing dotenv file
        "",  # accept default project
        "staging",  # use staging environment
        "",  # enter samples/advanced
        "",  # accept default project
        "default",  # use default environment
    ]
    result = runner.invoke(
        import_config,
        [
            "walk-directories",
            "-t",
            "yaml",
            "--create-hierarchy",
            "-c",
            "--config-dirs",
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
