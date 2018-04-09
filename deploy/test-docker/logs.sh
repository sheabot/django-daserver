#!/bin/bash

cd "$(dirname "$0")"

if [[ $# -eq 0 ]]; then
    docker-compose logs -t -f dasdaemon
else
    docker-compose logs -t -f "$1"
fi
