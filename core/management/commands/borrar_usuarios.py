"""Borra proveedores y/o solicitantes: fila, adjuntos y cuenta de Firebase.

Irreversible. Por defecto solo cuenta lo que borraría; hay que pasar --borrar.

    python manage.py borrar_usuarios                       # dry-run de ambos
    python manage.py borrar_usuarios --tipo proveedor
    python manage.py borrar_usuarios --borrar
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from accounts.models import Administrador, Datos, Document, Proveedor, Solicitante
from pagos.models import TransaccionPaymentez
from solicitudes.models import Envio_Interesados, Solicitud, Ubicacion


class Command(BaseCommand):
    help = "Borra proveedores/solicitantes con sus archivos y su cuenta de Firebase."

    def add_arguments(self, parser):
        parser.add_argument('--tipo', choices=['proveedor', 'solicitante', 'ambos'], default='ambos')
        parser.add_argument('--borrar', action='store_true', help="Borra de verdad. Sin esto solo cuenta.")
        parser.add_argument('--sin-firebase', action='store_true', help="No toca las cuentas de Firebase Auth.")
        parser.add_argument(
            '--borrar-pagos', action='store_true',
            help="Borra también las transacciones Paymentez del usuario (registro contable).")

    def handle(self, *args, **opciones):
        tipo = opciones['tipo']
        # Proveedor, Solicitante y Administrador son OneToOne al mismo Datos, así
        # que una cuenta puede tener ficha de admin y de solicitante a la vez.
        # Esas quedan afuera enteras: el panel no exige is_staff, así que ese
        # filtro solo no alcanzaría para salvarlas.
        admins = set(Administrador.objects.values_list('user_datos_id', flat=True))
        admins.discard(None)

        proveedores = Proveedor.objects.exclude(user_datos_id__in=admins)
        solicitantes = Solicitante.objects.exclude(user_datos_id__in=admins)
        if tipo == 'proveedor':
            solicitantes = Solicitante.objects.none()
        elif tipo == 'solicitante':
            proveedores = Proveedor.objects.none()

        datos_ids = set(proveedores.values_list('user_datos_id', flat=True))
        datos_ids |= set(solicitantes.values_list('user_datos_id', flat=True))
        datos_ids.discard(None)

        # El staff y los superusuarios tampoco se tocan, tengan la ficha que tengan.
        usuarios = User.objects.filter(
            id__in=Datos.objects.filter(id__in=datos_ids).values_list('user_id', flat=True),
            is_staff=False, is_superuser=False,
        )
        correos = [c for c in usuarios.values_list('email', flat=True) if c]
        pagos = TransaccionPaymentez.objects.filter(usuario__in=usuarios)

        self.stdout.write(
            f"{proveedores.count()} proveedores, {solicitantes.count()} solicitantes, "
            f"{usuarios.count()} cuentas de usuario, {len(correos)} correos en Firebase, "
            f"{pagos.count()} transacciones Paymentez.")

        if not opciones['borrar']:
            self.stdout.write(self.style.WARNING("Dry-run: no se borró nada (usá --borrar)."))
            return
        if pagos.exists() and not opciones['borrar_pagos']:
            raise CommandError(
                f"{pagos.count()} transacciones Paymentez apuntan a estos usuarios (FK PROTECT). "
                "Pasá --borrar-pagos si aceptás perder ese registro contable.")

        with transaction.atomic():
            solicitudes = Solicitud.objects.filter(
                Q(proveedor__in=proveedores) | Q(solicitante__in=solicitantes))
            # Ubicacion no cae por cascade (el OneToOne va al revés) y tiene foto.
            ubicaciones = list(solicitudes.values_list('ubicacion_id', flat=True))
            # Envio_Interesados.solicitud y Solicitud.proveedor son PROTECT:
            # hay que ir de adentro hacia afuera.
            Envio_Interesados.objects.filter(
                Q(solicitud__in=solicitudes) | Q(proveedor__in=proveedores)).delete()
            pagos.delete()
            solicitudes.delete()
            Ubicacion.objects.filter(id__in=ubicaciones).delete()
            # Los Document cuelgan de un M2M, así que no los alcanza el cascade.
            Document.objects.filter(proveedor__in=proveedores).delete()

            borrados_usuarios = usuarios.delete()[0]
            # Fichas sin cuenta de usuario (user=NULL): el cascade no las alcanza.
            borrados_datos = Datos.objects.filter(id__in=datos_ids).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f"{borrados_usuarios} filas borradas por cascade de usuarios, {borrados_datos} por fichas sueltas. "
            "Los archivos se borran del storage al confirmarse la transacción."))

        if opciones['sin_firebase']:
            return
        self._borrar_firebase(correos)

    def _borrar_firebase(self, correos):
        from core.firebase import borrar_cuenta_firebase

        borradas = inexistentes = fallidas = 0
        for correo in correos:
            try:
                if borrar_cuenta_firebase(correo):
                    borradas += 1
                else:
                    inexistentes += 1
            except Exception as e:
                fallidas += 1
                self.stderr.write(f"Firebase {correo}: {e}")
        self.stdout.write(self.style.SUCCESS(
            f"Firebase: {borradas} borradas, {inexistentes} no existían, {fallidas} con error."))
