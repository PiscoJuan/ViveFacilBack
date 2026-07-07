from django.db.models import Case, CharField, Q, Sum, Value, When
from django.utils import timezone
from rest_framework import status

from api.models import (
    Datos,
    Envio_Interesados,
    Proveedor,
    Servicio,
    Solicitante,
    Solicitud,
    Tipo_Pago,
    Ubicacion,
)

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


# --- Resto de endpoints solicitante de solicitudes/ ---


def crear_solicitud(data, files):
    """Devuelve (solicitud_o_None, data: dict)."""
    from core.firebase import send_notificationF

    resp = {}
    desc = data.get("descripcion")
    foto_desc = files.get("foto_descripcion")
    fecha_exp = data.get("fecha")
    user = data.get("solicitante")
    servicio_id = data.get("servicio")
    pago_name = data.get("tipo_pago")
    proveedores_id = data.get("proveedores")
    lat = data.get("latitud")
    alt = data.get("altitud")
    drc = data.get("direccion")
    ref = data.get("referencia")
    foto_ubic = files.get("foto_ubicacion")

    try:
        ubic, _ = Ubicacion.objects.get_or_create(
            latitud=lat, altitud=alt, direccion=drc, referencia=ref, foto_ubicacion=foto_ubic
        )
    except Exception as e:
        resp["message"] = "No se pudo obtener o crear al objeto Ubicación: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        solic = Solicitante.objects.get(id=user)
    except Exception as e:
        resp["message"] = "No se pudo obtener al solicitante en la base de datos: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        service = Servicio.objects.get(id=servicio_id)
    except Exception as e:
        resp["message"] = "No se pudo obtener al objeto Servicio en la base de datos: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        t_pago, _ = Tipo_Pago.objects.get_or_create(nombre=pago_name)
    except Exception as e:
        resp["message"] = "No se pudo obtener o crear al objeto Tipo_Pago: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        solicitud = Solicitud.objects.create(
            descripcion=desc, fecha_expiracion=fecha_exp, solicitante=solic, ubicacion=ubic,
            tipo_pago=t_pago, servicio=service, foto_descripcion=foto_desc, rating=0,
        )
    except Exception as e:
        # El original tenía un `if 'solicitud' in locals(): solicitud.delete()`
        # acá, pero como la excepción ocurre durante el propio `.create()`,
        # `solicitud` nunca llega a asignarse — esa rama nunca se ejecuta,
        # se omite en vez de replicar código muerto.
        resp["message"] = "No se pudo crear al objeto Solicitud: " + str(e)
        resp["success"] = False
        return None, resp

    try:
        proveedores_id = proveedores_id.split(",")
    except Exception as e:
        solicitud.delete()
        resp["message"] = "Ha ocurrido un error al hacer split de la lista de proveedores: " + str(e)
        resp["success"] = False
        return None, resp

    titles = "Solicitud Recibida del servicio " + solicitud.servicio.nombre
    bodys = "¡Dale un vistazo!"
    notif_data = {"ruta": "/main/home", "descripcion": "Se ha recibido una solicitud de servicio."}

    from fcm_django.models import FCMDevice

    for proveedor_id in proveedores_id:
        try:
            prov = Proveedor.objects.get(id=proveedor_id)
        except Exception as e:
            solicitud.delete()
            resp["message"] = f"Error al obtener un proveedor con ID {proveedor_id}: {str(e)}"
            resp["success"] = False
            return None, resp

        try:
            envio_interesados = Envio_Interesados.objects.create(solicitud=solicitud, proveedor=prov)
        except Exception as e:
            solicitud.delete()
            resp["message"] = f"Error al crear Envio_Interesados para proveedor {proveedor_id}: {str(e)}"
            resp["success"] = False
            return None, resp

        try:
            datos_prov = Datos.objects.get(id=prov.user_datos_id)
            devices = FCMDevice.objects.filter(active=True, user_id=datos_prov.user.id)
            tokens = list(devices.values_list("registration_id", flat=True))
            send_notificationF(tokens, titles, bodys, notif_data)
        except Exception as e:
            envio_interesados.delete()
            solicitud.delete()
            resp["message"] = f"Error al enviar notificación al proveedor {proveedor_id}: {str(e)}"
            resp["success"] = False
            return None, resp

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
            "ruta": "/historial",
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
    from api.serializers import Envio_InteresadosSerializer

    envio_interesado = Envio_Interesados.objects.all().filter(solicitud=solicitud_id, interesado=True)
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
        proveedor__user_datos__user=user, interesado=False,
    ).order_by("-fecha_creacion")
    return [ei.solicitud for ei in envio_interesados]


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
    from api.serializers import Envio_InteresadosSerializer
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
    send_notificationF(tokens, titles, bodys, {"ruta": "/historial", "descripcion": descripcion})
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
            rating_proveedor = solicitudes_proveedor.aggregate(Sum("rating"))["rating__sum"] / len(solicitudes_proveedor)
            adjudicada = Envio_Interesados.objects.get(solicitud=solicitud, proveedor=solicitud.proveedor)
            proveedor.rating = rating_proveedor
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

            if request_data.get("termino") != "pagado":
                titles = "Servicio finalizado: " + solicitud.servicio.nombre
                bodys = "¡Dale un vistazo!"
                devices = FCMDevice.objects.filter(active=True, user__username=solicitud.proveedor.user_datos.user.email)
                tokens = list(devices.values_list("registration_id", flat=True))
                notif_data = {
                    "ruta": "/historial",
                    "descripcion": "Puede observar la solicitud " + solicitud.servicio.nombre
                    + " finalizada en la seccion de Historial > PASADAS",
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
