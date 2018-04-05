#!/bin/sh

# Fail if any command fails
set -e

# Reset files directory
mkdir -p /files/
rm -rf /files/*

# Reset python bytecode files
find . -name "*.pyc" -exec rm {} \;

# Run migrations
python manage.py makemigrations dasdremote
python manage.py migrate

# Create test user
python manage.py environment-init --profile docker

# Start dasdremote daemon
python manage.py dasdremote-daemon --start --pidfile /files/dasdremote-daemon.pid

# Start wsgi server
gunicorn dasdremote.wsgi -b 0.0.0.0:8000
