from __future__ import annotations

import json
import os

import click
import urllib3

from dynamic_importer.api.client import CTClient
from dynamic_importer.processors import get_processor_class
from dynamic_importer.processors import get_supported_formats


@click.group()
def import_config():
    pass


@import_config.command()
@click.option(
    "-i",
    "--input-files",
    help="Full path to the file(s) to be imported. Can be a single file or a directory of files.",
)
@click.option(
    "-t",
    "--file-type",
    help=f"Type of file to process. Must be one of: {get_supported_formats()}",
)
@click.option(
    "--default-values",
    help="Full path to a file containing default values for the config data",
    default=None,
    required=False,
)
@click.option(
    "-o",
    "--output-dir",
    help="Directory to write processed output to. Default is current directory",
    default=".",
    required=False,
)
@click.option(
    "--walk-subdirs",
    help="Enables walking subdirectories when processing a directory of files",
    is_flag=True,
)
def process_configs(input_files, file_type, default_values, output_dir, walk_subdirs):
    input_files = input_files.rstrip("/")
    if default_values:
        click.echo(f"Using default values from: {default_values}")
    click.echo(f"Processing {file_type} files from: {input_files}")
    input_filename = input_files.split("/")[-1]
    if os.path.isfile(input_files):
        input_filename = ".".join(input_files.split("/")[-1].split(".")[:-1])

    processing_class = get_processor_class(file_type)
    processor = processing_class(default_values, input_files)
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


@import_config.command()
@click.option(
    "-d",
    "--data-file",
    help="Full path to config data file generated from process_file command",
)
@click.option(
    "-m",
    "--template-file",
    help="Full path to template file generated from process_file command",
)
@click.option("-p", "--project", help="CloudTruth project to import data into")
@click.option("-k", help="Ignore SSL certificate verification", is_flag=True)
@click.option("-c", help="Create missing projects and enviroments", is_flag=True)
@click.option("-u", help="Upsert values", is_flag=True)
def create_data(
    data_file, template_file, project, k, create_dependencies, upsert_values
):
    api_key = os.environ.get("CLOUDTRUTH_API_KEY") or click.prompt(
        "Enter your CloudTruth API Key", hide_input=True
    )
    if k:
        urllib3.disable_warnings()
    client = CTClient(api_key, skip_ssl_validation=k)
    with open(data_file, "r") as fp:
        config_data = json.load(fp)
        for raw_key, config_data in config_data.items():
            client.create_parameter(
                project,
                name=config_data["param_name"],
                type_str=config_data["type"],
                secret=config_data["secret"],
                create_dependencies=create_dependencies,
            )
            for env, value in config_data["values"].items():
                client.create_value(
                    project,
                    config_data["param_name"],
                    env,
                    value,
                    create_dependencies=create_dependencies,
                )
    with open(template_file, "r") as fp:
        template = fp.read()
        client.create_template(project, name=template_file, body=template)


@import_config.command()
@click.option("-i", "--input-file", help="Full path to the file to be imported")
@click.option(
    "-t",
    "--file-type",
    help=f"Type of file to process. Must be one of: {get_supported_formats()}",
)
@click.option(
    "-d",
    "--data-file",
    help="Full path to config data file generated from process_file command",
)
def regenerate_template(input_file, file_type, data_file):
    input_filename = ".".join(input_file.split("/")[-1].split(".")[:-1])
    processing_class = get_processor_class(file_type)
    config_data = {}
    with open(data_file, "r") as fp:
        config_data = json.load(fp)
    processor = processing_class(input_file)
    template, _ = processor.process(hints=config_data)

    template_out_file = f"{input_filename}.cttemplate"
    click.echo(f"Writing template to: {template_out_file}")
    with open(template_out_file, "w+") as fp:
        template_body = processor.generate_template(config_data)
        fp.write(template_body)


if __name__ == "__main__":
    import_config()
