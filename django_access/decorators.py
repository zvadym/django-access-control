from functools import wraps

from .utils import AccessControlWithUser, AccessControlWithSuperUser


def access_control_as(user):
    def real_decorator(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            with AccessControlWithUser(user):
                ret = fn(*args, **kwargs)
            return ret
        return inner
    return real_decorator


def access_control_as_super_user(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        with AccessControlWithSuperUser():
            ret = fn(*args, **kwargs)
        return ret
    return inner
