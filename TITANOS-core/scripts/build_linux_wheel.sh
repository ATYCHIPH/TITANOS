#!/bin/bash
set -e

# Build the docker image
docker build -t titanos-manylinux-builder -f docker/manylinux.Dockerfile .

# Run the docker container to build the wheel
docker run --rm -v "$(pwd):/io" titanos-manylinux-builder
