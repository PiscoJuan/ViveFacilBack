import logging

from django.db.models import Case, CharField, Q, Value, When
from django.utils import timezone
from rest_framework import status

from accounts.models import Datos, Proveedor, Solicitante
from catalog.models import Servicio
from solicitudes.models import Envio_Interesados, Solicitud, Tipo_Pago, Ubicacion

logger = logging.getLogger(__name__)


def _fecha_con_zona(fecha):
    """La app manda la fecha sin zona ("2026-08-27 11:55:00") y con USE_TZ
    activo Django avisa por RuntimeWarning en cada solicitud. Se interpreta en
    la zona del proyecto (America/Guayaquil) y se devuelve aware."""
    from django.utils.dateparse import parse_datetime

    if not isinstance(fecha, str):
        return fecha
    parseada = parse_datetime(fecha)
    if parseada is None:
        return fecha  # formato inesperado: que lo resuelva el ORM como antes
    return timezone.make_aware(parseada) if timezone.is_naive(parseada) else parseada


def _crear_solicitud_con_reintento(**campos):
    """Un `OperationalError` (2013 'Lost connection', 2006 'server has gone
    away') deja la conexión inservible: se cierra para forzar una nueva y se
    reintenta una vez.

    Antes de reintentar hay que mirar si la fila alcanzó a insertarse — la
    conexión puede caerse después de que MySQL aplicó el INSERT — o se crearían
    dos solicitudes. `Solicitud.ubicacion` es OneToOne, así que la ubicación
    recién creada identifica la fila sin ambigüedad; el corte por tiempo cubre
    el caso de una Ubicacion reutilizada por `get_or_create`.
    """
    from django.db import OperationalError, connection

    try:
        return Solicitud.objects.create(**campos)
    except OperationalError:
        logger.warning("crear_solicitud: conexión con MySQL caída en el INSERT, reintentando", exc_info=True)
        connection.close()

        ya_creada = Solicitud.objects.filter(
            ubicacion=campos["ubicacion"], solicitante=campos["solicitante"]
        ).order_by("-id").first()
        if ya_creada and ya_creada.fecha_creacion and (
            timezone.now() - ya_creada.fecha_creacion
        ).total_seconds() < 120:
            logger.info("crear_solicitud: el INSERT sí se había aplicado, se reutiliza", extra={"solicitud_id": ya_creada.id})
            return ya_creada

        return Solicitud.objects.create(**campos)


# --- Los 9 listados casi-duplicados de "mis solicitudes filtradas por
# estado" se dejan sin colapsar a propósito. Cada función devuelve un
# queryset sin evaluar, para que la vista decida si pagina o no. ---


def solicitudes_pendientes_queryset(correo):
    return Solicitud.objects.all().filter(
        solicitante__user_datos__user__email=correo, adjudicar=False,
        proveedor__isnull=True, termino__isnull=True, fecha_expiracion__gt=timezone.now(),
    ).order_by("-id")


def solicitudes_pasadas_queryset(correo):
    """Variante sin paginar, filtra por correo."""
    return Solicitud.objects.filter(
        Q(solicitante__user_datos__user__email=correo)
        & (Q(termino="finalizado") | Q(termino="cancelado") | Q(fecha_expiracion__lt=timezone.now(), adjudicar=False))
    ).order_by("-id")


def solicitudes_pasadas_pag_queryset(user, ordenar):
    """Filtra por `user` en vez de correo — endpoint distinto al de arriba
    pese al nombre parecido, se preserva la diferencia tal cual."""
    orden = "id" if ordenar == "asc" else "-id"
    return Solicitud.objects.all().filter(
        Q(solicitante__user_datos__user=user)
        & (Q(termino="finalizado") | Q(termino="cancelado") | Q(fecha_expiracion__lt=timezone.now(), adjudicar=False))
    ).order_by(orden)


def solicitudes_pagadas_queryset(correo):
    return Solicitud.objects.filter(
        solicitante__user_datos__user__email=correo, adjudicar=True, pagada=True, termino="pagado",
    ).order_by("-id")


def solicitudes_no_pagadas_queryset(correo):
    return Solicitud.objects.filter(
        solicitante__user_datos__user__email=correo, adjudicar=True, pagada=False, proveedor__isnull=False,
    ).order_by("-id")


def solicitudes_en_proceso_queryset(user, ordenar):
    resultado = Solicitud.objects.filter(solicitante__user_datos__user=user).annotate(
        estado_proceso=Case(
            When(adjudicar=False, proveedor__isnull=True, termino__isnull=True,
                 fecha_expiracion__gt=timezone.now(), then=Value("ABIERTA")),
            When(adjudicar=True, pagada=True, termino="pagado", then=Value("POR FINALIZAR")),
            When(adjudicar=True, pagada=False, proveedor__isnull=False, then=Value("POR PAGAR")),
            output_field=CharField(),
        )
    ).filter(estado_proceso__isnull=False)
    return resultado.order_by("id" if ordenar == "asc" else "-id")


def todas_solicitudes_admin_queryset(estado=None, tipo_pago=None, servicio=None, texto=None,
                                      fecha_inicio=None, fecha_fin=None):
    """Listado admin de TODAS las solicitudes (a diferencia de las de
    arriba, no filtra por solicitante), con el mismo `estado_proceso`
    anotado que `solicitudes_en_proceso_queryset` más CANCELADO/FINALIZADO/
    EXPIRADA para cubrir el ciclo de vida completo."""
    now = timezone.now()
    qs = Solicitud.objects.all().annotate(
        estado_proceso=Case(
            When(termino="cancelado", then=Value("CANCELADO")),
            When(termino="finalizado", then=Value("FINALIZADO")),
            When(adjudicar=True, pagada=True, termino="pagado", then=Value("POR FINALIZAR")),
            When(adjudicar=True, pagada=False, proveedor__isnull=False, then=Value("POR PAGAR")),
            When(adjudicar=False, proveedor__isnull=True, termino__isnull=True,
                 fecha_expiracion__gt=now, then=Value("ABIERTA")),
            When(adjudicar=False, proveedor__isnull=True, termino__isnull=True,
                 fecha_expiracion__lte=now, then=Value("EXPIRADA")),
            default=Value("OTRO"),
            output_field=CharField(),
        )
    )
    if estado:
        qs = qs.filter(estado_proceso=estado)
    if tipo_pago:
        qs = qs.filter(tipo_pago__nombre__iexact=tipo_pago)
    if servicio:
        qs = qs.filter(servicio_id=servicio)
    if texto:
        qs = qs.filter(
            Q(solicitante__user_datos__user__email__icontains=texto)
            | Q(solicitante__user_datos__nombres__icontains=texto)
            | Q(solicitante__user_datos__apellidos__icontains=texto)
            | Q(proveedor__user_datos__user__email__icontains=texto)
            | Q(proveedor__user_datos__nombres__icontains=texto)
            | Q(proveedor__user_datos__apellidos__icontains=texto)
        )
    if fecha_inicio and fecha_fin:
        qs = qs.filter(fecha_creacion__gte=fecha_inicio, fecha_creacion__lte=fecha_fin)
    return qs.order_by("-id")


def solicitud_admin_detalle(pk):
    """Una sola solicitud desde el mismo queryset anotado que el listado
    admin (necesario para que 'estado_proceso' exista al serializar).
    Lanza Solicitud.DoesNotExist si no existe."""
    return todas_solicitudes_admin_queryset().get(pk=pk)


# --- Resto de endpoints solicitante de solicitudes/ ---


def crear_solicitud(data, files):
    """Devuelve (solicitud_o_None, data: dict)."""
    import threading

    from core.email import FormatEmail
    from core.firebase import send_notificationF_async

    resp = {}
    desc = data.get("descripcion")
    foto_desc = files.get("foto_descripcion")
    fecha_exp = _fecha_con_zona(data.get("fecha"))
    user = data.get("solicitante")
    servicio_id = data.get("servicio")
    pago_name = data.get("tipo_pago")
    proveedores_id = data.get("proveedores")
    lat = data.get("latitud")
    alt = data.get("altitud")
    drc = data.get("direccion")
    ref = data.get("referencia")
    foto_ubic = files.get("foto_ubicacion")

    logger.info(
        "crear_solicitud: request recibido",
        extra={"solicitante": user, "servicio": servicio_id, "tipo_pago": pago_name, "proveedores": proveedores_id},
    )

    try:
        ubic, _ = Ubicacion.objects.get_or_create(
            latitud=lat, altitud=alt, direccion=drc, referencia=ref, foto_ubicacion=foto_ubic
        )
    except Exception as e:
        logger.error("crear_solicitud: falló creando/obteniendo Ubicacion", extra={"lat": lat, "alt": alt, "direccion": drc}, exc_info=True)
        resp["message"] = "No se pudo obtener o crear al objeto Ubicación: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        solic = Solicitante.objects.get(id=user)
    except Exception as e:
        logger.error("crear_solicitud: falló obteniendo Solicitante", extra={"solicitante_id": user}, exc_info=True)
        resp["message"] = "No se pudo obtener al solicitante en la base de datos: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        service = Servicio.objects.get(id=servicio_id)
    except Exception as e:
        logger.error("crear_solicitud: falló obteniendo Servicio", extra={"servicio_id": servicio_id}, exc_info=True)
        resp["message"] = "No se pudo obtener al objeto Servicio en la base de datos: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        t_pago, _ = Tipo_Pago.objects.get_or_create(nombre=pago_name)
    except Exception as e:
        logger.error("crear_solicitud: falló creando/obteniendo Tipo_Pago", extra={"tipo_pago": pago_name}, exc_info=True)
        resp["message"] = "No se pudo obtener o crear al objeto Tipo_Pago: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        solicitud = _crear_solicitud_con_reintento(
            descripcion=desc, fecha_expiracion=fecha_exp, solicitante=solic, ubicacion=ubic,
            tipo_pago=t_pago, servicio=service, foto_descripcion=foto_desc, rating=0,
        )
    except Exception as e:
        # El original tenía un `if 'solicitud' in locals(): solicitud.delete()`
        # acá, pero como la excepción ocurre durante el propio `.create()`,
        # `solicitud` nunca llega a asignarse — esa rama nunca se ejecuta,
        # se omite en vez de replicar código muerto.
        logger.error("crear_solicitud: falló creando Solicitud", extra={"descripcion": desc, "fecha_expiracion": fecha_exp}, exc_info=True)
        resp["message"] = "No se pudo crear al objeto Solicitud: " + str(e)
        resp["success"] = False
        return None, resp

    logger.info("crear_solicitud: Solicitud creada, procesando proveedores", extra={"solicitud_id": solicitud.id})

    try:
        proveedores_id = proveedores_id.split(",")
    except Exception as e:
        logger.error(
            "crear_solicitud: falló haciendo split de proveedores",
            extra={"solicitud_id": solicitud.id, "proveedores": proveedores_id},
            exc_info=True,
        )
        solicitud.delete()
        resp["message"] = "Ha ocurrido un error al hacer split de la lista de proveedores: " + str(e)
        resp["success"] = False
        return None, resp

    titles = "Solicitud Recibida del servicio " + solicitud.servicio.nombre
    bodys = "¡Dale un vistazo!"
    # Recién creada: el proveedor todavía no la aceptó, así que vive en home
    # (las pendientes por aceptar), no en la pestaña de solicitudes tomadas.
    notif_data = {"ruta": "/main/home", "descripcion": "Se ha recibido una solicitud de servicio."}

    from fcm_django.models import FCMDevice

    for proveedor_id in proveedores_id:
        try:
            prov = Proveedor.objects.get(id=proveedor_id)
        except Exception as e:
            logger.error(
                "crear_solicitud: falló obteniendo Proveedor",
                extra={"solicitud_id": solicitud.id, "proveedor_id": proveedor_id},
                exc_info=True,
            )
            solicitud.delete()
            resp["message"] = f"Error al obtener un proveedor con ID {proveedor_id}: {str(e)}"
            resp["success"] = False
            return None, resp

        try:
            # Ya no se guarda en una variable: solo servía para el `.delete()` de
            # abajo, que se sacó junto con el borrado de la solicitud.
            Envio_Interesados.objects.create(solicitud=solicitud, proveedor=prov)
        except Exception as e:
            logger.error(
                "crear_solicitud: falló creando Envio_Interesados",
                extra={"solicitud_id": solicitud.id, "proveedor_id": proveedor_id},
                exc_info=True,
            )
            solicitud.delete()
            resp["message"] = f"Error al crear Envio_Interesados para proveedor {proveedor_id}: {str(e)}"
            resp["success"] = False
            return None, resp

        try:
            datos_prov = Datos.objects.get(id=prov.user_datos_id)
        except Exception:
            # Sin los datos del proveedor no hay a quién notificar ni a quién
            # mandarle el email, pero la solicitud queda igual: ya está creada y
            # el proveedor la ve al entrar a la app.
            logger.error(
                "crear_solicitud: falló obteniendo los Datos del proveedor",
                extra={"solicitud_id": solicitud.id, "proveedor_id": proveedor_id},
                exc_info=True,
            )
            continue

        try:
            devices = FCMDevice.objects.filter(active=True, user_id=datos_prov.user.id)
            tokens = list(devices.values_list("registration_id", flat=True))
            logger.info(
                "crear_solicitud: notificando a proveedor",
                extra={"solicitud_id": solicitud.id, "proveedor_id": proveedor_id, "num_dispositivos": len(tokens)},
            )
            # En segundo plano: es un POST por token con timeout de 15s, y en
            # línea alargaba el request hasta que el cliente lo abandonaba.
            send_notificationF_async(tokens, titles, bodys, notif_data)
        except Exception:
            # Antes esto hacía envio_interesados.delete() + solicitud.delete():
            # un problema de red con Google le borraba la solicitud al usuario.
            # La notificación es accesoria, la solicitud es el dato de negocio.
            logger.error(
                "crear_solicitud: falló notificando a proveedor",
                extra={"solicitud_id": solicitud.id, "proveedor_id": proveedor_id},
                exc_info=True,
            )

        try:
            format_email = FormatEmail()
            threading.Thread(
                target=format_email.send_email,
                args=(
                    [datos_prov.user.email],
                    "Nueva solicitud de servicio",
                    "emails/nuevaSolicitudProveedor.html",
                    {
                        "username": f"{datos_prov.nombres} {datos_prov.apellidos}",
                        "solicitante_name": f"{solic.user_datos.nombres} {solic.user_datos.apellidos}",
                        "servicio": solicitud.servicio.nombre,
                        "descripcion": solicitud.descripcion,
                        "direccion": ubic.direccion,
                    },
                ),
            ).start()
        except Exception:
            # Igual que el push: avisar es accesorio, la solicitud ya está creada.
            logger.exception(
                "crear_solicitud: falló enviando email de notificación al proveedor",
                extra={"solicitud_id": solicitud.id, "proveedor_id": proveedor_id},
            )

    logger.info(
        "crear_solicitud: creada y enviada a todos los proveedores OK",
        extra={"solicitud_id": solicitud.id, "num_proveedores": len(proveedores_id)},
    )
    resp["success"] = True
    return solicitud, resp


def adjudicar_solicitud(solicitud_id, proveedor_user_id, request_data):
    """Devuelve (solicitud_o_None, data: dict)."""
    from api.serializers import SolicitudSerializer
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    data = {}
    try:
        proveedor = Proveedor.objects.get(user_datos__user__id=int(proveedor_user_id))
        solicitud = Solicitud.objects.get(id=int(solicitud_id))
        solicitud.proveedor = proveedor
        solicitud.save()
        serializer = SolicitudSerializer(solicitud, data=request_data, partial=True)
        if not serializer.is_valid():
            data["message"] = "La solicitud no es válida."
            data["success"] = False
            return None, data
        serializer.save()

        titles = "Solicitud Adjudicada del servicio " + solicitud.servicio.nombre
        bodys = "¡Dale un vistazo!"
        devices = FCMDevice.objects.filter(active=True, user__id=proveedor.user_datos.user.id)
        tokens = list(devices.values_list("registration_id", flat=True))
        notif_data = {
            "ruta": "/main/solicitudes",
            "descripcion": "Se le ha adjudicado el siguiente servicio: " + solicitud.servicio.nombre,
        }
        send_notificationF(tokens, titles, bodys, notif_data)

        data["message"] = "Solicitud adjudicada exitosamente!."
        data["success"] = True
        data["solicitud"] = serializer.data
        return solicitud, data
    except Exception as e:
        data["message"] = "No se pudo adjudicar la solicitud: " + str(e)
        data["success"] = False
        return None, data


def envio_interesados(solicitud_id):
    """Proveedores que respondieron la solicitud: los que ofertaron y los que la
    rechazaron. Los rechazados vienen con `rechazada: true` y sin oferta; la app
    del solicitante los muestra en una sección aparte."""
    from api.serializers import Envio_InteresadosSerializer
    from django.db.models import Q

    envio_interesado = Envio_Interesados.objects.filter(
        Q(interesado=True) | Q(rechazada=True), solicitud=solicitud_id)
    serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
    datos = []
    for solicitud in serializer.data:
        datos.append({
            "id": solicitud["proveedor"]["user_datos"]["user"]["id"],
            "username": solicitud["proveedor"]["user_datos"]["user"]["username"],
            "nombres": solicitud["proveedor"]["user_datos"]["nombres"],
            "apellidos": solicitud["proveedor"]["user_datos"]["apellidos"],
            "ciudad": solicitud["proveedor"]["user_datos"]["ciudad"],
            "telefono": solicitud["proveedor"]["user_datos"]["telefono"],
            "genero": solicitud["proveedor"]["user_datos"]["genero"],
            "foto": solicitud["proveedor"]["user_datos"]["foto"],
            "oferta": solicitud["oferta"],
            "descripcion": solicitud["proveedor"]["descripcion"],
            "rating": solicitud["proveedor"]["rating"],
            "servicios": solicitud["proveedor"]["servicios"],
            "rechazada": solicitud.get("rechazada", False),
            "fecha_rechazo": solicitud.get("fecha_rechazo"),
            "motivo_rechazo": solicitud.get("motivo_rechazo"),
        })
    return datos


# --- Solicituds: multi-rol, compartido con proveedor ---


def listar_todas_solicitudes():
    from api.serializers import SolicitudSerializer

    solicitud = Solicitud.objects.all().filter()
    return SolicitudSerializer(solicitud, many=True).data


def solicitud_por_servicio_pendientes(user, id_servicio):
    envio_interesados = Envio_Interesados.objects.filter(
        solicitud__servicio=id_servicio, solicitud__estado=True,
        proveedor__user_datos__user=user, interesado=False, rechazada=False,
    ).order_by("-fecha_creacion")
    return [ei.solicitud for ei in envio_interesados]


def rechazar_solicitud(solicitud_id, proveedor_user_id, motivo=None):
    """El proveedor descarta la solicitud. No se borra el Envio_Interesados: se
    marca, para que el solicitante y el admin vean que la recibió y la rechazó.
    Devuelve (data, http_status)."""
    try:
        envio = Envio_Interesados.objects.get(
            solicitud_id=solicitud_id, proveedor__user_datos__user_id=proveedor_user_id)
    except Envio_Interesados.DoesNotExist:
        return {"success": False, "message": "Esta solicitud no está asignada a este proveedor."}, 404

    if envio.interesado:
        return {"success": False, "message": "Ya enviaste una oferta para esta solicitud."}, 400

    envio.rechazada = True
    envio.fecha_rechazo = timezone.now()
    envio.motivo_rechazo = (motivo or "").strip()[:255] or None
    envio.save(update_fields=["rechazada", "fecha_rechazo", "motivo_rechazo"])

    logger.info(
        "rechazar_solicitud: solicitud rechazada",
        extra={"solicitud_id": solicitud_id, "proveedor_user_id": proveedor_user_id, "con_motivo": bool(envio.motivo_rechazo)},
    )
    return {"success": True, "message": "Solicitud rechazada."}, 200


def obtener_solicitud_por_id(solicitud_id):
    from api.serializers import SolicitudSerializer

    solicitud = Solicitud.objects.get(id=solicitud_id)
    return SolicitudSerializer(solicitud).data


def envio_interesado_lectura(solicitud_id):
    from api.serializers import Envio_InteresadosSerializer

    envio_interesado = Envio_Interesados.objects.all().filter(solicitud=solicitud_id, interesado=False)
    return Envio_InteresadosSerializer(envio_interesado, many=True).data


def actualizar_envio_interesado(solicitud_id, user_proveedor, request_data):
    """Devuelve (data, http_status)."""
    import threading

    from api.serializers import Envio_InteresadosSerializer
    from core.email import FormatEmail
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    solicitud = Solicitud.objects.get(id=solicitud_id)
    es_nuevo = solicitud.adjudicar
    solicitante = solicitud.solicitante
    envio_interesado = Envio_Interesados.objects.all().get(
        solicitud=solicitud_id, proveedor__user_datos__user__username=user_proveedor)
    serializer = Envio_InteresadosSerializer(envio_interesado, data=request_data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, status.HTTP_400_BAD_REQUEST
    serializer.save()

    if es_nuevo:
        titles = "Ha cambiado el precio del servicio de " + solicitud.servicio.nombre + " que solicitaste."
        descripcion = "Ha cambiado el precio del siguiente servicio: " + solicitud.servicio.nombre
    else:
        titles = "Tienes una nueva oferta en el servicio de " + solicitud.servicio.nombre + " que solicitaste."
        descripcion = "Ha recibido una oferta en el siguiente servicio: " + solicitud.servicio.nombre
    bodys = "¡Dale un vistazo!"
    devices = FCMDevice.objects.filter(active=True, user__username=solicitante.user_datos.user.email)
    tokens = list(devices.values_list("registration_id", flat=True))
    # Va al solicitante: su pestaña de solicitudes es /main-tabs/solicitudes.
    # "/historial" era la vista vieja (hoy solo redirige).
    send_notificationF(tokens, titles, bodys, {"ruta": "/main-tabs/solicitudes", "descripcion": descripcion})

    try:
        format_email = FormatEmail()
        threading.Thread(
            target=format_email.send_email,
            args=(
                [solicitante.user_datos.user.email],
                titles,
                "emails/ofertaSolicitante.html",
                {
                    "username": f"{solicitante.user_datos.nombres} {solicitante.user_datos.apellidos}",
                    "proveedor_name": f"{envio_interesado.proveedor.user_datos.nombres} {envio_interesado.proveedor.user_datos.apellidos}",
                    "servicio": solicitud.servicio.nombre,
                    "oferta": envio_interesado.oferta,
                    "es_cambio": es_nuevo,
                },
            ),
        ).start()
    except Exception:
        logger.exception(
            "actualizar_envio_interesado: falló enviando email de notificación al solicitante",
            extra={"solicitud_id": solicitud_id},
        )

    return serializer.data, status.HTTP_200_OK


def eliminar_envio_interesado(solicitud_id, user_proveedor):
    """Réplica exacta de Envio.delete (api/views.py:3074-3087), incluido el
    `except:` desnudo original."""
    try:
        instance = Envio_Interesados.objects.get(
            solicitud=solicitud_id, proveedor__user_datos__user__username=user_proveedor)
        instance.delete()
        return {"success": True, "message": "Se ha eliminado el objeto Envio_Interesados correctamente de la base de datos"}
    except:
        return {"success": False, "message": "No se ha encontrado el objeto Envio_Interesados en la base de datos"}


def _interesados_base_queryset(id_proveedor_user_datos):
    return Envio_Interesados.objects.filter(
        proveedor__user_datos_id=id_proveedor_user_datos, interesado=True)


def interesados_pag_queryset(id_proveedor_user_datos):
    return _interesados_base_queryset(id_proveedor_user_datos).order_by("-fecha_creacion")


def interesados_en_proceso_pag_queryset(id_proveedor_user_datos, ordenar):
    base = _interesados_base_queryset(id_proveedor_user_datos)
    now = timezone.now()
    pasadas_q = Q(solicitud__termino__in=["finalizado", "cancelado"]) | Q(
        solicitud__fecha_expiracion__lt=now, solicitud__adjudicar=False)
    qs = base.exclude(pasadas_q)
    return qs.order_by("fecha_creacion" if ordenar == "asc" else "-fecha_creacion")


def interesados_pasadas_pag_queryset(id_proveedor_user_datos, ordenar):
    base = _interesados_base_queryset(id_proveedor_user_datos)
    now = timezone.now()
    qs = base.filter(
        Q(solicitud__termino__in=["finalizado", "cancelado"]) |
        Q(solicitud__fecha_expiracion__lt=now, solicitud__adjudicar=False)
    )
    return qs.order_by("fecha_creacion" if ordenar == "asc" else "-fecha_creacion")


def actualizar_solicitud(solicitud_id, request_data):
    """Devuelve (data: dict, http_status: int)."""
    from api.serializers import SolicitudSerializer
    from core.firebase import send_notificationF
    from fcm_django.models import FCMDevice

    data = {}
    try:
        solicitud = Solicitud.objects.get(id=solicitud_id)

        # El proveedor califica al cliente: solo en solicitudes finalizadas, una sola
        # vez. Es una rama independiente de "finalizar" (no cambia estado ni acumula
        # tramites/dinero), por eso retorna antes del bloque pesado de más abajo.
        if request_data.get("rating_solicitante") is not None:
            rating_sol = float(request_data.get("rating_solicitante") or 0)
            ya_calificado = float(solicitud.rating_solicitante or 0) > 0
            if rating_sol > 0 and not ya_calificado and solicitud.termino == "finalizado":
                solicitud.rating_solicitante = rating_sol
                solicitud.descripcion_rating_solicitante = request_data.get("descripcion_rating_solicitante", " ")
                solicitud.save()
                sol = solicitud.solicitante
                sol.total_resenas_dejadas += 1
                sol.total_resenas_dejadas_puntos += rating_sol
                sol.save()
                return {"success": True, "message": "Calificación del cliente registrada."}, 200
            return {"success": False,
                    "message": "No se pudo calificar (ya calificada, o la solicitud no está finalizada)."}, 200

        ya_finalizada = solicitud.termino == "finalizado"  # evita contar la reseña dos veces
        solicitud.estado = request_data.get("estado", solicitud.estado)
        solicitud.pagada = request_data.get("pagada", solicitud.pagada)
        solicitud.termino = request_data.get("termino", solicitud.termino)
        solicitud.save()
        serializer = SolicitudSerializer(solicitud, data=request_data, partial=True)
        if not serializer.is_valid():
            data["message"] = "La solicitud no es válida."
            data["success"] = False
            return data, 200
        serializer.save()

        if request_data.get("termino") != "cancelado":
            proveedor = solicitud.proveedor
            solicitante = solicitud.solicitante
            solicitudes_proveedor = Solicitud.objects.filter(proveedor=proveedor)
            adjudicada = Envio_Interesados.objects.get(solicitud=solicitud, proveedor=solicitud.proveedor)
            # El rating del proveedor es una propiedad calculada; solo acumulamos los
            # totales cuando llega una reseña real (rating > 0). El proveedor que se
            # auto-finaliza manda rating 0 -> no cuenta como reseña.
            rating_val = float(request_data.get("rating") or 0)
            if rating_val > 0 and not ya_finalizada:
                proveedor.total_resenas_dejadas += 1
                proveedor.total_resenas_dejadas_puntos += rating_val
            proveedor.servicios = len(solicitudes_proveedor)
            proveedor.user_datos.tramites = proveedor.user_datos.tramites + 1
            proveedor.user_datos.dinero_invertido = proveedor.user_datos.dinero_invertido + adjudicada.oferta
            datos_solicitante = solicitante.user_datos
            datos_solicitante.tramites = datos_solicitante.tramites + 1
            datos_solicitante.dinero_invertido = datos_solicitante.dinero_invertido + adjudicada.oferta
            proveedor.save()
            datos_solicitante.save()
            datos_proveedor = proveedor.user_datos
            datos_proveedor.save()

            # Las medallas dependen de `tramites` y `dinero_invertido`, que
            # acaban de cambiar acá: este es el momento en que se ganan. Antes
            # solo se otorgaban al abrir el perfil, así que quien nunca entraba
            # no las recibía.
            # Solo al solicitante: las medallas son suyas, el proveedor gana
            # insignias (que se otorgan en `content.services.insignias_personales`).
            from content.services import otorgar_medallas
            try:
                otorgar_medallas(datos_solicitante)
            except Exception:
                # Cerrar la solicitud es el camino crítico (mueve dinero);
                # que falle una medalla no puede tumbarlo.
                logger.exception("No se pudieron otorgar medallas a datos_id=%s", datos_solicitante.id)

            if request_data.get("termino") != "pagado":
                titles = "Servicio finalizado: " + solicitud.servicio.nombre
                bodys = "¡Dale un vistazo!"
                devices = FCMDevice.objects.filter(active=True, user__username=solicitud.proveedor.user_datos.user.email)
                tokens = list(devices.values_list("registration_id", flat=True))
                notif_data = {
                    "ruta": "/main/solicitudes",
                    "descripcion": "Puede observar la solicitud " + solicitud.servicio.nombre
                    + " finalizada en la seccion de Solicitudes > PASADAS",
                }
                send_notificationF(tokens, titles, bodys, notif_data)

        data["message"] = "Solicitud actualizada exitosamente!."
        data["success"] = True
        data["solicitud"] = serializer.data
        return data, 200
    except Exception as e:
        data["message"] = "No se pudo actualizar la solicitud: " + str(e)
        data["success"] = False
        return data, 200


def historial_solicitudes_por_email(user_email):
    from api.serializers import SolicitudSerializer

    solicitudes = Solicitud.objects.all().filter(solicitante__user_datos__user__email=user_email)
    return SolicitudSerializer(solicitudes, many=True).data


def solicitud_adjudicada(solicitud_id):
    from api.serializers import Envio_InteresadosSerializer

    solicitud = Solicitud.objects.get(id=solicitud_id)
    adjudicada = Envio_Interesados.objects.all().filter(solicitud=solicitud, proveedor=solicitud.proveedor)
    return Envio_InteresadosSerializer(adjudicada, many=True).data


def interesados_por_fecha(id_proveedor_user_datos, fecha_inicio, fecha_final):
    from api.serializers import Envio_InteresadosSerializer

    envio_interesado = Envio_Interesados.objects.all().filter(
        proveedor__user_datos_id=id_proveedor_user_datos, fecha_creacion__gte=fecha_inicio,
        fecha_creacion__lte=fecha_final, interesado=True,
    ).order_by('-fecha_creacion')
    return Envio_InteresadosSerializer(envio_interesado, many=True).data


def interesados_pag_efectivo_queryset(id_proveedor_user_datos):
    return Envio_Interesados.objects.all().filter(
        proveedor__user_datos_id=id_proveedor_user_datos, interesado=True, solicitud__tipo_pago__nombre='Efectivo'
    ).order_by('-fecha_creacion')


def interesados_pag_tarjeta_queryset(id_proveedor_user_datos):
    return Envio_Interesados.objects.all().filter(
        proveedor__user_datos_id=id_proveedor_user_datos, interesado=True, solicitud__tipo_pago__nombre='Tarjeta'
    ).order_by('-fecha_creacion')


def solicitudes_pagadas_por_proveedor(id_proveedor_user_datos):
    from api.serializers import Envio_InteresadosSerializer

    envio_interesado = Envio_Interesados.objects.all().filter(
        proveedor__user_datos_id=id_proveedor_user_datos, interesado=True, solicitud__pagada=True
    ).order_by('-fecha_creacion')
    return Envio_InteresadosSerializer(envio_interesado, many=True).data
