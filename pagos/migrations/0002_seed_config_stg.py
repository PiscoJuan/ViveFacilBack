"""
Siembra la fila activa de ConfiguracionPaymentez a partir de las variables de
entorno STG que ya existían en .env (INNOVA-EC-*). Idempotente: si ya hay
alguna configuración, no hace nada. Las llaves de PROD se cargan luego desde el
admin (tras rotarlas — la anterior quedó comprometida en la app).
"""
import os

from django.db import migrations


def seed_config(apps, schema_editor):
    Config = apps.get_model("pagos", "ConfiguracionPaymentez")
    if Config.objects.exists():
        return

    code_server = os.environ.get("SERVER_APP_CODE")
    key_server = os.environ.get("SERVER_APP_KEY")
    code_client = os.environ.get("CLIENT_APP_CODE")
    key_client = os.environ.get("CLIENT_APP_KEY")
    if not (code_server and key_server and code_client and key_client):
        # Sin credenciales en el entorno: se crea la fila desde el admin.
        return

    host = (os.environ.get("PAYMENTEZ_HOST") or "https://ccapi-stg.paymentez.com/").rstrip("/") + "/"
    url_base = host + "v2/"
    ambiente = "prod" if "ccapi.paymentez.com" in host else "stg"

    Config.objects.create(
        nombre="Configuración Paymentez (STG)",
        app_code_client=code_client,
        app_key_client=key_client,
        app_code_server=code_server,
        app_key_server=key_server,
        url_base=url_base,
        ambiente=ambiente,
        is_active=True,
        eliminar_tarjeta_tras_compra=False,
    )


def unseed_config(apps, schema_editor):
    Config = apps.get_model("pagos", "ConfiguracionPaymentez")
    Config.objects.filter(nombre="Configuración Paymentez (STG)").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pagos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_config, unseed_config),
    ]
