"""Borra de Firebase Auth las cuentas cuyo correo ya no existe en la base.

Sirve para terminar lo que `borrar_usuarios` no alcanzó a hacer: si ese comando
falló después del COMMIT, las filas ya no están y sus correos se perdieron, así
que la única forma de identificar las cuentas huérfanas es ir al revés.

    python manage.py limpiar_firebase            # solo lista (dry-run)
    python manage.py limpiar_firebase --borrar
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lista (o borra con --borrar) las cuentas de Firebase Auth que ya no existen en la base."

    def add_arguments(self, parser):
        parser.add_argument('--borrar', action='store_true', help="Borra de verdad. Sin esto solo lista.")

    def handle(self, *args, **opciones):
        import firebase_admin
        from firebase_admin import auth, credentials
        from django.conf import settings

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(settings.CRED_PATH))

        en_la_base = {c.lower() for c in User.objects.values_list('email', flat=True) if c}
        huerfanas, sin_correo = [], 0
        for usuario in auth.list_users().iterate_all():
            if not usuario.email:
                sin_correo += 1  # sin correo no hay con qué cruzarlo: no se toca.
                continue
            if usuario.email.lower() not in en_la_base:
                huerfanas.append(usuario)

        for usuario in huerfanas:
            self.stdout.write(usuario.email)
        self.stdout.write(
            f"{len(huerfanas)} cuentas huérfanas, {len(en_la_base)} correos en la base, "
            f"{sin_correo} cuentas sin correo (se saltan).")

        if not opciones['borrar']:
            self.stdout.write(self.style.WARNING("Dry-run: no se borró nada (usá --borrar)."))
            return

        borradas = fallidas = 0
        for usuario in huerfanas:
            try:
                auth.delete_user(usuario.uid)
                borradas += 1
            except Exception as e:
                fallidas += 1
                self.stderr.write(f"Firebase {usuario.email}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Firebase: {borradas} borradas, {fallidas} con error."))
