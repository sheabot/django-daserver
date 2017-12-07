#!/bin/bash

# Fail if any command fails
set -e

cd "$(dirname "$0")"

# Build containers
docker-compose down
docker-compose build
docker-compose up -d
