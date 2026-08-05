import datetime

from accounts.models import Datos
from catalog.models import Categoria
from promotions.models import Cupon, Cupon_Aplicado, CuponCategoria
from api.serializers import CuponSerializer


def cupones_aplicados_activos(user):
    # order_by explícito: sin esto PageNumberPagination pagina sobre un
    # queryset sin orden garantizado y una página puede repetir o saltarse
    # cupones respecto a la anterior.
    return Cupon_Aplicado.objects.all().filter(user=user, estado=True).order_by('-id')


def cupones_categoria_disponibles(usuario):
    hoy = datetime.datetime.today()
    cupones = CuponCategoria.objects.all().filter(cupon__fecha_expiracion__gte=hoy)
    cupones = cupones.filter(cupon__fecha_iniciacion__lte=hoy)
    # Sin filtrar por estado: crear_cupon_aplicado no deja canjear un cupón
    # dos veces sin importar si el canje anterior ya se usó (estado=False) o
    # sigue disponible en "Mis cupones" (estado=True), así que acá también
    # se excluye por igual.
    ids_aplicados = list(
        Cupon_Aplicado.objects.all()
        .filter(user=usuario)
        .distinct()
        .values_list("cupon", flat=True)
    )
    # Mismo motivo que en cupones_aplicados_activos: orden explícito para que
    # la paginación no repita/salte cupones entre páginas.
    return cupones.exclude(cupon__pk__in=ids_aplicados).order_by('-id')


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
    from core.firebase import send_notificationF

    devices = FCMDevice.objects.filter(active=True, user__groups__name="Solicitante")
    tokens = list(devices.values_list("registration_id", flat=True))
    if tokens:
        send_notificationF(tokens, titulo, cuerpo, data_extra)


def _a_fecha_aware(valor):
    """Normaliza una fecha que llega del formulario a un datetime con zona.

    Los `<input type="datetime-local">` del admin mandan '2023-10-26T00:00', sin
    zona horaria. Si se asigna ese string al modelo y se guarda, la instancia en
    memoria SIGUE teniendo el string (Django no la refresca), y cualquier cosa
    que después compare esa fecha revienta con
    "'<' not supported between 'datetime.datetime' and 'str'". Además Django
    avisa por cada guardado (RuntimeWarning: naive datetime).

    Si no se puede interpretar se devuelve el valor tal cual, para no cambiar el
    comportamiento previo en formatos que no contemplamos.
    """
    from django.utils import timezone
    from django.utils.dateparse import parse_date, parse_datetime

    if not valor or not isinstance(valor, str):
        return valor

    fecha = parse_datetime(valor)
    if fecha is None:
        solo_dia = parse_date(valor)
        if solo_dia is None:
            return valor
        fecha = datetime.datetime.combine(solo_dia, datetime.time.min)

    return timezone.make_aware(fecha) if timezone.is_naive(fecha) else fecha


def _comparable(valor):
    """Devuelve un datetime con zona que se pueda comparar con `timezone.now()`,
    o None si el valor no sirve.

    `vigencia_cupon` lo usa para no reventar nunca: se lo llama desde
    `CuponSerializer`, y una función que solo decide una etiqueta no puede
    tumbar un request. Si llega un string sin normalizar, se intenta convertir;
    si no se puede, se ignora ese criterio en vez de fallar.
    """
    from django.utils import timezone

    fecha = _a_fecha_aware(valor)
    if not isinstance(fecha, datetime.datetime):
        return None
    return timezone.make_aware(fecha) if timezone.is_naive(fecha) else fecha


def list_cupones():
    return Cupon.objects.all().order_by("-pk")


def crear_cupon(data, categorias_nombres):
    resp = {"success": False}
    try:
        cupon = Cupon.objects.create(
            titulo=data.get("titulo"), descripcion=data.get("descripcion"),
            fecha_expiracion=_a_fecha_aware(data.get("fecha_expiracion")), porcentaje=data.get("porcentaje"),
            participantes=data.get("participantes"), codigo=data.get("codigo"),
            fecha_iniciacion=_a_fecha_aware(data.get("fecha_iniciacion")), puntos=data.get("puntos"),
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
    # Los datos vienen de un FormData: todos los campos son strings, y Django
    # no reconvierte la instancia en memoria al guardar. Sin este refresco, el
    # serializer trabaja con "5" en vez de 5 y con la fecha como texto.
    cupon.refresh_from_db()
    resp["success"] = True
    resp["msg"] = "El cupon se ha creado exitosamente"
    resp["cupon"] = CuponSerializer(cupon).data
    return cupon, resp


def actualizar_cupon(data, categorias_nombres, cupon_id=None):
    """Busca por el `id` de la URL cuando viene, y solo cae al `codigo` del
    body por compatibilidad con llamadas viejas. Antes buscaba únicamente por
    `codigo`, lo que hacía imposible editar el código de un cupón: al cambiarlo
    ya no encontraba nada que actualizar.

    `tipo_categoria` acá es singular: se guarda una sola categoría por cupón.
    """
    resp = {"success": False}
    codigo = data.get("codigo")
    type_category = data.get("tipo_categoria")
    try:
        cupon = Cupon.objects.get(id=cupon_id) if cupon_id else Cupon.objects.get(codigo=codigo)
    except (Cupon.DoesNotExist, ValueError):
        resp["error"] = "No se encontró el cupon"
        return resp

    if codigo:
        cupon.codigo = codigo
    cupon.titulo = data.get("titulo")
    cupon.descripcion = data.get("descripcion")
    cupon.puntos = data.get("puntos")
    cupon.porcentaje = data.get("porcentaje")
    cupon.cantidad = data.get("cantidad")
    cupon.fecha_iniciacion = _a_fecha_aware(data.get("fecha_iniciacion"))
    cupon.fecha_expiracion = _a_fecha_aware(data.get("fecha_expiracion"))
    cupon.participantes = data.get("participantes")
    cupon.tipo_categoria = type_category
    if data.get("foto") is not None:
        cupon.foto = data.get("foto")
    cupon.save()

    try:
        # Se filtra por el cupón y no por su código: el código pudo acabar de
        # cambiar en el save() de arriba.
        catnom = list(
            CuponCategoria.objects.all().filter(cupon=cupon).values_list("categoria__nombre", flat=True)
        )
        if type_category not in catnom:
            categ = Categoria.objects.get(nombre=type_category)
            CuponCategoria.objects.create(cupon=cupon, categoria=categ)
        for cupon_categoria in CuponCategoria.objects.all().filter(cupon=cupon):
            if cupon_categoria.categoria.nombre != type_category:
                cupon_categoria.delete()
    except Exception:
        resp["error"] = "No se pudo actualizar las categorias"
        return resp

    # Los datos vienen de un FormData: todos los campos son strings, y Django
    # no reconvierte la instancia en memoria al guardar. Sin este refresco, el
    # serializer trabaja con "5" en vez de 5 y con la fecha como texto.
    cupon.refresh_from_db()
    resp["success"] = True
    resp["msg"] = "El cupón se ha actualizado exitosamente"
    resp["cupon"] = CuponSerializer(cupon).data
    return resp


def eliminar_cupon(id):
    """Borrado definitivo, bloqueado si el cupón ya tiene historial. Devuelve
    (ok: bool, data: dict) — mismo criterio que
    catalog.services.eliminar_servicio_definitivo.

    Un cupón canjeado o usado no se borra: se desactiva (estado=False). Si se
    borrara, se irían con él los `Cupon_Aplicado` (CASCADE) y se perdería el
    rastro de a quién se le cobró el descuento.
    """
    from payments.models import PagoEfectivo, PagoTarjeta

    try:
        cupon = Cupon.objects.get(id=id)
    except (Cupon.DoesNotExist, ValueError):
        return False, {"error": "No se encontró el cupón."}

    canjes = Cupon_Aplicado.objects.filter(cupon=cupon).count()
    pagos = (
        PagoTarjeta.objects.filter(cupon=cupon).count()
        + PagoEfectivo.objects.filter(cupon=cupon).count()
    )
    if canjes or pagos:
        return False, {
            "error": "No se puede eliminar el cupón porque ya tiene historial de uso. "
                     "Desactívalo en su lugar.",
            "canjes": canjes,
            "pagos": pagos,
        }

    titulo = cupon.titulo
    cupon.delete()
    return True, {"titulo": titulo}


def obtener_cupon(pk):
    return Cupon.objects.get(id=pk)


# --------------------------------------------------------------- uso de cupones
def usos_de_cupon(cupon_id):
    """Canjes de un cupón, del más reciente al más viejo. `estado=True` es
    canjeado sin usar; `False` es ya usado en un pago."""
    return Cupon_Aplicado.objects.filter(cupon__id=cupon_id).select_related("cupon")


def estadisticas_cupon(cupon):
    """Los cuatro números que resumen un cupón. `cantidad` es el stock que
    queda por canjear: baja de a uno en `crear_cupon_aplicado`, no al pagar."""
    canjes = Cupon_Aplicado.objects.filter(cupon=cupon)
    usados = canjes.filter(estado=False).count()
    return {
        "canjeados": canjes.count(),
        "usados": usados,
        "pendientes": canjes.filter(estado=True).count(),
        "restantes": max(0, int(cupon.cantidad or 0)),
    }


def vigencia_cupon(cupon):
    """Si el cupón sirve hoy POR SUS FECHAS Y CUPOS: vigente | programado |
    expirado | agotado.

    A propósito NO mira `Cupon.estado`, que es el interruptor manual del admin y
    es una cosa aparte: un cupón puede estar habilitado y aun así estar expirado
    o agotado. Antes esta función devolvía "deshabilitado" y tapaba ese dato, de
    modo que al apagar un cupón ya no se veía por qué tampoco servía. El admin
    muestra ambos por separado.
    """
    from django.utils import timezone

    ahora = timezone.now()
    inicio = _comparable(cupon.fecha_iniciacion)
    fin = _comparable(cupon.fecha_expiracion)

    if inicio and ahora < inicio:
        return "programado"
    if fin and ahora > fin:
        return "expirado"
    if int(cupon.cantidad or 0) <= 0:
        return "agotado"
    return "vigente"


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
            saldo_tras_canje = (usuario.puntos or 0) - cupon.puntos
            if saldo_tras_canje < 0:
                data['valid'] = "puntos"
                data['creado'] = False
            elif cupon.cantidad <= 0:
                data['valid'] = "cantidad"
                data['creado'] = False
            else:
                from accounts.services import registrar_movimiento_puntos
                registrar_movimiento_puntos(usuario, -cupon.puntos, "cupon", referencia=str(cupon_id))
                cupon.cantidad = cupon.cantidad - 1
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
