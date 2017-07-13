from django.contrib.auth import get_user_model
from django.db import models

from .settings import SUPER_USER_ID, ANONYMOUS_USER_ID
from .managers import AccessControlManager
from .user import get_access_user
from .utils import AccessControlWithSuperUser


class AbstractAccessControlMixin(object):
    class Meta:
        abstract = True

    class Level:
        PUBLIC = 'public'
        AUTHORIZED = 'authorized'
        RESTRICTED = 'restricted'

        DEFAULT = AUTHORIZED

        CHOICES = (
            (PUBLIC, 'Public access'),
            (AUTHORIZED, 'Authorized users only'),
            (RESTRICTED, 'Selected users only (restricted)')
        )

    class BadManagerError(Exception):
        """
        Wrong manager (not AccessControlManager)
        """
        pass

    class AccessDataError(Exception):
        """
        It is raised when RESTRICTED access level is set with empty allowed users list.
        """
        pass

    class AccessDenied(Exception):
        pass

    # Access Control model marker
    is_access_control_model = True

    # Readonly fields! Only `reset_access_fields()` method can change this values
    access_level_cache = models.CharField(max_length=16, choices=Level.CHOICES, default=Level.DEFAULT, editable=False)
    access_permitted_users_cache = models.CharField(max_length=255, null=True, blank=True, editable=False)

    # Manager
    objects = AccessControlManager()

    def save(self, *args, **kwargs):
        if not getattr(type(self)._base_manager, 'access_control_manager', False):
            raise AbstractAccessControlMixin.BadManagerError
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self.check_access():
            raise AbstractAccessControlMixin.AccessDenied
        super().delete(*args, **kwargs)

    #
    #
    #

    def check_access(self, user=None):
        """
        It checks if user has access
        :param user: User object, `SUPER_USER_PK` or None if user is anonymous
        :return: True when access is allowed, otherwise False
        """

        # Anyone can see PUBLIC entry
        if self.access_level_cache == AbstractAccessControlMixin.Level.PUBLIC:
            return True

        if user is None:
            user = get_access_user()

        # Super user can access anything
        if user == SUPER_USER_ID:
            return True

        # Anonymous user can't see AUTHORIZED and RESTRICTED entries
        if user == ANONYMOUS_USER_ID:
            return False

        # At this point only authenticated users are left
        # Authenticated user can see AUTHORIZED entries
        if self.access_level_cache == AbstractAccessControlMixin.Level.AUTHORIZED:
            return True

        # Access level is RESTRICTED
        if self.access_permitted_users_cache is None:
            raise self.AccessDataError

        if isinstance(user, get_user_model()):
            user = user.pk  # need only ID

        return True if ':%s:' % user in self.access_permitted_users_cache else False

    def process_restricted_to_fields(self):
        """
        It checks `restricted_to_fields` property and returns list of Users who have access to the entry
        """
        users = []
        for field_name in self.restricted_to_fields:
            field = getattr(self, field_name)

            if isinstance(field, models.Manager):
                users.extend(list(field.all()))
            elif isinstance(field, get_user_model()):
                users.append(field)

        return users

    def reset_cached_access_fields(self):
        """
        Method updates `access_level_cache` and `access_permitted_users_cache` fields if access parameters were changed
        """
        changed = []
        new_access_level = self.get_access_level()
        new_access_permitted_users = self.allowed_for()

        if self.access_level_cache != new_access_level:
            self.access_level_cache = new_access_level
            changed.append('access_level_cache')

        if self.access_permitted_users_cache != new_access_permitted_users:
            self.access_permitted_users_cache = new_access_permitted_users
            changed.append('access_permitted_users_cache')

        if changed:
            self.save_access_fields(changed)

        return changed

    def save_access_fields(self, changed):
        """
        Use this method when you need to update cached access control fields
        It uses `super_user` mode

        :param changed: list of changed fields
        """
        if not getattr(type(self)._base_manager, 'access_control_manager', False):
            raise self.BadManagerError

        if hasattr(self, 'pre_save_access_fields'):
            # Create this method if you need to change instance before saving
            self.pre_save_access_fields()

        with AccessControlWithSuperUser():
            self.save(update_fields=changed, force_update=True)



    #
    # Inheritable section
    #

    # List of field names with allowed users. It can be FK and M2M field types
    # Example: restricted_to_fields = ('created_by', 'responsible')
    restricted_to_fields = list()

    def get_access_level(self):
        return AbstractAccessControlMixin.Level.DEFAULT

    def allowed_for(self, as_string=True):
        users = self.process_restricted_to_fields()

        if as_string:
            users = set(str(user.id) for user in users)
            return ':%s:' % str(':'.join(users)) if users else None

        return users

    #
    # end inheritable section
    #########
