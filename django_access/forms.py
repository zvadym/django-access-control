import warnings
from django import forms
from .user import get_access_user


class AccessControlRelatedModelForm(forms.ModelForm):
    class AccessControlFormError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update QuerySet for *related* form fields
        self.update_queryset()

    def update_queryset(self, *args, **kwargs):
        # We have to update queryset for all fields with QuerySet
        # because initially queryset contains only PUBLIC entries.
        # In order to get correct QuerySet we need a current user whom we can get from `request`

        if not get_access_user():  # user is still anonymous
            return

        if hasattr(self, 'access_control_query_updated'):  # QuerySet is already updated
            return

        setattr(self, 'access_control_query_updated', True)
        model_fields = [f.name for f in self._meta.model._meta.fields] + \
                       [f.name for f in self._meta.model._meta.many_to_many]
        declared_form_fields = list(self.declared_fields.keys())

        for field_name in self.fields:
            formfield = self.fields[field_name]

            if hasattr(formfield, 'queryset'):
                # Try to get QuerySet using `[field_name]_queryset` method
                if hasattr(self, '%s_queryset' % field_name):
                    qs = getattr(self, '%s_queryset' % field_name)(*args, **kwargs)
                    if qs:
                        formfield.queryset = qs
                        continue

                # It's a Model's field (RelatedField). We can reproduce initial QuerySet
                if field_name in model_fields and field_name not in declared_form_fields:
                    parent_model = getattr(self.Meta.model, field_name).field.rel.to
                    if not getattr(parent_model, 'is_access_control_model', False):
                        continue

                    formfield.queryset = parent_model._default_manager.get_queryset()

                    # Apply limit_choices_to
                    limit_choices_to = formfield.limit_choices_to
                    if limit_choices_to is not None:
                        if callable(limit_choices_to):
                            limit_choices_to = limit_choices_to()
                        formfield.queryset = formfield.queryset.complex_filter(limit_choices_to)

                else:
                    # It's a ChoiceField. We can't reproduce its initial QuerySet
                    raise self.AccessControlFormError(
                        "Please create `{form}.{field}_queryset` static method in order "
                        "to get correct queryset for this field".format(form=self.__class__, field=field_name))
