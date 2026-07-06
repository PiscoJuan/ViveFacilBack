import datetime

from django.db.models import Q

from api.models import Categoria, Ciudad, Profesion, Profesion_Proveedor, Proveedor, Servicio, SolicitudProfesion
from api.serializers import (
    CategoriaSerializer,
    CiudadSerializer,
    Profesion_ProveedorSerializer,
    ProfesionSerializer,
    ServicioSerializer,
)


def list_profesiones_activas():
    """Replica de Profesiones.get (api/views.py:2536-2545)."""
    return Profesion.objects.all().filter(estado=1)


def list_servicios(todas=False):
    """Replica de Servicios.get (api/views.py:947-958)."""
    servicios = Servicio.objects.all()
    if not todas:
        servicios = servicios.filter(estado=True)
    return servicios


def proveedores_activos_por_servicio(servicio_id):
    """Replica de ProveedoresByProfesion.get (api/views.py:2482-2490)."""
    servicio = Servicio.objects.get(id=servicio_id)
    profesion = Profesion.objects.get(nombre=servicio.nombre)
    return Profesion_Proveedor.objects.all().filter(
        profesion=profesion, proveedor__estado=True
    )


def _notificar_solicitantes(titulo, cuerpo, data_extra):
    """Réplica del patrón repetido de notificación masiva a Solicitantes en
    Categorias/Servicios/Profesiones (api/views.py), Fase 5. Import local de
    `send_notificationF` para evitar el ciclo con `api.views`, mismo patrón
    que `payments.services.registrar_pago_efectivo`."""
    from fcm_django.models import FCMDevice
    from api.views import send_notificationF

    devices = FCMDevice.objects.filter(active=True, user__groups__name="Solicitante")
    tokens = list(devices.values_list("registration_id", flat=True))
    if tokens:
        send_notificationF(tokens, titulo, cuerpo, data_extra)


def listar_categorias():
    """Réplica de Categorias.get (api/views.py:716-721), Fase 5."""
    return Categoria.objects.all().filter()


def crear_categoria(nombre, descripcion, foto):
    """Réplica de Categorias.post (api/views.py:786-815), Fase 5.
    Devuelve (categoria_o_None, data: dict)."""
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
    """Réplica de Categorias.put (api/views.py:723-761), Fase 5.
    Devuelve (serializer_data_o_errors: dict, es_valido: bool)."""
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
    """Réplica de Categorias.delete (api/views.py:763-784), Fase 5. Borra en
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
    """Réplica de Servicios.post (api/views.py:872-910), Fase 5. Crea el
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
    """Réplica de Servicios.put (api/views.py:831-848), Fase 5. Mantiene en
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
    """Réplica de Servicios.delete (api/views.py:850-870), Fase 5. El
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
    """Réplica de Profesiones.post (api/views.py:1725-1743), Fase 5.
    Devuelve (data: dict) tal cual el original (siempre 200, éxito o error
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
    """Réplica de Profesiones.put (api/views.py:1745-1763), Fase 5."""
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
    """Réplica de Profesiones.delete (api/views.py:1765-1769), Fase 5."""
    Profesion.objects.get(id=pk).delete()


def listar_ciudades():
    """Réplica de Ciudades.get (api/views.py:4462-4470), Fase 5."""
    return Ciudad.objects.all().filter()


def crear_ciudad(data):
    """Réplica de Ciudades.post (api/views.py:4472-4477), Fase 5."""
    serializer = CiudadSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def listar_profesiones_proveedor(user):
    """Replica del GET de Proveedor_Profesiones (api/views.py:2983-2999),
    Fase 4. Solo el GET se migra — el POST y el PUT (bajo `profesion_prov/
    <pk>`, usado por Admin, ver docs/refactor/06-fase-4-proveedor.md) se
    quedan en la clase legacy sin tocar, mismo patrón que `Bancos` en la
    Fase 2 (verbo dividido entre roles, la migración completa de la parte
    admin queda para la Fase 5).

    El `|` duplicado del filtro original (mismo filtro combinado consigo
    mismo) es un no-op inofensivo — se deja igual."""
    proveedor_profesiones = Profesion_Proveedor.objects.filter(
        proveedor__user_datos__user=user
    ) | Profesion_Proveedor.objects.filter(proveedor__user_datos__user=user)
    serializer = Profesion_ProveedorSerializer(proveedor_profesiones, many=True)
    data = serializer.data
    for i, _ in enumerate(proveedor_profesiones):
        servicio = Servicio.objects.get(nombre=data[i]["profesion"]["nombre"])
        data[i]["profesion"]["servicio"] = ServicioSerializer(servicio).data
    return data


def listar_solicitudes_profesion():
    """Réplica de SolicitudProfesionProveedor.get (api/views.py:1413-1423), Fase 5."""
    return SolicitudProfesion.objects.all()


def obtener_solicitudes_profesion():
    """Réplica de ManejoSolicitud.get (api/views.py:1427-1431), Fase 5. Sin
    evidencia de consumidor en ninguno de los 4 frontends (grep confirmado
    sobre `obtener_solicitudes_profesiones/`) — se migra igual por
    consistencia de namespace, no se borra código sin evidencia externa de
    que nada lo use fuera de este repo."""
    return SolicitudProfesion.objects.all().filter()


def crear_solicitud_profesion(correo_proveedor, nombre_profesion, anio_exp, documento):
    """Réplica de ManejoSolicitud.post (api/views.py:1433-1456), Fase 5. Sin
    evidencia de consumidor real (`crear_solicitud_profesion/` no aparece en
    ningún grep de los 4 frontends). Devuelve (data: dict, solicitud_o_None)."""
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
    """Réplica de ManejoSolicitud.put (api/views.py:1458-1465), Fase 5."""
    solicitud = SolicitudProfesion.objects.get(id=pk)
    solicitud.estado = estado
    solicitud.fecha = datetime.datetime.now()
    solicitud.save()
    return solicitud


def eliminar_solicitud_profesion(pk):
    """Réplica de ManejoSolicitud.delete (api/views.py:1467-1472), Fase 5."""
    solicitud = SolicitudProfesion.objects.get(id=pk)
    if solicitud.documento is not None:
        solicitud.documento.delete()
    solicitud.delete()


def solicitudes_profesion_por_usuario(user):
    """Réplica de SolicitudByName.get (api/views.py:1509-1516), Fase 5. Sin
    evidencia de consumidor en los 4 frontends — `solicitudes-proveedores/<user>`
    no aparece en ningún grep."""
    return SolicitudProfesion.objects.filter(proveedor__user_datos__user__username=user)


def obtener_solicitud_profesion(pk):
    """Réplica de SolicitudDetails.get (api/views.py:1519-1525), Fase 5."""
    return SolicitudProfesion.objects.get(id=pk)


def buscar_solicitudes_profesion_por_nombre(nombre):
    """Réplica de Solicitudes_Search_Name.get (api/views.py:1528-1540), Fase 5."""
    return SolicitudProfesion.objects.filter(
        Q(proveedor__user_datos__nombres__icontains=nombre) | Q(proveedor__user_datos__apellidos__icontains=nombre))


def filtrar_solicitudes_profesion_por_fecha(fecha_inicio, fecha_fin):
    """Réplica de Solicitudes_Filter_Date.get (api/views.py:1543-1558), Fase 5."""
    return SolicitudProfesion.objects.filter(fecha_solicitud__date__range=[fecha_inicio, fecha_fin])


def crear_profesiones_faltantes():
    """Réplica de CrearProfesionesFaltantesView.post (api/views.py:853-890),
    cleanup post-Fase-5, Bloque 4. Sin evidencia de consumidor real en
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
    """Réplica de ProfesionProveedor.get (api/views.py:903-907), cleanup
    post-Fase-5, Bloque 4. El wrapper `getProfesionProveedor` existe en
    Admin2022 pero grep fresco sobre componentes confirma **cero
    llamadores reales** (código muerto, corrige la suposición inicial del
    checklist) — se migra igual por consistencia y se actualiza el
    wrapper del frontend de todos modos."""
    return Profesion_Proveedor.objects.all().filter(proveedor__id=proveedor_id)


def sincronizar_profesion_proveedor():
    """Réplica de SincronizarProfesionProveedorView.post (api/views.py:740-791),
    cleanup post-Fase-5, Bloque 4. Sin evidencia de consumidor real en
    ningún frontend (grep fresco sobre los 4, cero resultados) — probable
    script de mantenimiento manual, se migra igual por consistencia."""
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
