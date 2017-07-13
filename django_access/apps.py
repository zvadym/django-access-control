from django.apps import AppConfig, apps
from django.db.models.signals import post_save, post_delete, m2m_changed

from .signals import update_access_fields_handler


class AccessAppConfig(AppConfig):
    name = 'django_access'

    def ready(self):
        for model in apps.get_models():
            if not getattr(model, 'is_access_control_model', False):
                continue

            # Update access fields after saving
            post_save.connect(update_access_fields_handler, sender=model)

            # ManyToMany fields get saved after the parent instance is saved.
            # We have to use `signals` in order to update access control fields.
            for field in model._meta.many_to_many:
                if not model.restricted_to_fields:
                    continue
                if field.name not in model.restricted_to_fields:
                    continue

                through = field.rel.through

                # We can't use `m2m_changed` in case when `through` is customized,
                # We have to use post_save/post_delete signals
                if through._meta.auto_created:
                    # auto created "through" model
                    m2m_changed.connect(update_access_fields_handler, sender=through)
                else:
                    # customized "through" model
                    post_save.connect(update_access_fields_handler, sender=through)
                    post_delete.connect(update_access_fields_handler, sender=through)
