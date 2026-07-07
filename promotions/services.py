import datetime

from api.models import Categoria, Cupon, Cupon_Aplicado, CuponCategoria, Datos, Promocion, PromocionCategoria
from api.serializers import CuponSerializer, PromocionSerializer


def cupones_aplicados_activos(user):
    return Cupon_Aplicado.objects.all().filter(user=user, estado=True)


def cupones_categoria_disponibles(usuario):
    hoy = datetime.datetime.today()
    cupones = CuponCategoria.objects.all().filter(cupon__fecha_expiracion__gte=hoy)
    cupones = cupones.filter(cupon__fecha_iniciacion__lte=hoy)
    ids_aplicados = list(
        Cupon_Aplicado.objects.all()
        .filter(user=usuario, estado=False)
        .distinct()
        .values_list("cupon", flat=True)
    )
    return cupones.exclude(cupon__pk__in=ids_aplicados)


def revisar_descuento_unico(user):
    """Devuelve uno de: "descuento" | "no" | "error"."""
    try:
        usuario = Datos.objects.get(user=user)
        return "descuento" if usuario.descuento == 1 else "no"
    except Exception:
        return "error"


def usar_descuento_unico(mail):
    """Devuelve uno de: "usado" | "error"."""
    try:
        usuario = Datos.objects.get(user__email=mail)
        if usuario.descuento == 1:
            usuario.descuento = 2
            usuario.save()
            return "usado"
        return "error"
    except Exception:
        return "error"


def _notificar_solicitantes(titulo, cuerpo, data_extra):
    from fcm_django.models import FCMDevice
    from api.views import send_notificationF

    devices = FCMDevice.objects.filter(active=True, user__groups__name="Solicitante")
    tokens = list(devices.values_list("registration_id", flat=True))
    if tokens:
        send_notificationF(tokens, titulo, cuerpo, data_extra)


def list_promociones():
    """El
    `order_by('-pk')` es el comportamiento real (el filtro por fecha
    comentado en el original nunca se aplicó)."""
    return Promocion.objects.all().order_by("-pk")


def crear_promocion(data, categorias_nombres):
    """Devuelve (promocion_o_None, data: dict)."""
    resp = {"success": False}
    try:
        promocion = Promocion.objects.create(
            titulo=data.get("titulo"), descripcion=data.get("descripcion"),
            fecha_expiracion=data.get("fecha_expiracion"), porcentaje=data.get("porcentaje"),
            codigo=data.get("codigo"), fecha_iniciacion=data.get("fecha_iniciacion"),
            participantes=data.get("participantes"), foto=data.get("foto"),
            tipo_categoria=data.get("tipo_categoria"), cantidad=data.get("cantidad"),
        )
    except Exception:
        resp["error"] = "No se pudo crear la promoción"
        return None, resp

    try:
        for nombre in categorias_nombres:
            categoria = Categoria.objects.all().filter(nombre=nombre)
            PromocionCategoria.objects.create(categoria=categoria[0], promocion=promocion)
    except Exception:
        promocion.delete()
        resp["error"] = "No se pudo asignar las categorias"
        return None, resp

    _notificar_solicitantes(
        "Nueva Promoción " + promocion.titulo, promocion.descripcion,
        {"ruta": "Home", "descripcion": "Se ha creado una nueva promoción"},
    )
    resp["success"] = True
    resp["msg"] = "La promoción se ha creado exitosamente"
    resp["promocion"] = PromocionSerializer(promocion).data
    return promocion, resp


def actualizar_promocion(data, categorias_nombres):
    """Busca
    por `codigo` (viene del body), no por el `id` de la URL — tal cual el
    original (el `id` de la URL nunca se usa)."""
    resp = {"success": False}
    codigo = data.get("codigo")
    try:
        promocion = Promocion.objects.get(codigo=codigo)
    except Promocion.DoesNotExist:
        resp["error"] = "No se encontró la promoción"
        return resp

    promocion.titulo = data.get("titulo")
    promocion.descripcion = data.get("descripcion")
    promocion.participantes = data.get("participantes")
    promocion.porcentaje = data.get("porcentaje")
    promocion.cantidad = data.get("cantidad")
    promocion.fecha_iniciacion = data.get("fecha_iniciacion")
    promocion.fecha_expiracion = data.get("fecha_expiracion")
    if data.get("foto") is not None:
        promocion.foto = data.get("foto")
    promocion.save()

    try:
        catnom = list(
            PromocionCategoria.objects.all()
            .filter(promocion__codigo=codigo)
            .values_list("categoria__nombre", flat=True)
        )
        for cat in categorias_nombres:
            if cat not in catnom:
                categ = Categoria.objects.get(nombre=cat)
                PromocionCategoria.objects.create(promocion=promocion, categoria=categ)
        for promctg in PromocionCategoria.objects.all().filter(promocion__codigo=codigo):
            if promctg.categoria.nombre not in categorias_nombres:
                PromocionCategoria.objects.filter(categoria=promctg.categoria).delete()
    except Exception:
        resp["error"] = "No se pudo actualizar las categorias"
        return resp

    resp["success"] = True
    resp["msg"] = "La promoción se ha actualizado exitosamente"
    resp["promocion"] = PromocionSerializer(promocion).data
    return resp


def eliminar_promocion(id):
    Promocion.objects.get(id=id).delete()


def obtener_promocion(pk):
    return Promocion.objects.get(id=pk)


def actualizar_estado_promocion(id, estado):
    promocion = Promocion.objects.get(id=id)
    promocion.estado = estado
    promocion.save()


def list_cupones():
    return Cupon.objects.all().order_by("-pk")


def crear_cupon(data, categorias_nombres):
    resp = {"success": False}
    try:
        cupon = Cupon.objects.create(
            titulo=data.get("titulo"), descripcion=data.get("descripcion"),
            fecha_expiracion=data.get("fecha_expiracion"), porcentaje=data.get("porcentaje"),
            participantes=data.get("participantes"), codigo=data.get("codigo"),
            fecha_iniciacion=data.get("fecha_iniciacion"), puntos=data.get("puntos"),
            foto=data.get("foto"), tipo_categoria=data.get("tipo_categoria"), cantidad=data.get("cantidad"),
        )
    except Exception:
        resp["error"] = "No se pudo crear el cupon"
        return None, resp

    try:
        for nombre in categorias_nombres:
            categoria = Categoria.objects.all().filter(nombre=nombre)
            CuponCategoria.objects.create(categoria=categoria[0], cupon=cupon)
    except Exception:
        cupon.delete()
        resp["error"] = "No se pudo asignar las categorias"
        return None, resp

    _notificar_solicitantes(
        "Nuevo Cupón de descuento " + cupon.titulo, cupon.descripcion,
        {"ruta": "/promociones", "descripcion": "Se encuentra disponible un nuevo cupón!"},
    )
    resp["success"] = True
    resp["msg"] = "El cupon se ha creado exitosamente"
    resp["cupon"] = CuponSerializer(cupon).data
    return cupon, resp


def actualizar_cupon(data, categorias_nombres):
    """Busca por
    `codigo` (body), no por el `id` de la URL, tal cual el original.
    `tipo_categoria` acá es singular (a diferencia de Promociones, que
    sincroniza una lista completa) — réplica exacta de la asimetría real
    entre ambas clases en el original."""
    resp = {"success": False}
    codigo = data.get("codigo")
    type_category = data.get("tipo_categoria")
    try:
        cupon = Cupon.objects.get(codigo=codigo)
    except Cupon.DoesNotExist:
        resp["error"] = "No se encontró el cupon"
        return resp

    cupon.titulo = data.get("titulo")
    cupon.descripcion = data.get("descripcion")
    cupon.puntos = data.get("puntos")
    cupon.porcentaje = data.get("porcentaje")
    cupon.cantidad = data.get("cantidad")
    cupon.fecha_iniciacion = data.get("fecha_iniciacion")
    cupon.fecha_expiracion = data.get("fecha_expiracion")
    cupon.participantes = data.get("participantes")
    cupon.tipo_categoria = type_category
    if data.get("foto") is not None:
        cupon.foto = data.get("foto")
    cupon.save()

    try:
        catnom = list(
            CuponCategoria.objects.all().filter(cupon__codigo=codigo).values_list("categoria__nombre", flat=True)
        )
        if type_category not in catnom:
            categ = Categoria.objects.get(nombre=type_category)
            CuponCategoria.objects.create(cupon=cupon, categoria=categ)
        for cupon_categoria in CuponCategoria.objects.all().filter(cupon__codigo=codigo):
            if cupon_categoria.categoria.nombre != type_category:
                cupon_categoria.delete()
    except Exception:
        resp["error"] = "No se pudo actualizar las categorias"
        return resp

    resp["success"] = True
    resp["msg"] = "El cupón se ha actualizado exitosamente"
    resp["cupon"] = CuponSerializer(cupon).data
    return resp


def eliminar_cupon(id):
    Cupon.objects.get(id=id).delete()


def obtener_cupon(pk):
    return Cupon.objects.get(id=pk)


def actualizar_estado_cupon(id, estado):
    cupon = Cupon.objects.get(id=id)
    cupon.estado = estado
    cupon.save()


def crear_cupon_aplicado(user, cupon_id, estado):
    """Devuelve el dict de respuesta tal cual el
    original (incluye 'creado'/'valid'/'error' según el camino)."""
    data = {}
    try:
        cupon_apl = Cupon_Aplicado.objects.filter(user=user, cupon__id=cupon_id)
        if not cupon_apl:
            cupon = Cupon.objects.get(id=cupon_id)
            data['cr'] = True
            usuario = Datos.objects.get(user__email=user)
            usuario.puntos = usuario.puntos - cupon.puntos
            cupon.cantidad = cupon.cantidad - 1
            if usuario.puntos < 0:
                data['valid'] = "puntos"
                data['creado'] = False
            elif cupon.cantidad + 1 <= 0:
                data['valid'] = "cantidad"
                data['creado'] = False
            else:
                usuario.save()
                cupon.save()
                Cupon_Aplicado.objects.get_or_create(cupon=Cupon.objects.get(id=cupon_id), user=user, estado=estado)
                data['creado'] = True
        else:
            data['creado'] = False
        data['success'] = True
    except Exception:
        data['error'] = "No se pudo adjudicar el cupon"
        data['success'] = False
        data['user'] = user
        data['cupon'] = cupon_id
    return data


def actualizar_cupon_aplicado(user, cupon_id, estado):
    """Sin evidencia de consumidor real en ningún
    frontend (solo el POST se llama en la práctica). **Bug real corregido
    al mover el código**: el original hacía `cupon_aplic.estado = ...` y
    `cupon_aplic.save()` sobre un QuerySet (resultado de `.filter(...)`),
    no sobre una instancia — `QuerySet` no tiene `.save()`, así que
    cualquier llamada real habría lanzado `AttributeError` garantizado. Se
    corrige con `.update(...)`, que es lo que la lógica claramente
    intentaba hacer. Devuelve True si se actualizó, False si no había un
    Cupon_Aplicado que coincidiera (la vista lo traduce a 400)."""
    cupon_aplicado = Cupon_Aplicado.objects.filter(user=user, cupon=Cupon.objects.get(id=cupon_id))
    if cupon_aplicado:
        cupon_aplicado.update(estado=estado)
        return True
    return False


def obtener_cupon(pk):
    """Confirmado real: Solicitante2022 y Admin2022."""
    return Cupon.objects.get(id=pk)


def actualizar_cantidad_cupon(pk, cantidad):
    """Sin consumidor real confirmado en ningún frontend."""
    cupon = Cupon.objects.get(id=pk)
    cupon.cantidad = cantidad
    cupon.save()


def promociones_por_categoria(promocion_codigo):
    """Sin consumidor real confirmado en ningún frontend."""
    return PromocionCategoria.objects.all().filter(promocion__codigo=promocion_codigo)


def all_promociones_categoria():
    """Sin consumidor real confirmado en ningún frontend."""
    return PromocionCategoria.objects.all()


def cupones_por_categoria(cupon_codigo):
    """Sin consumidor real confirmado en ningún frontend."""
    return CuponCategoria.objects.all().filter(cupon__codigo=cupon_codigo)


def confirmar_descuento(mail):
    """Devuelve uno de: "descuento" | "reclamado" | "usado" | "no_existe"."""
    try:
        usuario = Datos.objects.get(user__email=mail)
        if usuario.descuento == 0:
            usuario.descuento = 1
            usuario.save()
            return "descuento"
        elif usuario.descuento == 1:
            return "reclamado"
        else:
            return "usado"
    except Exception:
        return "no_existe"
