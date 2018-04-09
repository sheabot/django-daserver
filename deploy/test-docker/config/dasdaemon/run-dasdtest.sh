#!/bin/bash

# Reset python bytecode files
find . -name "*.pyc" -exec rm {} \;

# Run dasdtest
#export REQUESTS_MANAGER_DEBUG=True
python /daserver/manage.py dasdtest --cfg /config/dasd.cfg
