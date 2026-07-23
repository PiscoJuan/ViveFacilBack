import datetime

from django.contrib.auth.models import User
from django.db.models import Q, Sum

from accounts.models import Datos, Proveedor, Solicitante
from solicitudes.models import Solicitud
from payments.models import Banco, Cuenta, PagoEfectivo, PagoSolicitud, PagoTarjeta, Plan, PlanProveedor, Tarjeta
from promotions.models import Cupon, Cupon_Aplicado
from api.serializers import PagoTarjetaSerializer, PlanProveedorSerializer, PlanSerializer, TarjetaSerializer


def list_bancos():
    return Banco.objects.all()


def crear_banco(nombre, estado):
    return Banco.objects.create(nombre=nombre, estado=estado)


def eliminar_banco(id):
    """Deja que `Banco.DoesNotExist` se propague — la vista la captura para
    devolver el 404 original."""
    Banco.objects.get(pk=id).delete()


def listar_cuentas_por_proveedor(proveedor_id):
    """Sin
    evidencia de llamador real en ningún frontend (grep sobre los 4 apps) —
    se migra igual por consistencia de namespace."""
    return Cuenta.objects.all().filter(proveedor=proveedor_id)


def list_planes():
    return Plan.objects.all().filter()


def crear_plan(data):
    serializer = PlanSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    plan = serializer.save()
    return PlanSerializer(plan).data, True


def actualizar_plan(data):
    """El id viene
    del body (`request.data.get('id')`), no de la URL, tal cual el original."""
    plan = Plan.objects.get(id=data.get("id"))
    serializer = PlanSerializer(plan, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_plan(id):
    plan = Plan.objects.get(id=id)
    data = PlanSerializer(plan).data
    plan.delete()
    return data


def list_planes_activos():
    return Plan.objects.all().filter(estado=True)


def list_planes_proveedor():
    return PlanProveedor.objects.all().filter()


def crear_plan_proveedor(data):
    serializer = PlanProveedorSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    plan_proveedor = serializer.save()
    return PlanProveedorSerializer(plan_proveedor).data, True


def actualizar_plan_proveedor(data):
    """El id viene del body, no de la URL, tal cual el original."""
    plan_proveedor = PlanProveedor.objects.get(id=data.get("id"))
    serializer = PlanProveedorSerializer(plan_proveedor, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_plan_proveedor(id):
    plan_proveedor = PlanProveedor.objects.get(id=id)
    data = PlanProveedorSerializer(plan_proveedor).data
    plan_proveedor.delete()
    return data


def registrar_pago_efectivo(data):
    """Devuelve (pago_efectivo_o_None, data: dict)."""
    from core.firebase import send_notificationF

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
        "ruta": "/main/solicitudes",
        "descripcion": "El pago por el servicio de " + solicitud.servicio.nombre + " fue existoso",
    }
    send_notificationF(tokens, titles, bodys, data_not)

    return pago_efectivo, resp


def list_pagos_efectivo():
    return PagoEfectivo.objects.all().filter()


def list_pagos_tarjeta():
    return PagoTarjeta.objects.all().filter()


def actualizar_pago_tarjeta(id, estado):
    """El `id` viene por query param — llamado en producción vía el alias
    de URL `tarjeta_pago/?id=...` (el alias `pago_tarjetas/` en cambio solo
    se usa para el GET; ambos apuntan a la misma vista)."""
    pago = PagoTarjeta.objects.get(id=id)
    pago.pago_proveedor = estado
    pago.save()


def filtrar_pagos_efectivo_por_fecha(fecha_inicio, fecha_fin):
    return PagoEfectivo.objects.all().filter(fecha_creacion__date__range=[fecha_inicio, fecha_fin])


def filtrar_pagos_tarjeta_por_fecha(fecha_inicio, fecha_fin):
    return PagoTarjeta.objects.all().filter(fecha_creacion__date__range=[fecha_inicio, fecha_fin])


def valor_total_efectivo():
    return PagoEfectivo.objects.aggregate(Sum('valor'))


def valor_total_tarjeta():
    return PagoTarjeta.objects.aggregate(Sum('valor'))


def valor_total_pay_tarjeta():
    return PagoTarjeta.objects.aggregate(Sum('cargo_paymentez'))


def valor_total_banc_tarjeta():
    return PagoTarjeta.objects.aggregate(Sum('cargo_banco'))


def valor_total_sis_tarjeta():
    return PagoTarjeta.objects.aggregate(Sum('cargo_sistema'))


def valor_total():
    total_efectivo = PagoEfectivo.objects.aggregate(total=Sum('valor'))['total'] or 0
    total_tarjeta = PagoTarjeta.objects.aggregate(total=Sum('valor'))['total'] or 0
    return {'total': total_efectivo + total_tarjeta}


def valor_total_proveedores():
    """Nombre engañoso preservado tal cual: `totalProveedores` en realidad
    cuenta pagos en efectivo (`PagoEfectivo`), no proveedores — no se
    corrige el nombre del campo de respuesta para no romper el frontend,
    que ya lo consume así."""
    return {
        "totalPendientes": Proveedor.objects.count(),
        "totalProveedores": PagoEfectivo.objects.count(),
    }


def list_pagos_solicitud_efectivo(pago_id):
    return PagoSolicitud.objects.all().filter(pago_efectivo=pago_id)


def list_pagos_solicitud_tarjeta(pago_id):
    return PagoSolicitud.objects.all().filter(pago_tarjeta=pago_id)


def list_tarjetas_todas():
    """Sin llamador real confirmado — devuelve TODAS las tarjetas sin
    filtrar por usuario."""
    return Tarjeta.objects.all()


def crear_tarjeta(data):
    try:
        solicitante = Solicitante.objects.get(user_datos__user__username=data.get('user'))
    except Exception:
        return {'success': False, 'solicitante': data.get('user'), 'error': 'No se encontró el solicitante'}
    try:
        # Nunca se guardan datos sensibles de tarjeta: cvv/numero se neutralizan.
        # Las tarjetas reales viven en Paymentez; esta tabla queda por histórico.
        tarjeta = Tarjeta.objects.create(
            token=data.get('token_card'), code=data.get('status'), fecha_vencimiento=data.get('fecha_vencimiento'),
            cvv="***", numero=0, titular=data.get('titular'),
            solicitante=solicitante, brand=data.get('brand'), tipo=data.get('type'),
        )
        return {'success': True, 'msg': 'La tarjeta se ha guardado exitosamente', 'tarjeta': TarjetaSerializer(tarjeta).data}
    except Exception:
        return {'success': False, 'error': 'No se pudo guardar la tarjeta'}


def list_tarjetas_por_usuario(identifier):
    """Endpoint
    multi-rol confirmado por grep fresco: Solicitante2022 y Provedor2022
    (lectura) lo llaman igual."""
    return Tarjeta.objects.all().filter(solicitante__user_datos__user__username=identifier)


def eliminar_tarjeta(identifier):
    """Sin
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
    """Endpoint real de pago con tarjeta de Solicitante2022, distinto de
    la familia admin `PagosTarjetaAdminView`/`pago_tarjetas`/`tarjeta_pago`.
    Devuelve (pago_tarjeta_o_None, data)."""
    from core.firebase import send_notificationF

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
    data_not = {"ruta": "/main/solicitudes", "descripcion": "El pago por el servicio de " + solicitud.servicio.nombre + " fue existoso"}
    send_notificationF(tokens, titles, bodys, data_not)

    return pago_tarjeta, resp


def enviar_email_factura(data):
    """Exclusivo de Solicitante2022."""
    import threading
    import uuid

    from core.email import FormatEmail

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
        threading.Thread(
            target=format_email.send_email,
            args=([email_user], asunto, 'emails/factura.html', {
                "fecha_today": data.get('fecha_emision'), "fecha_emision": data.get('fecha_emision'),
                "solicitante_name": user.nombres + ' ' + user.apellidos, "solicitud_descripcion": data.get('solicitud'),
                "transaccion_id": data.get('transaccion'), "proveedor_name": data.get('proveedor'),
                "pago_descripcion": data.get('pago_descripcion'), "metodo_pago": data.get('metodo'),
                "oferta": data.get('oferta'), "descuento": data.get('descuento'), "valor_total": data.get('valor'),
            }),
        ).start()
        resp['success'] = True
        resp['clave'] = user.security_access
    except Exception as e:
        resp['error'] = str(e)
    return resp


def proveedores_por_fecha_plan(fecha_inicio, fecha_fin):
    """Sin llamador real confirmado en ningún frontend."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Proveedor.objects.all().filter(planproveedor__fecha_expiracion__date__range=[fecha_in, fecha_fi])


def proveedores_por_fecha_y_nombre(fecha_inicio, fecha_fin, user):
    """Sin llamador real confirmado en ningún frontend."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Proveedor.objects.all().filter(
        Q(user_datos__nombres__icontains=user, planproveedor__fecha_expiracion__date__range=[fecha_in, fecha_fi])
        | Q(user_datos__apellidos__icontains=user, planproveedor__fecha_expiracion__date__range=[fecha_in, fecha_fi])
    )
