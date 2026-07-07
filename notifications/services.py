import uuid

from api.models import Datos, Notificacion, NotificacionMasiva, Proveedor, Solicitante
from django.contrib.auth.models import User


def _notificar_proveedores_segmentado(notif):
    """Mismo código operando sobre `Notificacion` o `NotificacionMasiva`,
    unificado acá en vez de mantener dos copias. Los `print()` de debug
    del original se omiten, igual que en `notificar_chat_proveedor`."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    tipo_proveedor = notif.tipo_proveedores
    data_notificacion = {"descripcion": notif.descripcion}

    for proveedor in Proveedor.objects.all():
        profesiones = proveedor.profesion.split(",") if ',' in proveedor.profesion else [proveedor.profesion]
        if tipo_proveedor not in profesiones:
            continue
        datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
        user = User.objects.get(id=datos_prov.user.id)
        devices = FCMDevice.objects.filter(active=True, user_id=user.id)
        tokens = list(devices.values_list('registration_id', flat=True))
        if tokens:
            send_notificationF(tokens, notif.titulo, notif.descripcion, data_notificacion)


def list_notificaciones():
    return Notificacion.objects.all()


def crear_notificacion(data, files):
    """Devuelve (notificacion_o_None, data: dict)."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    notificacion = Notificacion.objects.create(
        user=User.objects.first(),
        nombre=data.get('nombre'),
        titulo=data.get('titulo'),
        descripcion=data.get('descripcion'),
        tipo_proveedores=data.get('tipo_proveedores'),
        frecuencia=data.get('frecuencia'),
        ruta=data.get('ruta'),
        imagen=files.get('imagen'),
        fecha_iniciacion=data.get('fecha_iniciacion'),
        fecha_expiracion=data.get('fecha_expiracion'),
        hora=data.get('hora'),
    )
    data_notificacion = {"ruta": data.get('ruta'), "descripcion": data.get('descripcion')}
    if files.get('imagen') is not None:
        data_notificacion["imagen"] = notificacion.imagen.url
    try:
        devices = FCMDevice.objects.filter(active=True)
        tokens = list(devices.values_list('registration_id', flat=True))
        send_notificationF(tokens, data.get('titulo'), data.get('descripcion'), data_notificacion)
        return notificacion, {"success": True, "message": "La notificación ha sido creada correctamente."}
    except Exception as e:
        notificacion.delete()
        return None, {"success": False, "message": f"Hubo un error al enviar la notificación: {str(e)}"}


def actualizar_notificacion(id, data):
    """Puede propagar Notificacion.DoesNotExist — la vista lo traduce a 404."""
    notificacion = Notificacion.objects.get(id=int(id))
    return notificacion


def eliminar_notificacion(id):
    """Devuelve (success: bool, message: str)."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    try:
        notificacion = Notificacion.objects.get(id=id)
        titulo = notificacion.titulo
        descripcion = notificacion.descripcion
        notificacion.delete()

        devices = FCMDevice.objects.filter(active=True)
        tokens = list(devices.values_list('registration_id', flat=True))
        send_notificationF(tokens, "Notificacion eliminada:" + titulo, descripcion, {"descripcion": descripcion})
        return True, "Se ha eliminado la notificación exitosamente."
    except Exception:
        return False, "La notificación no fue encontrada en la base de datos."


def obtener_notificacion(pk):
    """Nunca estuvo wireada a ninguna URL con `pk` real (dead branch), se
    mantiene por si se decide exponerla más adelante."""
    return Notificacion.objects.get(id=pk)


def actualizar_estado_notificacion(id, estado):
    notificacion = Notificacion.objects.get(id=id)
    notificacion.estado = estado
    notificacion.save()


def enviar_notificacion_segmentada(pk):
    notificacion = Notificacion.objects.get(id=pk)
    _notificar_proveedores_segmentado(notificacion)


def list_notificaciones_masivas():
    """Compartido con Provedor2022 y Solicitante2022, se queda expuesto
    sin rol específico."""
    return NotificacionMasiva.objects.all()


def crear_notificacion_masiva(data, files):
    """Devuelve (notificacion_o_None, data: dict)."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    notificacion = NotificacionMasiva.objects.create(
        nombre=data.get('nombre'),
        titulo=data.get('titulo'),
        descripcion=data.get('descripcion'),
        tipo_proveedores=data.get('tipo_proveedores'),
        frecuencia=data.get('frecuencia'),
        ruta=data.get('ruta'),
        imagen=files.get('imagen'),
        fecha_iniciacion=data.get('fecha_iniciacion'),
        fecha_expiracion=data.get('fecha_expiracion'),
        hora=data.get('hora'),
    )
    data_notificacion = {"ruta": data.get('ruta'), "descripcion": data.get('descripcion')}
    if files.get('imagen') is not None:
        data_notificacion["imagen"] = notificacion.imagen.url
    try:
        devices = FCMDevice.objects.filter(active=True)
        tokens = list(devices.values_list('registration_id', flat=True))
        send_notificationF(tokens, data.get('titulo'), data.get('descripcion'), data_notificacion)
        return notificacion, {"success": True, "message": "La notificación ha sido creada correctamente."}
    except Exception as e:
        notificacion.delete()
        return None, {"success": False, "message": f"Hubo un error al enviar la notificación: {str(e)}"}


def actualizar_notificacion_masiva(id, data):
    """Puede propagar NotificacionMasiva.DoesNotExist — la vista lo
    traduce a 404."""
    return NotificacionMasiva.objects.get(id=int(id))


def eliminar_notificacion_masiva(id):
    """Devuelve (success: bool, message: str)."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    try:
        notificacion = NotificacionMasiva.objects.get(id=id)
        titulo = notificacion.titulo
        descripcion = notificacion.descripcion
        notificacion.delete()

        devices = FCMDevice.objects.filter(active=True)
        tokens = list(devices.values_list('registration_id', flat=True))
        send_notificationF(tokens, "Notificacion eliminada:" + titulo, descripcion, {"descripcion": descripcion})
        return True, "Se ha eliminado la notificación exitosamente."
    except Exception:
        return False, "La notificación no fue encontrada en la base de datos."


def obtener_notificacion_masiva(pk):
    """Nunca estuvo wireada a ninguna URL con `pk` real (dead branch)."""
    return NotificacionMasiva.objects.get(id=pk)


def actualizar_estado_notificacion_masiva(id, estado):
    notificacion = NotificacionMasiva.objects.get(id=id)
    notificacion.estado = estado
    notificacion.save()


def enviar_notificacion_masiva_segmentada(pk):
    notificacion = NotificacionMasiva.objects.get(id=pk)
    _notificar_proveedores_segmentado(notificacion)


def enviar_email_bienvenida(email, password, tipo):
    """Devuelve dict de respuesta tal cual el original (incluye
    'clave' == security_access en el camino de éxito)."""
    import threading

    from core.email import FormatEmail

    data = {}
    format_email = FormatEmail()
    user = Datos.objects.get(user__email=email)
    if user is None:
        data['success'] = False
        return data

    user.security_access = uuid.uuid4()
    user.save()
    asunto = 'Bienvenido a Vive Fácil'
    try:
        plantilla = 'emails/welcomeAdmin.html' if tipo == "Administrador" else 'emails/welcomeProveedor.html'
        thread = threading.Thread(target=format_email.send_email([email], asunto, plantilla, {
            "username": user.nombres + ' ' + user.apellidos, "user": email, "password": password}))
        thread.start()
        data['success'] = True
        data['clave'] = user.security_access
    except Exception:
        data['success'] = False
    return data


def enviar_correo_solicitud(email, profesion, rechazada):
    import threading

    from core.email import FormatEmail

    data = {}
    format_email = FormatEmail()
    user = Datos.objects.get(user__email=email)
    if user is None:
        data['success'] = False
        return data

    asunto = "Respuesta Solicitud"
    try:
        plantilla = 'emails/solicitudRechazada.html' if rechazada else 'emails/solicitudAceptada.html'
        thread = threading.Thread(target=format_email.send_email([email], asunto, plantilla, {
            "username": user.nombres + ' ' + user.apellidos, "user": email, "profesion": profesion}))
        thread.start()
        data['success'] = True
    except Exception:
        data['success'] = False
    return data


def enviar_alerta(user_email, asunto, texto):
    import threading

    from django.contrib.auth.models import User as AuthUser

    from core.email import FormatEmail

    data = {'success': False}
    usuario = AuthUser.objects.filter(email=user_email)
    if usuario.count() > 0:
        user_dato = Datos.objects.get(user=usuario.first())
        if user_dato is not None:
            format_email = FormatEmail()
            thread = threading.Thread(target=format_email.send_email(
                [user_email], asunto, 'emails/enviarAlerta.html', {"username": user_dato.nombres, "contenido": texto}))
            thread.start()
            data['success'] = True
    return data


def notificar_chat_solicitante(remitente_id, es_solicitante, mensaje, user_id, url):
    """**Bug real preservado, no corregido**: en la
    rama `es_solicitante` falso, el original referencia `tokens` sin
    haberla asignado nunca en esa rama (`NameError` garantizado) — se
    replica tal cual. No se corrige porque el único consumidor real
    confirmado (`ViveFacil_Solicitante2022`, `chat-texto.page.ts:88`)
    siempre manda `isSolicitante: true`, así que esa rama nunca se
    ejecuta en producción; arreglarla implicaría adivinar comportamiento
    nuevo para el lado proveedor del chat, fuera de alcance acá."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    remitente_nombre = Datos.objects.get(id=remitente_id)
    titles = 'Nuevo Mensaje de ' + remitente_nombre.nombres + remitente_nombre.apellidos
    bodys = mensaje
    ruta = ""
    if es_solicitante:
        ruta = "/main-tabs/chat"
        dato_prov = Datos.objects.get(user_id=user_id)
        dato_id_prov = dato_prov.user_id
        devices = FCMDevice.objects.filter(active=True, user_id=dato_id_prov)
        tokend = devices.values_list('registration_id', flat=True)
        tokens = list(tokend)
        data = {"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}
        send_notificationF(tokens, titles, bodys, data)
    else:
        ruta = "/main/chat"
        data = {"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}
        send_notificationF(tokens, titles, bodys, data)  # noqa: F821 — bug preservado, ver docstring

    return user_id


def notificar_general(user, message, title):
    """Sin consumidor real confirmado en ningún frontend."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    devices = FCMDevice.objects.filter(active=True, user_id=user)
    tokend = devices.values_list('registration_id', flat=True)
    data = {"ruta": "Historial", "descripcion": "Proveedor Interesado"}
    tokens = list(tokend)
    send_notificationF(tokens, title, message, data)
    return user


def notificar_chat_proveedor(remitente_id, get_usuario_id, mensaje, url):
    """Devuelve (data, http_status). Los `print()` de debug del original se
    omiten (no forman parte del contrato de la API); el resto de la lógica,
    incluidos los mensajes de error, se preserva tal cual."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    try:
        remitente_nombre_prov = Datos.objects.get(user_id=remitente_id)
    except Datos.DoesNotExist:
        return {"error": "Remitente not found"}, 404

    titles = "Nuevo Mensaje de " + remitente_nombre_prov.nombres
    bodys = mensaje

    try:
        solicitante = Solicitante.objects.get(user_datos__id=get_usuario_id)
    except Solicitante.DoesNotExist:
        return {"error": "Solicitante not found"}, 404

    soli_id = solicitante.user_datos_id

    try:
        dato_soli = Datos.objects.get(id=soli_id)
    except Datos.DoesNotExist:
        return {"error": "Datos not found"}, 404

    dato_id_soli = dato_soli.user_id
    devices = FCMDevice.objects.filter(active=True, user_id=dato_id_soli)
    if not devices.exists():
        return {"error": "No devices found"}, 404

    tokens = list(devices.values_list("registration_id", flat=True))
    data = {"url": url, "ruta": "/main/chat", "descripcion": "Tiene un Mensaje nuevo"}
    try:
        send_notificationF(tokens, titles, bodys, data)
    except Exception:
        pass  # el original también ignoraba errores de envío acá

    return get_usuario_id, 200
