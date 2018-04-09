#!/bin/bash

# Reset python bytecode files
find . -name "*.pyc" -exec rm {} \;

# Run tests
export DASD_CONFIG=/config/dasd.cfg
if [[ $# -eq 0 ]]; then
    python /daserver/manage.py test test
else
    python /daserver/manage.py test $@
fi
