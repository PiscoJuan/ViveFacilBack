from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_delete

        from . import checks  # noqa: registra el system check al importarse
        from .campos import borrar_archivos_al_eliminar

        post_delete.connect(borrar_archivos_al_eliminar, dispatch_uid='core.borrar_archivos')
