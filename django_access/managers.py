import warnings
from django.db import models
from django.db.models import Q

from .user import get_access_user
from .settings import SUPER_USER_ID, ANONYMOUS_USER_ID


class AccessControlManagerMixin(object):
    use_for_related_fields = True

    # Access Control Manager Marker
    access_control_manager = True

    # True if was used with None access user
    access_control_init_without_user = True

    class UserRequiredWarning(Warning):
        """
        User isn't defined. You have to use `set_access_user` function
        or call queryset after middleware has been called up.
        """
        pass

    def __init__(self):
        super(AccessControlManagerMixin, self).__init__()
        if get_access_user() is not None:
            self.access_control_init_without_user = False

    def get_user(self):
        current_user = get_access_user()

        if current_user:
            return current_user

        warnings.warn(
            "AccessControlManagerMixin.get_user() warning. User isn't set. "
            "Please beware that you will get only PUBLIC entries",
            self.UserRequiredWarning)

        return None

    def control_qs(self, qs):
        """
        Main control method.

        :param qs: QuerySet before access control
        :return: QuerySet after access control
        """

        user = self.get_user()
        if user == SUPER_USER_ID:
            return qs
        elif user == ANONYMOUS_USER_ID:
            # If user is anonymous - only PUBLIC entries return
            qs = qs.filter(access_level_cache=self.model.Level.PUBLIC)
        else:
            # If user is authorized:
            # all entries with PUBLIC and AUTHORIZED level return
            # as well as the ones with RESTRICTED level, if user ID is in `access_permitted_users_cache`
            qs = qs.filter(
                ~Q(access_level_cache=self.model.Level.RESTRICTED) |
                (Q(access_level_cache=self.model.Level.RESTRICTED) &
                 Q(access_permitted_users_cache__contains=':%s:' % user.pk))
            )
        return qs

    def get_queryset(self):
        return self.control_qs(super().get_queryset())

    # Deprecated, but some app are still using it
    get_query_set = get_queryset


class AccessControlManager(AccessControlManagerMixin, models.Manager):
    pass
