"""Admin de FCMDevice.

El de `fcm_django` sirve tal cual salvo por un detalle: su acción "Send test
notification" deja escapar el `FirebaseError` cuando el token ya no existe en
Firebase, y el admin responde 500 (`UnregisteredError: NotRegistered`). La baja
del dispositivo sí ocurre — `FCMDevice.send_message` llama a
`deactivate_devices_with_error_result` antes de relanzar —, así que lo único que
falta es no reventar y contar lo que pasó.

Se agrega además la columna "activos del usuario": con más de uno, ese usuario
recibe la misma notificación varias veces en el mismo teléfono (tokens viejos
que nunca se desactivaron).
"""

from django.contrib import admin, messages
from django.db.models import Count, OuterRef, Subquery
from fcm_django.admin import DeviceAdmin
from fcm_django.models import FCMDevice
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import Message, Notification

# `notifications` va después de `fcm_django` en INSTALLED_APPS, así que para
# cuando se importa este módulo el admin de la librería ya está registrado.
admin.site.unregister(FCMDevice)


@admin.register(FCMDevice)
class DispositivoNotificacionAdmin(DeviceAdmin):
    list_display = DeviceAdmin.list_display + ("activos_del_usuario",)

    def get_queryset(self, request):
        activos = (
            FCMDevice.objects.filter(user_id=OuterRef("user_id"), active=True)
            .values("user_id")
            .annotate(total=Count("pk"))
            .values("total")
        )
        return super().get_queryset(request).annotate(_activos=Subquery(activos))

    @admin.display(description="Activos del usuario", ordering="_activos")
    def activos_del_usuario(self, obj):
        return obj._activos or 0

    def send_messages(self, request, queryset, bulk=False):
        # El camino bulk de la librería ya agrega los errores en su respuesta en
        # vez de lanzarlos; solo el de a uno necesita la red.
        if bulk:
            return super().send_messages(request, queryset, bulk=True)

        enviados = 0
        dados_de_baja = []
        fallidos = []

        for device in queryset:
            try:
                device.send_message(
                    Message(
                        notification=Notification(
                            title="Notificación de prueba",
                            body="Prueba enviada desde el panel de administración.",
                        )
                    )
                )
                enviados += 1
            except FirebaseError as exc:
                etiqueta = f"{(device.registration_id or '')[:12]}… ({type(exc).__name__})"
                # Se relee de la base en vez de asumir: la librería solo desactiva
                # los errores que considera definitivos.
                device.refresh_from_db(fields=["active"])
                (dados_de_baja if not device.active else fallidos).append(etiqueta)

        if enviados:
            self.message_user(
                request, f"{enviados} notificación(es) enviada(s).", messages.SUCCESS
            )
        if dados_de_baja:
            self.message_user(
                request,
                f"{len(dados_de_baja)} dispositivo(s) dados de baja por token inválido: "
                + ", ".join(dados_de_baja),
                messages.WARNING,
            )
        if fallidos:
            self.message_user(
                request,
                f"{len(fallidos)} dispositivo(s) fallaron pero siguen activos: "
                + ", ".join(fallidos),
                messages.ERROR,
            )
