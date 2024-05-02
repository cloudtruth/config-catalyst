# dynamic-importer
Extract parameters from your existing config and import to your CloudTruth organization

![CI](https://github.com/cloudtruth/dynamic-importer/actions/workflows/ci.yaml/badge.svg)
![Codecov](https://img.shields.io/codecov/c/github/cloudtruth/dynamic-importer)
![Docker pulls](https://img.shields.io/docker/pulls/cloudtruth/dynamic-importer)
![version](https://img.shields.io/docker/v/cloudtruth/dynamic-importer)


# Supported file types
* JSON
* YAML
* dotenv
* tfvars
* variables.tf

## Not yet supported (but planned)
* ini
* pkl

# Usage
This utility is distributed as a Docker container and can be pulled from cloudtruth/dynamic-importer on Docker Hub

## Procesing a directory tree (the easy method)
You can feed a directory of files into the `walk-directories` command, which will find all files matching the supplied types and parse them into CloudTruth config formats. If you supply your CLOUDTRUTH_API_KEY via docker, the data will be uploaded to your CloudTruth account.

```
docker run --rm -e CLOUDTRUTH_API_KEY="myverysecureS3CR3T!!" -v ${PWD}/files:/app/files cloudtruth/dynamic-importer walk-directories --config-dirs /app/samples/ -t dotenv -t json -t tf
```

## Processing a single file
An example of how to process a .env file
```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer process-configs -p myproj --default-values /app/samples/.env.sample --file-type dotenv --output-dir /app/files/
```

This command will mount a subdir `files` from the current working directory to the container. Assuming your input file is in that dir, the processed files will be placed in that dir once processing has completed.

## Processing several files
An example of how to orocess several .env files and create values for each environment
```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer process-configs \
    -p myproj -t dotenv \
    --default-values /app/samples/dotenvs/.env.default.sample \
    --env-values development:/app/samples/dotenvs/.env.dev.sample \
    --env-values staging:/app/samples/dotenvs/.env.staging.sample \
    --env-values production:/app/samples/dotenvs/.env.prod.sample \
    --output-dir /app/files/
```

## Editing template references
There may be times when this utility is too aggressive or you want a variable to remain hard-coded in your CloudTruth template. In that case, you can remove the references from the generated `.ctconfig` file and re-generate the template.

```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer regenerate-template --input-file /app/samples/.env.sample --file-type dotenv --data-file /app/files/.env.ctconfig --output-dir /app/files/
```

## Uploading data to CloudTruth
Once you are comfortable with your template and associated data, you're ready to upload to CloudTruth! Be sure to provide your CloudTruth API Key as an environment variable

```
docker run --rm -e CLOUDTRUTH_API_KEY="myverysecureS3CR3T!!" -v ${PWD}/files:/app/files cloudtruth/dynamic-importer create-data --data-file /app/files/.env.ctconfig -m /app/files/.env.cttemplate -p "Meaningful Project Name"
```

# Development
1. Set up a virtualenv
1. From your checkout of the code, `pip install -e .[dev]`

# Testing
Test code lives in `src/tests` and uses [click.testing](https://click.palletsprojects.com/en/8.1.x/testing/) as the entrypoint for all commands and processors. There are additional unit tests for the api client code, which heavily leverages mocks for the CloudTruth API. See examples in `tests.fixures.requests` for more.

To run unittests, run `pytest` from within your virtualenv.

Pre-commit is installed in this repo and should be used to verify code organization and formatting. To set it up, run `pre-commit install` in your virtualenv

# Contributing
Issues, pull requests, and discussions are welcomed. Please vote for any issues tagged with [needs votes](https://github.com/cloudtruth/dynamic-importer/issues?q=is%3Aissue+is%3Aopen+label%3A%22needs+votes%22)

See `dynamic_importer.processors` and the subclasses within for examples of the current design. TL;DR - if you can convert the source into a dict, `BaseProcessor._traverse_data` should handle most of the heavy lifting.

# Counter-examples
Because this has come up internally, this utility is intended to process config data, not application code or even raw IaC code. If you want to feed it a full Terraform manifest, you're going to get strange results. Pull your common variables into a variables.tf first!
