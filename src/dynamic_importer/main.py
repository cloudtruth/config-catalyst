# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import json
import os
from collections import defaultdict
from time import time
from typing import Dict

import click
import urllib3
from dynamic_importer.api.client import CTClient
from dynamic_importer.api.types import coerce_types
from dynamic_importer.processors import BaseProcessor
from dynamic_importer.processors import get_processor_class
from dynamic_importer.processors import get_supported_formats
from dynamic_importer.util import validate_env_values
from dynamic_importer.walker import walk_files

CREATE_DATA_MSG_INTERVAL = 20
DIRS_TO_IGNORE = [
    ".git",
    ".github",
    ".vscode",
    "__pycache__",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
]


@click.group()
def import_config():
    pass


@import_config.command()
@click.option(
    "-t",
    "--file-type",
    type=click.Choice(get_supported_formats(), case_sensitive=False),
    help=f"Type of file to process. Must be one of: {get_supported_formats()}",
    required=True,
)
@click.option(
    "--default-values",
    help="Full path to a file containing default values for the config data",
    default=None,
    required=False,
)
@click.option(
    "--env-values",
    help="Full path to a file containing environment specific values for the config data. "
    + "Should be in the format of `env:file_path`",
    multiple=True,
    required=False,
    callback=validate_env_values,
)
@click.option(
    "-o",
    "--output-dir",
    help="Directory to write processed output to. Default is current directory",
    default=".",
    required=False,
)
@click.option(
    "--parse-descriptions",
    help="Detect comments in the input file and use them for parameter descriptions",
    is_flag=True,
)
@click.option(
    "-p", "--project", help="CloudTruth project to import data into", required=True
)
def process_configs(
    file_type, default_values, env_values, output_dir, parse_descriptions, project
):
    if not default_values and not env_values:
        raise click.UsageError(
            "At least one of --default-values and --env-values must be provided"
        )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = {}
    if default_values:
        click.echo(f"Using default values from: {default_values}")
        input_files["default"] = default_values
    for env_value in env_values:
        env, file_path = env_value.split(":")
        click.echo(f"Using {env}-specific values from: {file_path}")
        input_files[env] = file_path
    click.echo(f"Processing {file_type} files from: {', '.join(input_files)}")
    processing_class = get_processor_class(file_type)
    processor: BaseProcessor = processing_class(
        input_files, should_parse_description=parse_descriptions
    )
    template, config_data = processor.process()

    template_out_file = f"{output_dir}/{project}-{file_type}.cttemplate"
    config_out_file = f"{output_dir}/{project}-{file_type}.ctconfig"

    click.echo(f"Writing template to: {template_out_file}")
    with open(template_out_file, "w+") as fp:
        template_body = processor.generate_template()
        fp.write(template_body)

    click.echo(f"Writing config data to: {config_out_file}")
    with open(config_out_file, "w+") as fp:
        json.dump(config_data, fp, indent=4)


@import_config.command()
@click.option(
    "--default-values",
    help="Full path to a file containing default values for the config data",
    default=None,
    required=False,
)
@click.option(
    "--env-values",
    help="Full path to a file containing environment specific values for the config data. "
    + "Should be in the format of `env:file_path`",
    multiple=True,
    required=False,
    callback=validate_env_values,
)
@click.option(
    "-t",
    "--file-type",
    help=f"Type of file to process. Must be one of: {get_supported_formats()}",
    required=True,
)
@click.option(
    "-d",
    "--data-file",
    help="Full path to config data file generated from process_configs command",
    required=True,
)
def regenerate_template(default_values, env_values, file_type, data_file):
    if not default_values and not env_values:
        raise click.UsageError(
            "At least one of --default-values and --env-values must be provided"
        )

    output_dir = os.path.dirname(data_file) or "."
    input_files = {}
    if default_values:
        click.echo(f"Using default values from: {default_values}")
        input_files["default"] = default_values
    for env_value in env_values:
        env, file_path = env_value.split(":")
        click.echo(f"Using {env}-specific values from: {file_path}")
        input_files[env] = file_path
    click.echo(f"Processing {file_type} files from: {', '.join(input_files)}")

    config_data = {}
    with open(data_file, "r") as fp:
        config_data = json.load(fp)

    processing_class = get_processor_class(file_type)
    processor: BaseProcessor = processing_class(input_files)
    template, _ = processor.process(hints=config_data)

    input_filename = ".".join(
        list(input_files.values())[0].split("/")[-1].split(".")[:-1]
    )
    template_out_file = f"{output_dir}/{input_filename}.cttemplate"
    click.echo(f"Writing template to: {template_out_file}")
    with open(template_out_file, "w+") as fp:
        template_body = processor.generate_template(config_data)
        fp.write(template_body)


@import_config.command()
@click.option(
    "-d",
    "--data-file",
    help="Full path to config data file generated from process_configs command",
    required=True,
)
@click.option(
    "-m",
    "--template-file",
    help="Full path to template file generated from process_configs command",
    required=True,
)
@click.option(
    "-p", "--project", help="CloudTruth project to import data into", required=True
)
@click.option("-k", help="Ignore SSL certificate verification", is_flag=True)
@click.option("-c", help="Create missing projects and enviroments", is_flag=True)
@click.option("-u", help="Upsert values", is_flag=True)
def create_data(data_file, template_file, project, k, c, u):
    with open(data_file, "r") as dfp, open(template_file, "r") as tfp:
        config_data = json.load(dfp)
        template_data = tfp.read()
    _create_data(config_data, str(template_file), template_data, project, k, c, u)

    click.echo("Data upload to CloudTruth complete!")


def _create_data(
    config_data: Dict,
    template_name: str,
    template_data: str,
    project: str,
    k: bool,
    c: bool,
    u: bool,
):
    api_key = os.environ.get("CLOUDTRUTH_API_KEY")
    if not api_key:
        raise click.UsageError(
            "CLOUDTRUTH_API_KEY environment variable is required. "
            "Please visit https://app.cloudtruth.io/organization/api to generate one."
        )
    if k:
        urllib3.disable_warnings()
    client = CTClient(api_key, skip_ssl_validation=k)

    if "/" in project:
        parent_project, project = project.split("/", 1)
        client.upsert_project(project, parent=parent_project, create_dependencies=c)

    total_params = len(config_data.values())
    click.echo(f"Creating {total_params} parameters")
    start_time = time()
    i = 0
    for _, config_data in config_data.items():
        i += 1
        type_name = coerce_types(config_data["type"])
        client.upsert_parameter(
            project,
            name=config_data["param_name"],
            type_name=type_name,
            secret=config_data["secret"],
            create_dependencies=c,
        )
        for env, value in config_data["values"].items():
            if value:
                client.upsert_value(
                    project,
                    config_data["param_name"],
                    env,
                    value,
                    create_dependencies=c,
                )
        cur_time = time()
        if cur_time - start_time > CREATE_DATA_MSG_INTERVAL:
            click.echo(f"Created {i} parameters, {total_params - i} remaining")
            start_time = time()
    click.echo(f"Uploading template: {template_name}")
    client.upsert_template(project, name=template_name, body=template_data)


@import_config.command()
@click.option(
    "--config-dirs",
    help="Full path to directory to walk and locate configs",
    required=True,
    multiple=True,
)
@click.option(
    "-t",
    "--file-types",
    type=click.Choice(get_supported_formats(), case_sensitive=False),
    help=f"Type of file to process. Must be one of: {get_supported_formats()}",
    required=True,
    multiple=True,
)
@click.option(
    "--exclude-dirs",
    help="Directory to exclude from walking. Can be specified multiple times",
    multiple=True,
)
@click.option(
    "--create-hierarchy",
    help="If specified, project hierarchy will be created based on directory hierarchy",
    is_flag=True,
)
@click.option(
    "--parse-descriptions",
    help="Detect comments in the input file and use them for parameter descriptions",
    is_flag=True,
)
@click.option("-k", help="Ignore SSL certificate verification", is_flag=True)
@click.option("-c", help="Create missing projects and enviroments", is_flag=True)
@click.option("-u", help="Upsert values", is_flag=True)
def walk_directories(
    config_dirs, file_types, exclude_dirs, create_hierarchy, parse_descriptions, k, c, u
):
    """
    Walks a directory, constructs templates and config data, and uploads to CloudTruth.
    This is an interactive version of the process_configs and create_data commands. The
    user will be prompted for project and environment names as files are walked.
    """
    walked_files = {}
    for config_dir in config_dirs:
        for root, dirs, files in os.walk(config_dir):
            root = root.rstrip("/")

            # skip over known non-config directories
            for dir in DIRS_TO_IGNORE:
                if dir in dirs:
                    dirs.remove(dir)

            # skip over user-specified non-config directories
            for dir in exclude_dirs:
                dir = dir.rstrip("/")
                if os.path.abspath(dir) in [
                    f"{os.path.abspath(root)}/{d}" for d in dirs
                ]:
                    click.echo(f"Excluding directory: {os.path.abspath(dir)}")
                    dirs.remove(os.path.basename(dir))

            walked_files.update(walk_files(root, files, file_types, create_hierarchy))

    project_files = defaultdict(lambda: defaultdict(list))
    for v in walked_files.values():
        project_files[v["project"]][v["type"]].append(
            {"path": v["path"], "environment": v["environment"]}
        )

    processed_data = defaultdict(dict)
    for project, type_info in project_files.items():
        for file_type, file_meta in type_info.items():
            env_paths = {d["environment"]: d["path"] for d in file_meta}

            click.echo(f"Processing {project} files: {', '.join(env_paths.values())}")
            processing_class = get_processor_class(file_type)
            processor: BaseProcessor = processing_class(
                env_paths, should_parse_description=parse_descriptions
            )
            template, config_data = processor.process()

            template_name = f"{project}-{file_type}.cttemplate"
            template_body = processor.generate_template()

            processed_data[project][template_name] = {
                "template_body": template_body,
                "config_data": config_data,
            }

    for project, ct_data in processed_data.items():
        click.echo(f"Uploading data for {project}")
        for template_name, template_data in ct_data.items():
            template_body = template_data["template_body"]
            config_data = template_data["config_data"]
            _create_data(config_data, template_name, template_body, project, k, c, u)
    click.echo("Data upload to CloudTruth complete!")


if __name__ == "__main__":
    import_config()
