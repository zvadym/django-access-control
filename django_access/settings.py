from django.conf import settings

# This ID is used for SUPER_USER mode
SUPER_USER_ID = getattr(settings, 'ACCESS_CONTROL_SUPER_USER_ID', -1)

# This ID is used for anonymous users
ANONYMOUS_USER_ID = getattr(settings, 'ACCESS_CONTROL_ANONYMOUS_USER_ID', -2)

# Initial user ID is used in case no other ID has been defined
DEFAULT_USER_ID = getattr(settings, 'ACCESS_CONTROL_DEFAULT_USER_ID', ANONYMOUS_USER_ID)
