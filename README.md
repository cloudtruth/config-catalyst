![Logo for Config Catalyst by CloudTruth](https://github.com/cloudtruth/config-catalyst/blob/main/docs/img/repo-logo.png?raw=true)

# Config Catalyst

![CI](https://github.com/cloudtruth/config-catalyst/actions/workflows/ci.yaml/badge.svg)
![Codecov](https://img.shields.io/codecov/c/github/cloudtruth/config-catalyst)
![Docker pulls](https://img.shields.io/docker/pulls/cloudtruth/config-catalyst)
![version](https://img.shields.io/docker/v/cloudtruth/config-catalyst)

Config Catalyst automatically converts static config files in your repos into parameterized templates.
It's the easiest way to "pay down config tech debt" with a single command.

We :heart: feedback, [bugs](https://github.com/cloudtruth/config-catalyst/issues/new), and [enhancement suggestions](https://github.com/cloudtruth/config-catalyst/issues/new). 

We also have a #config-catalyst channel [on our Discord](https://discord.com/invite/eBZXm9Tzr7).

# Motivation
Config Catalyst exists to solve this problem:

"I need to take this weird network config that Bob (who left five years ago) roughed out by hand and turn it into a crisp little YAML template with parameterized variables."
Static, hard-coded config is a form of "tech debt" many teams want to eliminate, but the "pay it down" process is tedious and time consuming.

# How it works
Config Catalyst works off of a local copy of your repo folder structure.
1. Scans your repos and finds all the configuration files (JSON, YAML, ENV, HCL, TF_Var, etc..)
1. Automatically creates parameterized templates with linked parameters and secrets to the parameter/secret store.
1. Result: Finally, parameter and secret changes can be reflected in all the config files that use/depend on them.

You don't need to build all the plumbing anymore. Config file changes are independent of param/secret variable changes.

Need to manage values across multiple environments with one template? No problem!

Bonus: The variables and secrets can optionally be synced to Azure Key Vault, AWS Secrets Manager, ParameterStore, or Vault.

# Features and supported file types

**Current file type support includes**:
* JSON
* YAML
* dotenv
* tfvars
* variables.tf

**Not yet supported (but planned)**
* ini
* pkl

# Installation
This utility is distributed as a Docker container and can be pulled from cloudtruth/config-catalyst on Docker Hub

Clone your repo(s) to local disk to allow Config Catalyst to find the supported file types.

To complete the process, you will need a CloudTruth [API token](https://app.cloudtruth.io/organization/api).

To get an API token, use your existing account or create a free [CloudTruth account](https://app.cloudtruth.io/signup).

# Usage

## Processing a directory tree (the easy method)
You can feed a directory of files into the `walk-directories` command, which will find all files matching the supplied types and parse them into CloudTruth config formats. If you supply your CLOUDTRUTH_API_KEY via docker, the data will be uploaded to your CloudTruth account.

```
docker run --rm -it -e CLOUDTRUTH_API_KEY="myverysecureS3CR3T!!" -v ${PWD}/files:/app/files cloudtruth/config-catalyst walk-directories --config-dirs /app/samples/ -t dotenv -t json -t tf
```

## Processing a single file
An example of how to process a .env file. This example assumes you have one .env file in the current directory that will be mounted through to the container

```
docker run --rm -v ${PWD}:/app/files cloudtruth/config-catalyst walk-directories --config-dirs /app/files/ --file-type dotenv --output-dir /app/files/
```

# Advanced Usage
These examples break down the directory walking method into its individual components.

## Processing several files
An example of how to process several .env files and create values for each environment
```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/config-catalyst process-configs \
    -p myproj -t dotenv \
    --default-values /app/samples/dotenvs/.env.default.sample \
    --env-values development:/app/samples/dotenvs/.env.dev.sample \
    --env-values staging:/app/samples/dotenvs/.env.staging.sample \
    --env-values production:/app/samples/dotenvs/.env.prod.sample \
    --output-dir /app/files/
```

## Editing template references
Sometimes this utility is too aggressive or you want a variable to remain hard-coded in your CloudTruth template. In that case, you can remove the references from the generated `.ctconfig` file and re-generate the template.

```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/config-catalyst regenerate-template --input-file /app/samples/.env.sample --file-type dotenv --data-file /app/files/.env.ctconfig --output-dir /app/files/
```

## Uploading data to CloudTruth
Once you are comfortable with your template and associated data, you're ready to upload to CloudTruth! Be sure to provide your CloudTruth API Key as an environment variable

```
docker run --rm -e CLOUDTRUTH_API_KEY="myverysecureS3CR3T!!" -v ${PWD}/files:/app/files cloudtruth/config-catalyst create-data --data-file /app/files/.env.ctconfig -m /app/files/.env.cttemplate -p "Meaningful Project Name"
```

# Development
1. Set up a virtualenv
1. From your checkout of the code, `pip install -e .[dev]`

# Testing
Test code lives in `src/tests` and uses [click.testing](https://click.palletsprojects.com/en/8.1.x/testing/) as the entrypoint for all commands and processors. There are additional unit tests for the api client code, which heavily leverages mocks for the CloudTruth API. See examples in `tests.fixures.requests` for more.

To run unittests, run `pytest` from within your virtualenv.

Pre-commit is installed in this repo and should be used to verify code organization and formatting. To set it up, run `pre-commit install` in your virtualenv

# Contributing
Issues, pull requests, and discussions are welcomed. Please vote for any issues tagged with [needs votes](https://github.com/cloudtruth/config-catalyst/issues?q=is%3Aissue+is%3Aopen+label%3A%22needs+votes%22)

See `dynamic_importer.processors` and the subclasses within for examples of the current design. TL;DR - if you can convert the source into a dict, `BaseProcessor._traverse_data` should handle most of the heavy lifting.

# Further reading
CloudTruth [documentation](https://docs.cloudtruth.com/)
