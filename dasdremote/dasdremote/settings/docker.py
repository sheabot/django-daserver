# Load defaults in order to then add/override with dev-only settings
from dev import *


# nginx proxy_set_header SCRIPT_NAME did not work, so set it here
FORCE_SCRIPT_NAME = '/dasdremote'

# Put database in files directory
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SECRETS['db_name'],
    }
}
