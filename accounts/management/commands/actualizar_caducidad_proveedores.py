from django.core.management.base import BaseCommand

from accounts import services


class Command(BaseCommand):
    help = (
        "Desactiva proveedores con fecha_caducidad vencida y les avisa por "
        "email. Reemplaza al cron externo que pegaba a "
        "actualizar_caducidad_proveedores/ vía HTTP; misma lógica, "
        "invocada directo en el servidor."
    )

    def handle(self, *args, **options):
        data, http_status = services.actualizar_caducidad_masiva_proveedores()
        if http_status != 200:
            self.stdout.write(self.style.WARNING(str(data)))
            return
        for linea in data["success"]:
            self.stdout.write(linea)
        self.stdout.write(self.style.SUCCESS(f"{len(data['success'])} proveedor(es) actualizado(s)."))
