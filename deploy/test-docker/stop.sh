#!/bin/bash

cd "$(dirname "$0")"

if [[ $# -eq 0 ]]; then
    docker-compose stop
else
    docker-compose stop "$1"
fi
