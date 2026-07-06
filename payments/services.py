import datetime

from django.contrib.auth.models import User
from django.db.models import Q, Sum

from api.models import (
    Banco, Cuenta, Cupon, Cupon_Aplicado, Datos, PagoEfectivo, PagoSolicitud, PagoTarjeta,
    Plan, PlanProveedor, Proveedor, Solicitante, Solicitud, Tarjeta,
)
from api.serializers import PagoTarjetaSerializer, PlanProveedorSerializer, PlanSerializer, TarjetaSerializer


def list_bancos():
    """Replica de Bancos.get (api/views.py:6335-6347)."""
    return Banco.objects.all()


def listar_cuentas_por_proveedor(proveedor_id):
    """Replica de CuentaProveedor.get (api/views.py:2605-2611), Fase 4. Sin
    evidencia de llamador real en ningún frontend (grep sobre los 4 apps) —
    se migra igual por consistencia de namespace."""
    return Cuenta.objects.all().filter(proveedor=proveedor_id)


def list_planes():
    """Réplica de Planes.get (api/views.py:4315-4320), Fase 5."""
    return Plan.objects.all().filter()


def crear_plan(data):
    """Réplica de Planes.post (api/views.py:4322-4329), Fase 5."""
    serializer = PlanSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    plan = serializer.save()
    return PlanSerializer(plan).data, True


def actualizar_plan(data):
    """Réplica de Planes.put (api/views.py:4331-4338), Fase 5. El id viene
    del body (`request.data.get('id')`), no de la URL, tal cual el original."""
    plan = Plan.objects.get(id=data.get("id"))
    serializer = PlanSerializer(plan, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_plan(id):
    """Réplica de Planes.delete (api/views.py:4340-4344), Fase 5."""
    plan = Plan.objects.get(id=id)
    data = PlanSerializer(plan).data
    plan.delete()
    return data


def list_planes_activos():
    """Réplica de PlanesEstado.get (api/views.py:4513-4518), Fase 5."""
    return Plan.objects.all().filter(estado=True)


def list_planes_proveedor():
    """Réplica de PlanProveedorView.get (api/views.py:4480-4485), Fase 5."""
    return PlanProveedor.objects.all().filter()


def crear_plan_proveedor(data):
    """Réplica de PlanProveedorView.post (api/views.py:4487-4494), Fase 5."""
    serializer = PlanProveedorSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    plan_proveedor = serializer.save()
    return PlanProveedorSerializer(plan_proveedor).data, True


def actualizar_plan_proveedor(data):
    """Réplica de PlanProveedorView.put (api/views.py:4496-4504), Fase 5.
    El id viene del body, no de la URL, tal cual el original."""
    plan_proveedor = PlanProveedor.objects.get(id=data.get("id"))
    serializer = PlanProveedorSerializer(plan_proveedor, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_plan_proveedor(id):
    """Réplica de PlanProveedorView.delete (api/views.py:4506-4510), Fase 5."""
    plan_proveedor = PlanProveedor.objects.get(id=id)
    data = PlanProveedorSerializer(plan_proveedor).data
    plan_proveedor.delete()
    return data


def registrar_pago_efectivo(data):
    """Replica exacta de PagosEfectivo.post (api/views.py:5029-5100).
    Devuelve (pago_efectivo_o_None, data: dict).

    `send_notificationF` se importa localmente para evitar el ciclo con
    `api.views` (mismo patrón que `accounts.services.crear_proveedor_pendiente`)."""
    from api.views import send_notificationF

    resp = {"success": False}
    user = data.get("username")
    id_cupon = data.get("id_cupon")
    amount = data.get("valor")
    descuento = data.get("descuento")
    desc = data.get("descripcion")
    referencia = data.get("referencia")
    solicitud_id = data.get("solicitud")
    us = data.get("usuario")
    serv = data.get("servicio")
    prov = data.get("proveedor")
    prov_phone = data.get("prov_phone")
    prov_email = data.get("prov_email")
    us_phone = data.get("user_phone")

    try:
        usuario = User.objects.get(username=user)
        cupon = Cupon.objects.get(pk=id_cupon) if id_cupon else None
        solicitud = Solicitud.objects.get(id=solicitud_id)
    except Exception:
        resp["error"] = "No se encontraron los datos de la promocion"
        return None, resp

    try:
        pago_efectivo = PagoEfectivo.objects.create(
            user=usuario, promocion=None, cupon=cupon, valor=amount, descripcion=desc,
            referencia=referencia, oferta=descuento, solicitud=solicitud, usuario=us,
            servicio=serv, proveedor=prov, prov_correo=prov_email, prov_telefono=prov_phone,
            user_telefono=us_phone,
        )
        if cupon:
            try:
                cupon_aplicado = Cupon_Aplicado.objects.get(cupon=cupon, user=usuario)
                cupon_aplicado.estado = False
                cupon_aplicado.save()
            except Exception:
                pass
        resp["oferta"] = descuento
        PagoSolicitud.objects.create(pago_efectivo=pago_efectivo, solicitud=solicitud)
    except Exception:
        resp["error"] = "No se pudo guardar el pago/sin embargo, si se realizo"
        resp["oferta"] = descuento
        return None, resp

    solicitud.descuento = descuento
    solicitud.save()
    resp["success"] = True
    resp["msg"] = "El pago se guardo exitosamente"

    from fcm_django.models import FCMDevice

    titles = "Servicio pagado: " + solicitud.servicio.nombre
    bodys = "¡Dale un vistazo!"
    devices = FCMDevice.objects.filter(active=True, user__id=solicitud.proveedor.user_datos.user.id)
    tokens = list(devices.values_list("registration_id", flat=True))
    data_not = {
        "ruta": "/historial",
        "descripcion": "El pago por el servicio de " + solicitud.servicio.nombre + " fue existoso",
    }
    send_notificationF(tokens, titles, bodys, data_not)

    return pago_efectivo, resp


def list_pagos_efectivo():
    """Réplica de PagosEfectivoUser.get (api/views.py), Fase 5 Bloque 3."""
    return PagoEfectivo.objects.all().filter()


def list_pagos_tarjeta():
    """Réplica del GET de PagosTarjetaUser (api/views.py), Fase 5 Bloque 3."""
    return PagoTarjeta.objects.all().filter()


def actualizar_pago_tarjeta(id, estado):
    """Réplica del PUT de PagosTarjetaUser (api/views.py). El `id` viene por
    query param, tal cual el original — llamado en producción vía el alias
    de URL `tarjeta_pago/?id=...` (el alias `pago_tarjetas/` en cambio solo
    se usa para el GET; ambos apuntan a la misma vista)."""
    pago = PagoTarjeta.objects.get(id=id)
    pago.pago_proveedor = estado
    pago.save()


def filtrar_pagos_efectivo_por_fecha(fecha_inicio, fecha_fin):
    """Réplica de EfectivosFilter.get (api/views.py), Fase 5 Bloque 3."""
    return PagoEfectivo.objects.all().filter(fecha_creacion__date__range=[fecha_inicio, fecha_fin])


def filtrar_pagos_tarjeta_por_fecha(fecha_inicio, fecha_fin):
    """Réplica de TarjetasFilter.get (api/views.py), Fase 5 Bloque 3."""
    return PagoTarjeta.objects.all().filter(fecha_creacion__date__range=[fecha_inicio, fecha_fin])


def valor_total_efectivo():
    """Réplica de ValorTotalEfectivo.get (api/views.py), Fase 5 Bloque 3."""
    return PagoEfectivo.objects.aggregate(Sum('valor'))


def valor_total_tarjeta():
    """Réplica de ValorTotalTarjeta.get (api/views.py), Fase 5 Bloque 3."""
    return PagoTarjeta.objects.aggregate(Sum('valor'))


def valor_total_pay_tarjeta():
    """Réplica de ValorTotalPayTarjeta.get (api/views.py), Fase 5 Bloque 3."""
    return PagoTarjeta.objects.aggregate(Sum('cargo_paymentez'))


def valor_total_banc_tarjeta():
    """Réplica de ValorTotalBancTarjeta.get (api/views.py), Fase 5 Bloque 3."""
    return PagoTarjeta.objects.aggregate(Sum('cargo_banco'))


def valor_total_sis_tarjeta():
    """Réplica de ValorTotalSisTarjeta.get (api/views.py), Fase 5 Bloque 3."""
    return PagoTarjeta.objects.aggregate(Sum('cargo_sistema'))


def valor_total():
    """Réplica de ValorTotal.get (api/views.py), Fase 5 Bloque 3."""
    total_efectivo = PagoEfectivo.objects.aggregate(total=Sum('valor'))['total'] or 0
    total_tarjeta = PagoTarjeta.objects.aggregate(total=Sum('valor'))['total'] or 0
    return {'total': total_efectivo + total_tarjeta}


def valor_total_proveedores():
    """Réplica exacta de ValorTotalProveedores.get (api/views.py), Fase 5
    Bloque 3. Nombre engañoso preservado tal cual: `totalProveedores` en
    realidad cuenta pagos en efectivo (`PagoEfectivo`), no proveedores — no
    se corrige el nombre del campo de respuesta para no romper el frontend,
    que ya lo consume así."""
    return {
        "totalPendientes": Proveedor.objects.count(),
        "totalProveedores": PagoEfectivo.objects.count(),
    }


def list_pagos_solicitud_efectivo(pago_id):
    """Réplica de PagosSolicitudesEfectivo.get (api/views.py), Fase 5 Bloque 3."""
    return PagoSolicitud.objects.all().filter(pago_efectivo=pago_id)


def list_pagos_solicitud_tarjeta(pago_id):
    """Réplica de PagosSolicitudesTarjeta.get (api/views.py), Fase 5 Bloque 3."""
    return PagoSolicitud.objects.all().filter(pago_tarjeta=pago_id)


def list_tarjetas_todas():
    """Réplica exacta de Tarjetas.get (api/views.py:1694-1700). Sin evidencia
    de llamador real en ningún frontend (grep fresco) — devuelve TODAS las
    tarjetas sin filtrar por usuario, preexistente, se migra igual por
    consistencia de namespace, no se corrige (requeriría decidir qué filtro
    faltaba, decisión de producto)."""
    return Tarjeta.objects.all()


def crear_tarjeta(data):
    """Réplica exacta de Tarjetas.post (api/views.py:1702-1734)."""
    try:
        solicitante = Solicitante.objects.get(user_datos__user__username=data.get('user'))
    except Exception:
        return {'success': False, 'solicitante': data.get('user'), 'error': 'No se encontró el solicitante'}
    try:
        tarjeta = Tarjeta.objects.create(
            token=data.get('token_card'), code=data.get('status'), fecha_vencimiento=data.get('fecha_vencimiento'),
            cvv=data.get('cvv'), numero=data.get('numero'), titular=data.get('titular'),
            solicitante=solicitante, brand=data.get('brand'), tipo=data.get('type'),
        )
        return {'success': True, 'msg': 'La tarjeta se ha guardado exitosamente', 'tarjeta': TarjetaSerializer(tarjeta).data}
    except Exception:
        return {'success': False, 'error': 'No se pudo guardar la tarjeta'}


def list_tarjetas_por_usuario(identifier):
    """Réplica exacta de TarjetaUser.get (api/views.py:1667-1672). Endpoint
    multi-rol confirmado por grep fresco: Solicitante2022 y Provedor2022
    (lectura) lo llaman igual."""
    return Tarjeta.objects.all().filter(solicitante__user_datos__user__username=identifier)


def eliminar_tarjeta(identifier):
    """Réplica exacta de TarjetaUser.delete (api/views.py:1674-1691). Sin
    evidencia de llamador real en Provedor2022 (grep fresco confirma solo
    Solicitante2022 lo usa)."""
    try:
        tarjeta = Tarjeta.objects.get(id=identifier)
    except Exception:
        return {'success': False, 'error': 'No se encontro la tarjeta'}
    try:
        tarjeta.delete()
        return {'success': True, 'msg': 'Se elimino exitosamente'}
    except Exception:
        return {'success': False, 'error': 'No se pudo borrar la tarjeta'}


def registrar_pago_tarjeta(data):
    """Réplica exacta de PagosTarjeta.post (api/views.py:1777-1855). Endpoint
    real de pago con tarjeta de Solicitante2022, distinto de la familia
    admin `PagosTarjetaUser`/`pago_tarjetas`/`tarjeta_pago` (Fase 5 Bloque 3)
    — confirmado por comentario preexistente en api/views.py y por grep
    fresco (cleanup post-Fase-5, Bloque 3). Devuelve (pago_tarjeta_o_None, data)."""
    from api.views import send_notificationF

    resp = {"success": False}
    try:
        resp["detail"] = "User"
        usuario = User.objects.get(username=data.get("username"))
        resp["detail"] = "Tarjeta"
        tarjeta = Tarjeta.objects.get(id=data.get("tarjeta"))
        resp["detail"] = "Promocion"
        cupon = Cupon.objects.get(pk=data.get("id_cupon")) if data.get("id_cupon") else None
        resp["detail"] = "Solicitud"
        solicitud = Solicitud.objects.get(id=data.get("solicitud"))
    except Exception as e:
        resp["error"] = str(e)
        return None, resp

    try:
        resp["detail"] = "pago_tarjeta"
        pago_tarjeta = PagoTarjeta.objects.create(
            user=usuario, tarjeta=tarjeta, carrier_id=data.get("carrier"), carrier_code=data.get("carrier_code"),
            promocion=None, cupon=cupon, valor=data.get("valor"), descripcion=data.get("descripcion"),
            impuesto=data.get("impuesto"), solicitud=solicitud, referencia=data.get("referencia"),
            cargo_paymentez=data.get("cargo_paymentez"), cargo_banco=data.get("cargo_banco"),
            cargo_sistema=data.get("cargo_sistema"), usuario=data.get("usuario"), servicio=data.get("servicio"),
            proveedor=data.get("proveedor"), prov_correo=data.get("prov_email"), prov_telefono=data.get("prov_phone"),
        )
        if cupon:
            try:
                cupon_aplicado = Cupon_Aplicado.objects.get(cupon=cupon, user=usuario)
                cupon_aplicado.estado = False
                cupon_aplicado.save()
            except Exception:
                pass
        resp["detail"] = "pago_solicitud"
        PagoSolicitud.objects.create(pago_tarjeta=pago_tarjeta, solicitud=solicitud)
    except Exception:
        resp["error"] = "No se pudo guardar el pago/sin embargo, si se realizo"
        return None, resp

    solicitud.descuento = data.get("descuento")
    solicitud.save()
    resp["success"] = True
    resp["msg"] = "El pago se guardo exitosamente"

    from fcm_django.models import FCMDevice

    titles = "Servicio pagado: " + solicitud.servicio.nombre
    bodys = "¡Dale un vistazo!"
    devices = FCMDevice.objects.filter(active=True, user__username=solicitud.proveedor.user_datos.user.email)
    tokens = list(devices.values_list("registration_id", flat=True))
    data_not = {"ruta": "/historial", "descripcion": "El pago por el servicio de " + solicitud.servicio.nombre + " fue existoso"}
    send_notificationF(tokens, titles, bodys, data_not)

    return pago_tarjeta, resp


def enviar_email_factura(data):
    """Réplica exacta de EmailFactura.post (api/views.py:525-563). Confirmado
    exclusivo de Solicitante2022 (cleanup post-Fase-5, Bloque 3). Se importa
    `FormatEmail`/`threading`/`uuid` localmente para evitar el ciclo con
    `api.views` (mismo patrón que `registrar_pago_efectivo`)."""
    import threading
    import uuid

    from api.views import FormatEmail

    resp = {}
    email_user = data.get('email')
    format_email = FormatEmail()
    try:
        user = Datos.objects.get(user__username=email_user)
    except Datos.DoesNotExist:
        resp['success'] = False
        return resp

    user.security_access = uuid.uuid4()
    user.save()
    try:
        asunto = 'Recibo Pago de Servicios Vive Fácil'
        thread = threading.Thread(target=format_email.send_email([email_user], asunto, 'emails/factura.html', {
            "fecha_today": data.get('fecha_emision'), "fecha_emision": data.get('fecha_emision'),
            "solicitante_name": user.nombres + ' ' + user.apellidos, "solicitud_descripcion": data.get('solicitud'),
            "transaccion_id": data.get('transaccion'), "proveedor_name": data.get('proveedor'),
            "pago_descripcion": data.get('pago_descripcion'), "metodo_pago": data.get('metodo'),
            "oferta": data.get('oferta'), "descuento": data.get('descuento'), "valor_total": data.get('valor'),
        }))
        thread.start()
        resp['success'] = True
        resp['clave'] = user.security_access
    except Exception as e:
        resp['error'] = str(e)
    return resp


def proveedores_por_fecha_plan(fecha_inicio, fecha_fin):
    """Réplica exacta de PlanProveedores_Filter_Date.get (api/views.py:1100-1115).
    Sin evidencia de llamador real en ningún frontend (grep fresco) — se
    migra igual por consistencia de namespace (cleanup post-Fase-5, Bloque 3)."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Proveedor.objects.all().filter(planproveedor__fecha_expiracion__date__range=[fecha_in, fecha_fi])


def proveedores_por_fecha_y_nombre(fecha_inicio, fecha_fin, user):
    """Réplica exacta de ProveedoresDate_Search_Name.get (api/views.py:1949-1966).
    Sin evidencia de llamador real en ningún frontend — se migra igual por
    consistencia de namespace (cleanup post-Fase-5, Bloque 3)."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Proveedor.objects.all().filter(
        Q(user_datos__nombres__icontains=user, planproveedor__fecha_expiracion__date__range=[fecha_in, fecha_fi])
        | Q(user_datos__apellidos__icontains=user, planproveedor__fecha_expiracion__date__range=[fecha_in, fecha_fi])
    )
