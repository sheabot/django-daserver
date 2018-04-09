#!/bin/bash

cd "$(dirname "$0")"

if [[ $# -eq 0 ]]; then
    docker-compose run dasdaemon bash
else
    docker-compose run "$1" bash
fi
