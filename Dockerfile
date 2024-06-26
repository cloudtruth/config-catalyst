FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install .
RUN rm -rf /app/

ENTRYPOINT [ "cloudtruth-dynamic-importer" ]
