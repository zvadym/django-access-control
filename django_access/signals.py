from .utils import AccessControlWithSuperUser


def update_access_fields_handler(sender, instance, **kwargs):
    """
    Signals handler is used to update access fields
    """
    with AccessControlWithSuperUser():
        # TODO: if m2m with auto created `Through` model
        if 'action' in kwargs:
            if kwargs['action'] in ('post_add', 'post_clear', 'post_remove'):
                instance.reset_cached_access_fields()
            return

        # TODO: if is_access_control_model
        if getattr(instance, 'is_access_control_model', False):
            instance.reset_cached_access_fields()
            return

        # TODO: if m2m with custom `Through` model
        for value in list(instance.__dict__.values()):
            if getattr(value, 'is_access_control_model', False):
                try:
                    value.refresh_from_db()
                except type(value).DoesNotExist:
                    pass
                else:
                    value.reset_cached_access_fields()
