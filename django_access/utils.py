from .settings import SUPER_USER_ID
from .user import get_access_user, set_access_user


class AccessControlWithUser(object):
    """
    This context manager is used ... when you need to do some operations under a defined user
    Usage example:

        def do_save_access_fields(self, changed):
            with AccessControlWithUser(user1):
                self.save(update_fields=changed, force_update=True)
    """
    def __init__(self, user):
        self.new_user = user
        self.current_user = get_access_user()

    def __enter__(self):
        set_access_user(self.new_user)
        return None

    def __exit__(self, type, value, traceback):
        set_access_user(self.current_user)


class AccessControlWithSuperUser(AccessControlWithUser):
    """
    Contextmanager. Use it when you need to do some operations in full-access mode
    """
    def __init__(self):
        super(AccessControlWithSuperUser, self).__init__(SUPER_USER_ID)
