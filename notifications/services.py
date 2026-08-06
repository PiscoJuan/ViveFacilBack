import uuid
from datetime import datetime, time

from django.contrib.auth.models import User
from django.db.models import F, Q, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import Datos, Proveedor, Solicitante
from notifications.models import (
    DIRIGIDA_AMBAS,
    DIRIGIDA_PROVEEDOR,
    DIRIGIDA_SOLICITANTE,
    FRECUENCIA_DIARIA,
    FRECUENCIA_SEMANAL,
    FRECUENCIA_UNICA,
    NOTIF_TIPO_GENERAL,
    Notificacion,
    NotificacionIndividual,
    NotificacionMasiva,
    NotificacionMasivaEstado,
)


def condicion_destinatarios(dirigida_a, profesion_ids):
    """Q sobre `Datos` con los filtros de destinatario configurables.

    Función pura a propósito: es la regla de negocio que decide a quién le
    llega una notificación, y así se testea sin base de datos (este proyecto no
    puede crear una de tests).

    `proveedor`, `solicitante` y `profesion_proveedor` son los accesores
    inversos por defecto — ningún modelo del repo declara `related_name`.
    """
    dirigida_a = dirigida_a or DIRIGIDA_AMBAS
    cond = Q()
    if dirigida_a in (DIRIGIDA_PROVEEDOR, DIRIGIDA_AMBAS):
        q_prov = Q(proveedor__estado=True)
        if profesion_ids:
            # Vía la pivote real, no el CSV `Proveedor.profesion`, que está
            # documentadamente desincronizado (ver reparar_profesion_proveedor).
            q_prov &= Q(
                proveedor__profesion_proveedor__estado=True,
                proveedor__profesion_proveedor__profesion_id__in=profesion_ids,
            )
        cond |= q_prov
    if dirigida_a in (DIRIGIDA_SOLICITANTE, DIRIGIDA_AMBAS):
        cond |= Q(solicitante__estado=True)
    return cond


def resolver_destinatarios(notif):
    """`user_id` (auth.User) a los que va la notificación.

    Devuelve un queryset, no una lista, para que MySQL lo resuelva como
    subconsulta: el `IN` no degenera aunque haya miles de usuarios.

    Reemplaza al `_notificar_proveedores_segmentado` viejo, que iteraba
    `Proveedor.objects.all()` en Python haciendo dos queries por proveedor.
    """
    profesion_ids = (
        list(notif.profesiones.values_list('id', flat=True))
        if notif.dirigida_a == DIRIGIDA_PROVEEDOR else []
    )
    return (Datos.objects
            .filter(estado=True, user__isnull=False)
            .filter(condicion_destinatarios(notif.dirigida_a, profesion_ids))
            .values_list('user_id', flat=True)
            .distinct())


def _payload(notif):
    """`data` del push. FCM v1 exige que todos los valores sean strings."""
    data = {
        "ruta": notif.ruta or "",
        "descripcion": notif.descripcion or "",
    }
    if notif.imagen:
        data["imagen"] = notif.imagen.url
    return data


def enviar_push(notif, asincrono=False):
    """Manda el push a los destinatarios de `notif`. Devuelve cuántos tokens.

    `asincrono` en las vistas del admin (una masiva a ambas apps son miles de
    POST en serie con timeout de 15s), síncrono en el management command, donde
    los threads daemon de la versión async morirían al salir el proceso.
    """
    from core.firebase import send_notificationF, send_notificationF_async
    from fcm_django.models import FCMDevice

    tokens = list(FCMDevice.objects
                  .filter(active=True, user_id__in=resolver_destinatarios(notif))
                  .values_list('registration_id', flat=True))
    if not tokens:
        return 0
    enviar = send_notificationF_async if asincrono else send_notificationF
    enviar(tokens, notif.titulo, notif.descripcion, _payload(notif))
    return len(tokens)


def crear_notificacion_individual(user, tipo, titulo, descripcion, ruta='', asincrono=True, imagen=None):
    """Evento de un único destinatario (cupón, solicitud adjudicada/aceptada,
    pago exitoso, etc.): persiste la fila (queda visible en el feed de la
    app) y manda el push, en un solo paso. Reemplaza las llamadas sueltas a
    `send_notificationF`/`send_notificationF_async` en los puntos de un solo
    destinatario de `solicitudes`, `payments` y `pagos.services.pago_controller`.

    `descripcion` hace de cuerpo del push Y de texto del feed — antes esos
    puntos mandaban un cuerpo de push genérico ("¡Dale un vistazo!") separado
    de la descripción real, que solo viajaba en el `data` del push. Con un
    único texto más informativo en el push no se pierde nada.

    `imagen`: nombre/ruta de un archivo YA guardado (p. ej. `cupon.foto.name`),
    no un upload nuevo — así no se duplica el archivo, solo se referencia.
    """
    from core.firebase import send_notificationF, send_notificationF_async
    from fcm_django.models import FCMDevice

    NotificacionIndividual.objects.create(
        user=user, tipo=tipo, titulo=titulo, descripcion=descripcion, ruta=ruta or '', imagen=imagen or None,
    )
    tokens = list(FCMDevice.objects
                  .filter(active=True, user=user)
                  .values_list('registration_id', flat=True))
    if not tokens:
        return
    enviar = send_notificationF_async if asincrono else send_notificationF
    enviar(tokens, titulo, descripcion, {"ruta": ruta or '', "descripcion": descripcion or ''})


def crear_notificaciones_individuales_bulk(users, tipo, titulo, descripcion, ruta='', imagen=None):
    """Variante broadcast de `crear_notificacion_individual`: un evento que le
    llega a varios usuarios a la vez (hoy solo el cupón nuevo, a todos los
    solicitantes). Un `bulk_create` para las filas del feed; el push en sí lo
    sigue mandando el llamador con su propio queryset de tokens (agrupado, no
    un POST por usuario)."""
    NotificacionIndividual.objects.bulk_create([
        NotificacionIndividual(
            user=user, tipo=tipo, titulo=titulo, descripcion=descripcion, ruta=ruta or '', imagen=imagen or None,
        )
        for user in users
    ])


def slot_de_hoy(hora, hoy):
    """Combina un `TimeField` naive con una fecha, en la zona del proyecto.

    Nunca `.replace(tzinfo=...)`: America/Guayaquil es UTC-5 fijo, pero el
    atajo se rompería el día que cambie el TIME_ZONE.
    """
    return timezone.make_aware(datetime.combine(hoy, hora), timezone.get_current_timezone())


def debe_disparar(notif, ahora, hoy):
    """Slot que le toca a una notificación programada, o None si no le toca.

    Duck-typed (no exige una instancia de `Notificacion`) para poder testearlo
    sin ORM. `ahora` y `hoy` se pasan en vez de leerlos del reloj para que el
    test controle el tiempo.
    """
    if not notif.hora:
        return None
    if notif.fecha_iniciacion and notif.fecha_iniciacion > ahora:
        return None
    if notif.fecha_expiracion and notif.fecha_expiracion < ahora:
        return None
    if notif.frecuencia == FRECUENCIA_UNICA and notif.veces_enviada > 0:
        return None
    if notif.frecuencia == FRECUENCIA_SEMANAL:
        dias = [d for d in (notif.dias_semana or '').split(',') if d]
        if str(hoy.weekday()) not in dias:
            return None
    elif notif.frecuencia not in (FRECUENCIA_UNICA, FRECUENCIA_DIARIA):
        # Frecuencia legacy en texto libre: no dispara nunca en vez de adivinar.
        return None

    slot = slot_de_hoy(notif.hora, hoy)
    if slot > ahora:
        return None                      # su turno es más tarde hoy
    if notif.ultimo_envio and timezone.localtime(notif.ultimo_envio) >= slot:
        return None                      # ya se disparó en este slot
    return slot


def _ids(data, key):
    """Lee un campo multivalor. El admin manda FormData multipart, así que
    `request.data` es un QueryDict y hay que usar `getlist`."""
    if hasattr(data, 'getlist'):
        crudos = data.getlist(key)
    else:
        crudo = data.get(key) or []
        crudos = crudo if isinstance(crudo, (list, tuple)) else str(crudo).split(',')
    return [int(v) for v in crudos if str(v).strip()]


def _fecha(data, key):
    """Parsea 'YYYY-MM-DD' o 'YYYY-MM-DDTHH:MM[:SS]' a datetime aware, o None.

    Explícito y no delegado al ORM porque un string suelto en un DateTimeField
    entra como naive y Django solo avisa con un warning.
    """
    valor = (data.get(key) or '').strip()
    if not valor:
        return None
    fecha = parse_datetime(valor)
    if fecha is None:
        solo_dia = parse_date(valor)
        if solo_dia is None:
            return None
        fecha = datetime.combine(solo_dia, time.min)
    if timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())
    return fecha


def aplicar_profesiones(notificacion, data):
    """El filtro por profesión solo aplica a proveedores; con cualquier otro
    destinatario se descarta lo que venga para no dejar filtros fantasma."""
    if notificacion.dirigida_a == DIRIGIDA_PROVEEDOR:
        notificacion.profesiones.set(_ids(data, 'profesiones'))
    else:
        notificacion.profesiones.clear()


def list_notificaciones():
    return Notificacion.objects.prefetch_related('profesiones').order_by('-id')


def crear_notificacion(data, files, user=None):
    """Crea una notificación programada. Devuelve (notificacion, data: dict).

    No envía nada: nace pendiente y la dispara
    `manage.py enviar_notificaciones_programadas` cuando le toque su slot.
    """
    notificacion = Notificacion.objects.create(
        user=user if user and user.is_authenticated else None,
        nombre=data.get('nombre'),
        titulo=data.get('titulo'),
        descripcion=data.get('descripcion'),
        dirigida_a=data.get('dirigida_a') or DIRIGIDA_AMBAS,
        frecuencia=data.get('frecuencia') or FRECUENCIA_UNICA,
        dias_semana=data.get('dias_semana') or '',
        ruta=data.get('ruta'),
        imagen=files.get('imagen'),
        fecha_iniciacion=_fecha(data, 'fecha_iniciacion'),
        fecha_expiracion=_fecha(data, 'fecha_expiracion'),
        hora=data.get('hora') or None,
    )
    aplicar_profesiones(notificacion, data)
    return notificacion, {"success": True, "message": "La notificación programada ha sido creada correctamente."}


def actualizar_notificacion(id, data):
    """Puede propagar Notificacion.DoesNotExist — la vista lo traduce a 404."""
    notificacion = Notificacion.objects.get(id=int(id))
    return notificacion


def eliminar_notificacion(id):
    """Devuelve (success: bool, message: str).

    Ya no manda el push "Notificacion eliminada:" a todos los dispositivos:
    borrar un registro del admin no es algo que le interese a los usuarios.
    """
    try:
        Notificacion.objects.get(id=id).delete()
        return True, "Se ha eliminado la notificación exitosamente."
    except Notificacion.DoesNotExist:
        return False, "La notificación no fue encontrada en la base de datos."


def obtener_notificacion(pk):
    """Puede propagar Notificacion.DoesNotExist — la vista lo traduce a 404."""
    return Notificacion.objects.get(id=pk)


def actualizar_estado_notificacion(id, estado):
    notificacion = Notificacion.objects.get(id=id)
    notificacion.estado = estado
    notificacion.save()


def enviar_notificacion_segmentada(pk):
    """"Enviar ahora" de una programada: sale fuera de su horario y cuenta
    igual que un envío del job (consume el slot del día)."""
    notificacion = Notificacion.objects.get(id=pk)
    enviar_push(notificacion, asincrono=True)
    Notificacion.objects.filter(pk=pk).update(
        veces_enviada=F('veces_enviada') + 1, ultimo_envio=timezone.now())


def list_notificaciones_masivas():
    """Listado completo para el admin: incluye las que aún no se han enviado.
    Lo que ven las apps sale de `notificaciones_visibles`."""
    return NotificacionMasiva.objects.prefetch_related('profesiones').order_by('-id')


def notificaciones_visibles(user):
    """Masivas que puede ver en su app el usuario del token.

    Los tres criterios pedidos:
      1. Fecha de registro: nada anterior a su alta. Se compara contra la fecha
         de ENVÍO, no la de creación — si estabas registrado cuando salió, te
         llega, aunque se hubiese redactado antes.
      2. Tipo de app (`dirigida_a`).
      3. Profesión, solo para proveedores. Se evalúa AL LEER, así que un
         proveedor que obtiene la profesión después igual la ve. Sin
         profesiones configuradas = para todos los proveedores.
    """
    from catalog.models import Profesion_Proveedor

    datos = Datos.objects.filter(user=user).select_related('tipo').first()
    if datos is None:
        return NotificacionMasiva.objects.none()

    qs = (NotificacionMasiva.objects
          .filter(estado=True, enviada_en__isnull=False)
          .filter(enviada_en__gte=datos.fecha_creacion))

    if datos.tipo and datos.tipo.name == 'Proveedor':
        qs = qs.filter(dirigida_a__in=[DIRIGIDA_AMBAS, DIRIGIDA_PROVEEDOR])
        mis_profesiones = (Profesion_Proveedor.objects
                           .filter(proveedor__user_datos=datos, estado=True)
                           .values('profesion_id'))
        qs = qs.filter(Q(profesiones__isnull=True) | Q(profesiones__in=Subquery(mis_profesiones)))
    else:
        qs = qs.filter(dirigida_a__in=[DIRIGIDA_AMBAS, DIRIGIDA_SOLICITANTE])

    return qs.prefetch_related('profesiones').distinct().order_by('-enviada_en')


def _item_masiva(notif, estado):
    """Normaliza una NotificacionMasiva + su estado (o None si nunca se
    tocó) al shape común del feed. `tipo`+`id` es la clave compuesta que el
    cliente manda de vuelta a marcar-leída/ocultar."""
    return {
        "tipo": "masiva",
        "subtipo": "aviso",
        "id": notif.id,
        "titulo": notif.titulo,
        "descripcion": notif.descripcion,
        "imagen": notif.imagen.url if notif.imagen else None,
        "ruta": notif.ruta or "",
        "fecha": notif.enviada_en,
        "leida": bool(estado and estado.leida_en),
        "leida_en": estado.leida_en if estado else None,
    }


def _item_individual(notif):
    return {
        "tipo": "individual",
        "subtipo": notif.tipo,
        "id": notif.id,
        "titulo": notif.titulo,
        "descripcion": notif.descripcion,
        "imagen": notif.imagen.url if notif.imagen else None,
        "ruta": notif.ruta or "",
        "fecha": notif.fecha_creacion,
        "leida": notif.leida_en is not None,
        "leida_en": notif.leida_en,
    }


def feed_notificaciones(user):
    """Todo lo que ve el usuario en su pestaña Notificaciones: masivas
    (con su estado por usuario) + eventos individuales, normalizados a un
    shape común y mezclados por fecha. Devuelve (items, counts), con los
    contadores calculados sobre la lista completa (no la que filtre la
    pestaña activa en el cliente) para que los badges de pestaña sean
    correctos sin importar cuál esté activa."""
    masivas = list(notificaciones_visibles(user))
    estados = {
        e.notificacion_id: e
        for e in NotificacionMasivaEstado.objects.filter(user=user, notificacion__in=masivas)
    }
    items = [
        _item_masiva(m, estados.get(m.id))
        for m in masivas
        if not (estados.get(m.id) and estados[m.id].oculta)
    ]

    individuales = NotificacionIndividual.objects.filter(user=user, oculta=False)
    items += [_item_individual(n) for n in individuales]

    items.sort(key=lambda it: it["fecha"], reverse=True)
    no_leidas = sum(1 for it in items if not it["leida"])
    counts = {"todas": len(items), "no_leidas": no_leidas, "leidas": len(items) - no_leidas}
    return items, counts


def marcar_leida(user, tipo, id):
    if tipo == "masiva":
        estado, _creado = NotificacionMasivaEstado.objects.get_or_create(notificacion_id=id, user=user)
        if estado.leida_en is None:
            estado.leida_en = timezone.now()
            estado.save(update_fields=["leida_en"])
    elif tipo == "individual":
        NotificacionIndividual.objects.filter(
            id=id, user=user, leida_en__isnull=True,
        ).update(leida_en=timezone.now())
    else:
        raise ValueError(f"Tipo de notificación inválido: {tipo!r}")


def ocultar_notificacion(user, tipo, id):
    """"Eliminar" desde la app: oculta solo para este usuario. Una masiva es
    de muchos destinatarios, así que nunca se borra la fila compartida —
    eso sigue siendo `eliminar_notificacion_masiva`, exclusivo del admin."""
    if tipo == "masiva":
        NotificacionMasivaEstado.objects.update_or_create(
            notificacion_id=id, user=user, defaults={"oculta": True},
        )
    elif tipo == "individual":
        NotificacionIndividual.objects.filter(id=id, user=user).update(oculta=True)
    else:
        raise ValueError(f"Tipo de notificación inválido: {tipo!r}")


def crear_notificacion_masiva(data, files):
    """Crea una masiva. Devuelve (notificacion, data: dict).

    Sin `programada_para` sale en el acto; con hora queda pendiente y la recoge
    el job. Ya no se hace rollback borrando la notificación si FCM falla: que
    el push no salga no es motivo para destruir lo que el admin acaba de
    redactar, y para eso está el botón "enviar ahora".
    """
    programada = _fecha(data, 'programada_para')
    notificacion = NotificacionMasiva.objects.create(
        nombre=data.get('nombre'),
        titulo=data.get('titulo'),
        descripcion=data.get('descripcion'),
        dirigida_a=data.get('dirigida_a') or DIRIGIDA_AMBAS,
        ruta=data.get('ruta'),
        imagen=files.get('imagen'),
        programada_para=programada,
    )
    aplicar_profesiones(notificacion, data)

    if programada is not None:
        cuando = timezone.localtime(programada).strftime('%d/%m/%Y %H:%M')
        return notificacion, {"success": True, "message": f"Notificación programada para el {cuando}."}

    notificacion.enviada_en = timezone.now()
    notificacion.save(update_fields=['enviada_en'])
    enviados = enviar_push(notificacion, asincrono=True)
    return notificacion, {
        "success": True,
        "message": f"Notificación creada y enviada a {enviados} dispositivo(s).",
    }


def actualizar_notificacion_masiva(id, data):
    """Puede propagar NotificacionMasiva.DoesNotExist — la vista lo
    traduce a 404."""
    return NotificacionMasiva.objects.get(id=int(id))


def eliminar_notificacion_masiva(id):
    """Devuelve (success: bool, message: str). Sin push al borrar, igual que
    `eliminar_notificacion`."""
    try:
        NotificacionMasiva.objects.get(id=id).delete()
        return True, "Se ha eliminado la notificación exitosamente."
    except NotificacionMasiva.DoesNotExist:
        return False, "La notificación no fue encontrada en la base de datos."


def obtener_notificacion_masiva(pk):
    """Puede propagar NotificacionMasiva.DoesNotExist — la vista lo traduce a 404."""
    return NotificacionMasiva.objects.get(id=pk)


def actualizar_estado_notificacion_masiva(id, estado):
    notificacion = NotificacionMasiva.objects.get(id=id)
    notificacion.estado = estado
    notificacion.save()


def enviar_notificacion_masiva_segmentada(pk):
    """"Enviar ahora" de una masiva. Además de mandar el push la marca como
    enviada, que es lo que la hace visible en la lista in-app y lo que evita
    que el job la vuelva a mandar si tenía hora programada."""
    notificacion = NotificacionMasiva.objects.get(id=pk)
    enviar_push(notificacion, asincrono=True)
    if notificacion.enviada_en is None:
        NotificacionMasiva.objects.filter(pk=pk).update(enviada_en=timezone.now())


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
        thread = threading.Thread(
            target=format_email.send_email,
            args=([email], asunto, plantilla, {
                "username": user.nombres + ' ' + user.apellidos, "user": email, "password": password}),
        )
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
        thread = threading.Thread(
            target=format_email.send_email,
            args=([email], asunto, plantilla, {
                "username": user.nombres + ' ' + user.apellidos, "user": email, "profesion": profesion}),
        )
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
            thread = threading.Thread(
                target=format_email.send_email,
                args=([user_email], asunto, 'emails/enviarAlerta.html', {"username": user_dato.nombres, "contenido": texto}),
            )
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
    # nombres/apellidos vienen con espacios sueltos en la BD ("Nancy "), así que
    # se normaliza en vez de concatenar a pelo (antes salía "Juan CarlosCarrillo").
    titles = 'Nuevo Mensaje de ' + ' '.join(
        p for p in [(remitente_nombre.nombres or '').strip(), (remitente_nombre.apellidos or '').strip()] if p)
    bodys = mensaje
    # Un remitente = una conversación para quien recibe: con este tag la bandeja
    # muestra una sola notificación con el último mensaje en vez del historial.
    tag = f"chat-{remitente_nombre.id}"
    # OJO: la ruta es la de la app que RECIBE el push, no la de la que lo manda.
    # Solicitante usa /main-tabs/..., Proveedor usa /main/... Estaban al revés y
    # el tap en la notificación no navegaba a ningún lado (ninguna de las dos
    # apps tiene ruta comodín, así que Angular no matcheaba nada).
    ruta = ""
    if es_solicitante:
        # Lo manda el solicitante; el destinatario es el proveedor.
        ruta = "/main/chat"
        dato_prov = Datos.objects.get(user_id=user_id)
        dato_id_prov = dato_prov.user_id
        devices = FCMDevice.objects.filter(active=True, user_id=dato_id_prov)
        tokend = devices.values_list('registration_id', flat=True)
        tokens = list(tokend)
        data = {"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}
        send_notificationF(tokens, titles, bodys, data, tag=tag)
    else:
        # Destinatario solicitante (rama muerta hoy, ver docstring).
        ruta = "/main-tabs/chat"
        data = {"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}
        send_notificationF(tokens, titles, bodys, data, tag=tag)  # noqa: F821 — bug preservado, ver docstring

    return user_id


def notificar_general(user, message, title):
    """Sin consumidor real confirmado en ningún frontend."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    devices = FCMDevice.objects.filter(active=True, user_id=user)
    tokend = devices.values_list('registration_id', flat=True)
    # "Historial" no era una ruta, era el nombre de la vista vieja: el router
    # de la app no la resolvía y la notificación no navegaba a ningún lado.
    data = {"ruta": "/main-tabs/solicitudes", "descripcion": "Proveedor Interesado"}
    tokens = list(tokend)
    send_notificationF(tokens, title, message, data)
    return user


def notificar_chat_proveedor(remitente_id, get_usuario_id, mensaje, url):
    """Manda el push del mensaje de chat al solicitante. Devuelve
    (data, http_status), con data = {"enviado": bool, ...}.

    El mensaje en sí no pasa por acá: lo escribe la app directo en Firebase
    Realtime DB. Esto es solo el aviso, así que no poder mandarlo no invalida
    el envío del mensaje — por eso "sin dispositivos" es 200 y no un error.
    Los 404 que quedan sí son peticiones mal formadas (ids que no existen)."""
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    try:
        remitente_nombre_prov = Datos.objects.get(user_id=remitente_id)
    except Datos.DoesNotExist:
        return {"error": "Remitente not found"}, 404

    titles = "Nuevo Mensaje de " + (remitente_nombre_prov.nombres or '').strip()
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
    tokens = list(devices.values_list("registration_id", flat=True))
    if not tokens:
        # Que el destinatario no tenga dispositivos no es un fallo de la
        # petición: el mensaje ya se guardó en Firebase y llegó igual, solo no
        # hay a quién mandarle el push (pasa siempre que el otro lado se probó
        # en navegador, donde no se registra token FCM). Antes esto devolvía
        # 404 y la app lo pintaba como error rojo en consola. La otra dirección
        # (`notificar_chat_solicitante`) nunca falló en este caso: devuelve 200
        # con la lista de tokens vacía.
        return {"enviado": False, "motivo": "sin dispositivos"}, 200

    # El destinatario es el solicitante: su app usa /main-tabs/... (la del
    # proveedor usa /main/...). Iba con la ruta del proveedor y el tap en la
    # notificación no navegaba a ningún lado.
    data = {"url": url, "ruta": "/main-tabs/chat", "descripcion": "Tiene un Mensaje nuevo"}
    try:
        # Mismo espacio de nombres que el otro sentido del chat
        # (`notificar_chat_solicitante`): el Datos.id del remitente.
        send_notificationF(tokens, titles, bodys, data, tag=f"chat-{remitente_nombre_prov.id}")
    except Exception:
        pass  # el original también ignoraba errores de envío acá

    # Antes devolvía el `get_usuario_id` pelado; se cambia por el mismo dict de
    # la rama sin dispositivos para que el endpoint conteste siempre igual.
    # Ningún frontend lee el cuerpo (los dos hacen `.subscribe()` sin handlers).
    return {"enviado": True}, 200
