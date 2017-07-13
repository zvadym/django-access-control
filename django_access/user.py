from . import settings as app_settings


def make_tls_property(default=None):
    """Creates a class-wide instance property with a thread-specific value."""
    class TLSProperty(object):
        def __init__(self):
            from threading import local
            self.local = local()

        def __get__(self, instance, cls):
            if not instance:
                return self
            return self.value

        def __set__(self, instance, value):
            self.value = value

        def _get_value(self):
            return getattr(self.local, 'value', default)

        def _set_value(self, value):
            self.local.value = value
        value = property(_get_value, _set_value)

    return TLSProperty()


CURRENT_ACCESS_USER = make_tls_property(default=app_settings.DEFAULT_USER_ID)


def set_access_user(user):
    CURRENT_ACCESS_USER.value = user


def get_access_user():
    return CURRENT_ACCESS_USER.value
