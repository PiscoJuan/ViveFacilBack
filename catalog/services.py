import datetime

from django.db.models import Q

from accounts.models import Proveedor
from catalog.models import Categoria, Ciudad, Profesion, Profesion_Proveedor, Servicio, SolicitudProfesion
from api.serializers import (
    CategoriaSerializer,
    CiudadSerializer,
    Profesion_ProveedorSerializer,
    ProfesionSerializer,
    ServicioSerializer,
)


def list_profesiones_activas():
    return Profesion.objects.all().filter(estado=1)


def list_servicios(todas=False):
    servicios = Servicio.objects.all()
    if not todas:
        servicios = servicios.filter(estado=True)
    return servicios


def proveedores_activos_por_servicio(servicio_id):
    servicio = Servicio.objects.get(id=servicio_id)
    profesion = Profesion.objects.get(nombre=servicio.nombre)
    return Profesion_Proveedor.objects.all().filter(
        profesion=profesion, proveedor__estado=True
    )


def _notificar_solicitantes(titulo, cuerpo, data_extra):
    from fcm_django.models import FCMDevice
    from core.firebase import send_notificationF

    devices = FCMDevice.objects.filter(active=True, user__groups__name="Solicitante")
    tokens = list(devices.values_list("registration_id", flat=True))
    if tokens:
        send_notificationF(tokens, titulo, cuerpo, data_extra)


def listar_categorias():
    return Categoria.objects.all().filter()


def crear_categoria(nombre, descripcion, foto):
    """Devuelve (categoria_o_None, data: dict)."""
    categoria = Categoria.objects.create(
        nombre=nombre, descripcion=descripcion, foto=foto, foto2=foto
    )
    data = {}
    if categoria:
        _notificar_solicitantes(
            "Nueva Categoría: " + nombre,
            "¡Dale un vistazo!",
            {"ruta": "/main-tabs/home", "descripcion": f"Vive Fácil cuenta con una nueva Categoría llamada {categoria.nombre}"},
        )
        data["categoria"] = CategoriaSerializer(categoria).data
        return categoria, data
    data["error"] = "Error al crear!."
    return None, data


def actualizar_categoria(id, data):
    """Devuelve (serializer_data_o_errors: dict, es_valido: bool)."""
    categoria = Categoria.objects.get(id=id)
    serializer = CategoriaSerializer(categoria, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False

    serializer.save()
    estado = data.get("estado")
    if estado is not None:
        if estado == False:  # noqa: E712 -- réplica exacta de la comparación original
            titulo = "Categoría Desabilitada: " + categoria.nombre
            cuerpo = "¡Sorry, volveremos pronto!"
            descripcion = f"Lamentamos informarles que la Categoría {categoria.nombre} se encuentra fuera de servicio"
        else:
            titulo = "Categoría Habilitada: " + categoria.nombre
            cuerpo = "¡Hemos Vuelto!"
            descripcion = f"Es de nuestro agrado informarles que la Categoría {categoria.nombre} ha regresado nuevamente a su servicio"
        _notificar_solicitantes(titulo, cuerpo, {"descripcion": descripcion, "ruta": "/main-tabs/home"})
    return serializer.data, True


def eliminar_categoria(id):
    """Borra en
    cascada los Servicios de la categoría, igual que el original."""
    categoria = Categoria.objects.get(id=id)
    Servicio.objects.filter(categoria=categoria).delete()
    nombre = categoria.nombre
    categoria.delete()
    _notificar_solicitantes(
        "Categoría Eliminada: " + nombre,
        "¡Sorry, no podrás acceder a la categoría!",
        {"descripcion": f"Lamentamos informarles que la Categoría {nombre} ha sido eliminada de la aplicación", "ruta": "/main-tabs/home"},
    )


def crear_servicio(nombre, descripcion, categoria_nombre, foto):
    """Crea el
    Servicio y, como efecto colateral del original, una Profesion homónima.
    Devuelve (servicio_o_None, data: dict)."""
    data = {}
    if Servicio.objects.filter(nombre=nombre).exists():
        data["error"] = "Ya existe el servicio con el mismo nombre"
        return None, data

    categoria = Categoria.objects.get(nombre=categoria_nombre)
    servicio = Servicio.objects.create(
        nombre=nombre, descripcion=descripcion, categoria=categoria, foto=foto
    )
    data["servicio"] = ServicioSerializer(servicio).data
    Profesion.objects.create(nombre=nombre, descripcion=descripcion, foto=foto)

    _notificar_solicitantes(
        "Nuevo Servicio: " + nombre,
        "¡Dale un vistazo!",
        {"ruta": "/main-tabs/home", "descripcion": f"El servicio {nombre} se ha agregado a nuestro aplicativo"},
    )
    return servicio, data


def actualizar_servicio(id, data):
    """Mantiene en
    sincronía la Profesion homónima con nombre/foto/descripcion del
    Servicio, igual que el original."""
    servicio = Servicio.objects.get(id=id)
    profesion, _creada = Profesion.objects.get_or_create(nombre=servicio.nombre)
    data_actualizar = data.copy()
    categoria = Categoria.objects.get(nombre=data.get("categoria"))
    data_actualizar["categoria"] = categoria.pk
    serializer = ServicioSerializer(servicio, data=data_actualizar, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    servicio_actualizado = Servicio.objects.get(id=id)
    profesion.nombre = servicio_actualizado.nombre
    profesion.foto = servicio_actualizado.foto
    profesion.descripcion = servicio_actualizado.descripcion
    profesion.save()
    return serializer.data, True


def desactivar_servicio(id):
    """El
    original no borra el registro, solo lo desactiva (`estado = 0`)."""
    servicio = Servicio.objects.get(id=id)
    nombre = servicio.nombre
    servicio.estado = 0
    servicio.save()
    _notificar_solicitantes(
        "Servicio Eliminado: " + nombre,
        "¡Sorry, no podrás acceder al Servicio!",
        {"ruta": "/main-tabs/home", "descripcion": f"El servicio {nombre} se ha eliminado de nuestro aplicativo"},
    )


def crear_profesion(nombre, descripcion, servicio_nombre, foto):
    """Devuelve (data: dict) tal cual el original (siempre 200, éxito o error
    en el body, nunca un status HTTP distinto)."""
    data = {}
    try:
        servicio = Servicio.objects.get(nombre=servicio_nombre)
        profesion = Profesion.objects.create(nombre=nombre, descripcion=descripcion)
        profesion.foto = foto
        profesion.servicio.add(servicio)
        profesion.save()
        data["success"] = True
        data["mensaje"] = "Creacion de profesion exitoso"
        data["profesion"] = ProfesionSerializer(profesion).data
    except Exception:
        data["success"] = False
        data["mensaje"] = "Hubo un error al crear la profesion"
    return data


def actualizar_profesion(id, servicio_nombre, data):
    profesion = Profesion.objects.get(id=id)
    servicio_nuevo = Servicio.objects.get(nombre=servicio_nombre)
    profesion.servicio.clear()
    profesion.servicio.add(servicio_nuevo)
    serializer = ProfesionSerializer(profesion, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_profesion(pk):
    Profesion.objects.get(id=pk).delete()


def obtener_profesion(pk):
    return Profesion.objects.get(id=pk)


def listar_ciudades():
    return Ciudad.objects.all().filter()


def crear_ciudad(data):
    serializer = CiudadSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def listar_profesiones_proveedor(user):
    """El `|` duplicado del filtro (mismo filtro combinado consigo mismo)
    es un no-op inofensivo — se deja igual."""
    proveedor_profesiones = Profesion_Proveedor.objects.filter(
        proveedor__user_datos__user=user
    ) | Profesion_Proveedor.objects.filter(proveedor__user_datos__user=user)
    serializer = Profesion_ProveedorSerializer(proveedor_profesiones, many=True)
    data = serializer.data
    for i, _ in enumerate(proveedor_profesiones):
        servicio = Servicio.objects.get(nombre=data[i]["profesion"]["nombre"])
        data[i]["profesion"]["servicio"] = ServicioSerializer(servicio).data
    return data


def crear_profesion_proveedor(user, data):
    """`user` tiene que ser una instancia de `User`, no un username — lo
    compara por FK exacta contra `user_datos__user` y contra
    `FCMDevice.user`. El panel admin (que solo tiene el username a mano)
    entra por `crear_profesion_proveedor_por_username`, que hace ese
    resuelve-y-delega. Preserva un bug preexistente: `titles`/`bodys` quedan
    como tuplas de 1 elemento (coma colgante) en vez de strings."""
    from fcm_django.models import FCMDevice

    from core.firebase import send_notificationF

    profesion = data.get("profesion")
    anios = data.get("ano_experiencia")
    try:
        profesion_obj = Profesion.objects.get(nombre=profesion)
    except Profesion.DoesNotExist:
        return {"success": False, "message": "La profesion con el nombre pasado por parámetro no se ha encontrado en la base de datos."}, None

    try:
        proveedor = Proveedor.objects.get(user_datos__user=user)
    except Proveedor.DoesNotExist:
        return {"success": False, "message": "El correo del proveedor pasado por parámetro no se ha encontrado en la base de datos."}, None

    existe = Profesion_Proveedor.objects.filter(profesion__id=profesion_obj.id, proveedor__id=proveedor.id).first()
    if existe:
        return {"success": False, "message": "Ya existe la tabla Profesion_Proveedor con el mismo proveedor y la misma profesión registrado en la base de datos."}, None

    creada = Profesion_Proveedor.objects.create(proveedor=proveedor, profesion=profesion_obj, ano_experiencia=anios)

    lista = Profesion_Proveedor.objects.all().filter(proveedor__id=proveedor.id)
    proveedor.profesion = ",".join(p.profesion.nombre for p in lista)
    proveedor.save()

    devices = FCMDevice.objects.filter(active=True, user=user)
    tokens = list(devices.values_list("registration_id", flat=True))
    titles = "Tienes una Nueva Profesión: " + profesion,
    bodys = "¡Dale un vistazo!",
    send_notificationF(tokens, titles, bodys, {})

    return {"success": True, "message": "Se ha creado la tabla Profesion_Proveedor y se ha registrado en la base de datos correctamente."}, creada


def crear_profesion_proveedor_por_username(username, data):
    """Usado por el panel admin al aceptar una SolicitudProfesion: solo tiene
    el username del proveedor a mano, no un `User` autenticado como en el
    flujo de autoservicio (`MisProfesionesProveedorView`)."""
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return {"success": False, "message": "No se ha encontrado un usuario con el username pasado por parámetro."}, None
    return crear_profesion_proveedor(user, data)


def actualizar_profesion_proveedor(pk, data):
    """Confirmado exclusivo de Admin2022."""
    profesion_proveedor = Profesion_Proveedor.objects.get(id=pk)
    serializer = Profesion_ProveedorSerializer(profesion_proveedor, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return serializer.data, True
    return serializer.errors, False


def eliminar_profesion_proveedor(pk):
    try:
        profesion = Profesion_Proveedor.objects.get(id=pk)
    except Profesion_Proveedor.DoesNotExist:
        return {"success": False, "message": "No se encontró en la base de datos el objeto Profesion_Proveedor con el ID pasado por parámentro."}
    proveedor = profesion.proveedor
    profesion.delete()
    lista = Profesion_Proveedor.objects.all().filter(proveedor__id=proveedor.id)
    proveedor.profesion = ",".join(p.profesion.nombre for p in lista)
    proveedor.save()
    return {"success": True, "message": "Se ha eliminado el objeto Profesion_Proveedor exitosamente."}


def listar_solicitudes_profesion():
    return SolicitudProfesion.objects.all()


def obtener_solicitudes_profesion():
    """Sin
    evidencia de consumidor en ninguno de los 4 frontends (grep confirmado
    sobre `obtener_solicitudes_profesiones/`) — se migra igual por
    consistencia de namespace, no se borra código sin evidencia externa de
    que nada lo use fuera de este repo."""
    return SolicitudProfesion.objects.all().filter()


def crear_solicitud_profesion(correo_proveedor, nombre_profesion, anio_exp, documento):
    """Consumidor real confirmado: Provedor2022 (`profesion.page.ts`, pide
    agregar una profesión al perfil con años de experiencia y evidencia en
    archivo) — llamaba bajo un nombre de wrapper distinto
    (`postCrearSolicitud`) al de este endpoint, lo que hizo que un grep
    literal por el nombre de la ruta no lo detectara antes. No valida que
    `correo_proveedor` coincida con el usuario autenticado (mismo patrón sin
    ownership-check que el resto de este archivo). Devuelve
    (data: dict, solicitud_o_None)."""
    data = {}
    try:
        proveedorUser = Proveedor.objects.get(user_datos__user__username=correo_proveedor)
    except Exception:
        data['succes'] = False
        data['message'] = 'No se ha encontrado a un proveedor en la base de datos con el correo pasado por parametro.'
        return data, None
    try:
        solicitud = SolicitudProfesion.objects.create(
            proveedor=proveedorUser, profesion=nombre_profesion, anio_experiencia=anio_exp, documento=documento)
    except Exception:
        data['succes'] = False
        data['message'] = 'No se ha podido crear el objeto SolicitudProfesion en la base de datos.'
        return data, None
    return data, solicitud


def actualizar_solicitud_profesion(pk, estado):
    solicitud = SolicitudProfesion.objects.get(id=pk)
    solicitud.estado = estado
    solicitud.fecha = datetime.datetime.now()
    solicitud.save()
    return solicitud


def eliminar_solicitud_profesion(pk):
    solicitud = SolicitudProfesion.objects.get(id=pk)
    if solicitud.documento is not None:
        solicitud.documento.delete()
    solicitud.delete()


def solicitudes_profesion_por_usuario(user):
    """Sin
    evidencia de consumidor en los 4 frontends — `solicitudes-proveedores/<user>`
    no aparece en ningún grep."""
    return SolicitudProfesion.objects.filter(proveedor__user_datos__user__username=user)


def obtener_solicitud_profesion(pk):
    return SolicitudProfesion.objects.get(id=pk)


def buscar_solicitudes_profesion_por_nombre(nombre):
    return SolicitudProfesion.objects.filter(
        Q(proveedor__user_datos__nombres__icontains=nombre) | Q(proveedor__user_datos__apellidos__icontains=nombre))


def filtrar_solicitudes_profesion_por_fecha(fecha_inicio, fecha_fin):
    return SolicitudProfesion.objects.filter(fecha_solicitud__date__range=[fecha_inicio, fecha_fin])


def crear_profesiones_faltantes():
    """Sin evidencia de consumidor real en
    ningún frontend (probable script de mantenimiento manual) — se migra
    igual por consistencia."""
    data = {"profesiones_creadas": [], "errores": []}
    for servicio in Servicio.objects.all():
        if Profesion.objects.filter(nombre=servicio.nombre).first() is not None:
            continue
        try:
            profesion = Profesion.objects.create(
                nombre=servicio.nombre, descripcion=servicio.descripcion, foto=servicio.foto,
            )
            data["profesiones_creadas"].append({"id": profesion.id, "nombre": profesion.nombre})
        except Exception as e:
            data["errores"].append({"servicio_id": servicio.id, "nombre": servicio.nombre, "error": str(e)})
    return data


def profesiones_por_proveedor(proveedor_id):
    """El wrapper `getProfesionProveedor` existe en Admin2022 pero no lo
    invoca ningún componente real."""
    return Profesion_Proveedor.objects.all().filter(proveedor__id=proveedor_id)


def sincronizar_profesion_proveedor():
    """Sin consumidor real confirmado en ningún frontend — probable
    script de mantenimiento manual."""
    data = {"creados": [], "actualizados": [], "errores": []}
    for servicio in Servicio.objects.all():
        try:
            profesion, _ = Profesion.objects.get_or_create(
                nombre=servicio.nombre,
                defaults={"descripcion": servicio.descripcion, "foto": servicio.foto},
            )
            proveedores = Proveedor.objects.filter(profesion=profesion)
            if not proveedores.exists():
                continue
            for proveedor in proveedores:
                _, created = Profesion_Proveedor.objects.update_or_create(
                    profesion=profesion, proveedor=proveedor, ano_experiencia=proveedor.ano_profesion,
                )
                if created:
                    data["creados"].append({"profesion_id": profesion.id, "proveedor_id": proveedor.id})
                else:
                    data["actualizados"].append({"profesion_id": profesion.id, "proveedor_id": proveedor.id})
        except Exception as e:
            data["errores"].append({"servicio_id": servicio.id, "nombre": servicio.nombre, "error": str(e)})
    return data
