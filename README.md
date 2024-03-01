# dynamic-importer
Extract parameters from your existing config and import to your CloudTruth organization

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

## Processing a single file
An example of how to process a .env file
```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer process-configs --default-values /app/dynamic_importer/samples/.env.sample --file-type dotenv --output-dir /app/files/
```

This command will mount a subdir `files` from the current working directory to the container. Assuming your input file is in that dir, the processed files will be placed in that dir once processing has completed.

## Processing several files
An example of how to orocess several .env files and create values for each environment
```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer process-configs -t dotenv \
    --default-values /app/dynamic_importer/samples/dotenvs/.env.default.sample \
    --env-values development:/app/dynamic_importer/samples/dotenvs/.env.dev.sample \
    --env-values staging:/app/dynamic_importer/samples/dotenvs/.env.staging.sample \
    --env-values production:/app/dynamic_importer/samples/dotenvs/.env.prod.sample \
    --output-dir /app/files/
```


## Editing template references
There may be times when this utility is too aggressive or you want a variable to remain hard-coded in your CloudTruth template. In that case, you can remove the references from the generated `.ctconfig` file and re-generate the template.

```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer regenerate-template --input-file /app/dynamic_importer/samples/.env.sample --file-type dotenv --data-file /app/files/.env.ctconfig --output-dir /app/files/
```

## Uploading data to CloudTruth
Once you are comfortable with your template and associated data, you're ready to upload to CloudTruth!

```
docker run --rm -v ${PWD}/files:/app/files cloudtruth/dynamic-importer create-data --data-file /app/files/.env.ctconfig -m /app/files/.env.cttemplate -p "Meaningful Project Name"
```

By default, the utility will prompt for your CloudTruth API Key. You may also provide it via `-e CLOUDTRUTH_API_KEY="myverysecureS3CR3T!!"`

# Development
1. Set up a virtualenv
1. From your checkout of the code, `pip install -e .`

# Testing
TBD

# Contributing
Issues, pull requests, and discussions are welcomed.

See dynamic_importer.processors and the subclasses within for examples of the current design. TL;DR - if you can convert the source into a dict, BaseProcessor._traverse_data should handle most of the heavy lifting.

# Counter-examples
Because this has come up internally, this utility is intended to process config data, not application code or even raw IaC code. If you want to feed it a full Terraform manifest, you're going to get strange results. Pull your common variables into a variables.tf first!
