from django.core.management.base import BaseCommand
from django.apps import apps

from ...utils import AccessControlWithSuperUser


class Command(BaseCommand):
    help = 'Access control stuff'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            dest='reset', default=False,
                            help='Reset access control cache for all instances.')
        parser.add_argument('--app-label', action='store',
                            dest='app_label', default=None,
                            help='Reset only this app.')

    def handle(self, *args, **options):
        if options['reset']:
            for model in apps.get_models():
                if not getattr(model, 'is_access_control_model', False):
                    continue

                if options['app_label'] is not None:
                    if model._meta.app_label != options['app_label']:
                        continue

                with AccessControlWithSuperUser():
                    print('Updating', model.__name__)
                    for entry in model.objects.all():
                        cache_before = entry.access_permitted_users_cache
                        entry.reset_cached_access_fields()
                        if entry.access_permitted_users_cache != cache_before:
                            print('%s updated' % entry)

        else:
            raise RuntimeError('No arguments')
