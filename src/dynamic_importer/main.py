from __future__ import annotations

import json
import os
from collections import defaultdict
from time import time

import click
import urllib3
from dynamic_importer.api.client import CTClient
from dynamic_importer.processors import BaseProcessor
from dynamic_importer.processors import get_processor_class
from dynamic_importer.processors import get_supported_formats
from dynamic_importer.util import validate_env_values

CREATE_DATA_MSG_INTERVAL = 10
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
# mime types think .env and tf files are plain text
EXTENSIONS_TO_FILE_TYPES = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".env": "dotenv",
    ".tf": "tf",
    ".tfvars": "tfvars",
}


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
def process_configs(file_type, default_values, env_values, output_dir):
    if not default_values and not env_values:
        raise click.UsageError(
            "At least one of --default-values and --env-values must be provided"
        )
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
    processor: BaseProcessor = processing_class(input_files)
    template, config_data = processor.process()

    input_filename = ".".join(
        list(input_files.values())[0].split("/")[-1].split(".")[:-1]
    )
    template_out_file = f"{output_dir}/{input_filename}.cttemplate"
    config_out_file = f"{output_dir}/{input_filename}.ctconfig"

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
    api_key = os.environ.get("CLOUDTRUTH_API_KEY") or click.prompt(
        "Enter your CloudTruth API Key", hide_input=True
    )
    if k:
        urllib3.disable_warnings()
    client = CTClient(api_key, skip_ssl_validation=k)
    with open(data_file, "r") as fp:
        config_data = json.load(fp)
        total_params = len(config_data.values())
        click.echo(f"Creating {total_params} parameters")
        start_time = time()
        i = 0
        for raw_key, config_data in config_data.items():
            i += 1
            client.upsert_parameter(
                project,
                name=config_data["param_name"],
                type_name=config_data["type"],
                secret=config_data["secret"],
                create_dependencies=c,
            )
            for env, value in config_data["values"].items():
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
    with open(template_file, "r") as fp:
        template = fp.read()
        click.echo(f"Uploading template: {template_file}")
        client.upsert_template(project, name=template_file, body=template)

    click.echo("Data upload to CloudTruth complete!")


@import_config.command()
@click.option(
    "-c",
    "--config-dir",
    help="Full path to directory to walk and locate configs",
    required=True,
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
    "-o",
    "--output-dir",
    help="Directory to write processed output to. Default is current directory",
    default=".",
    required=False,
)
def walk_directories(config_dir, file_types, output_dir):
    walked_files = {}
    output_dir = output_dir.rstrip("/")
    for root, dirs, files in os.walk(config_dir):
        root = root.rstrip("/")
        last_project = None

        # skip over known non-config directories
        for dir in DIRS_TO_IGNORE:
            if dir in dirs:
                dirs.remove(dir)

        for file in files:
            file_path = f"{root}/{file}"
            name, file_extension = os.path.splitext(file)
            if name.startswith(".env"):
                file_extension = ".env"
            if data_type := EXTENSIONS_TO_FILE_TYPES.get(file_extension):
                confirmed_type = click.prompt(
                    f"File type {data_type} detected for {file_path}. Is this correct?",
                    type=click.Choice(get_supported_formats(), case_sensitive=False),
                    default=data_type,
                )
                if confirmed_type not in file_types:
                    click.echo(
                        f"Skipping {confirmed_type} file {file_path} as "
                        f"it is not included in the supplied file types: {', '.join(file_types)}"
                    )
                    continue
                project = click.prompt(
                    f"Enter the CloudTruth project to import {file_path} into",
                    default=last_project,
                )
                if project:
                    last_project = project
                env = click.prompt(
                    f"Enter the CloudTruth environment to import {file_path} into",
                )
                if not env:
                    env = click.prompt(
                        "Environment cannot be empty. Please enter a CloudTruth environment"
                    )
                walked_files[file_path] = {
                    "type": confirmed_type,
                    "path": file_path,
                    "project": project,
                    "environment": env,
                }

    project_files = defaultdict(lambda: defaultdict(list))
    for v in walked_files.values():
        project_files[v["project"]][v["type"]].append(
            {"path": v["path"], "environment": v["environment"]}
        )
    for project, type_info in project_files.items():
        for file_type, file_meta in type_info.items():
            env_paths = {d["environment"]: d["path"] for d in file_meta}
            input_filename = ".".join(
                list(env_paths.values())[0].split("/")[-1].split(".")[:-1]
            )
            click.echo(f"Processing {project} files: {', '.join(env_paths.values())}")
            processing_class = get_processor_class(file_type)
            processor: BaseProcessor = processing_class(env_paths)
            template, config_data = processor.process()
            template_out_file = f"{output_dir}/{input_filename}.cttemplate"
            config_out_file = f"{output_dir}/{input_filename}.ctconfig"
            click.echo(f"Writing template to: {template_out_file}")
            with open(template_out_file, "w+") as fp:
                template_body = processor.generate_template()
                fp.write(template_body)

            click.echo(f"Writing config data to: {config_out_file}")
            with open(config_out_file, "w+") as fp:
                json.dump(config_data, fp, indent=4)


if __name__ == "__main__":
    import_config()
