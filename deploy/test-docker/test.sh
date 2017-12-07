#!/bin/bash

# Fail if any command fails
set -e

cd "$(dirname "$0")"

# Run tests
docker-compose run dasdaemon bash /config/run-tests.sh $@
