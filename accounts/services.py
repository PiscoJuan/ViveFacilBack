import datetime
import threading

from django.contrib.auth import authenticate as authenticate_django
from django.contrib.auth import login as do_login
from django.contrib.auth import logout as do_logout
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Q
from rest_framework import status
from rest_framework.authtoken.models import Token

from api.models import (
    Administrador,
    Cardauth,
    Datos,
    Document,
    PendienteDocuments,
    Profesion,
    Profesion_Proveedor,
    Proveedor,
    Proveedor_Pendiente,
    Solicitante,
)
from api.serializers import DocumentSerializer, Proveedor_PendienteSerializer


def get_proveedor_pendiente_activo_por_email(mail):
    """Replica de Proveedores_Pendientes_Email (api/views.py:1644-1660)."""
    return (
        Proveedor_Pendiente.objects.filter(email=mail, estado=False)
        .filter(Q(rechazo__isnull=True) | Q(rechazo=""))
        .first()
    )


def crear_proveedor_pendiente(data, files):
    """Replica de Proveedor_Pendiente_Admin.post (api/views.py:1570-1643,
    la vista que en realidad atiende el formulario público "quiero ser
    proveedor" pese al nombre — ver docs/refactor/04-fase-2-web.md).

    Se omite a propósito la línea original `data['data'] = {nombres_prov}`:
    asignaba un `set` de Python a una respuesta JSON, no serializable por
    DRF — hacía fallar la respuesta con un 500 después de guardar el
    registro en la base. Se corrige acá al mover el código.

    El `threading.Thread(...)` sin `.start()` de abajo replica un patrón
    repetido en todo `api/views.py`: el `target=` se evalúa (y por lo tanto
    el email se manda) al construir el `Thread`, nunca llega a ejecutarse
    en background. Se deja igual a propósito — arreglarlo es un cambio de
    comportamiento (timing) fuera del alcance de esta fase.
    """
    proveedor_pend = Proveedor_Pendiente.objects.create(
        nombres=data.get("nombres"),
        apellidos=data.get("apellidos"),
        genero=data.get("genero"),
        telefono=data.get("telefono"),
        cedula=data.get("cedula"),
        copiaCedula=files.get("copiaCedula"),
        ciudad=data.get("ciudad"),
        direccion=data.get("direccion"),
        email=data.get("email"),
        licencia=data.get("licencia"),
        copiaLicencia=files.get("copiaLicencia"),
        profesion=data.get("profesion"),
        ano_experiencia=data.get("ano_experiencia"),
        banco=data.get("banco"),
        numero_cuenta=data.get("numero_cuenta"),
        tipo_cuenta=data.get("tipo_cuenta"),
        descripcion=data.get("descripcion"),
        foto=data.get("foto"),
    )
    for doc in files.getlist("filesDocuments"):
        documento_creado = PendienteDocuments.objects.create(document=doc)
        proveedor_pend.documentsPendientes.add(documento_creado)

    from api.views import FormatEmail  # import local: evita ciclo con api.views

    format_email = FormatEmail()
    nombre_completo = f"{data.get('nombres')} {data.get('apellidos')}"
    threading.Thread(
        target=format_email.send_email(
            [data.get("email")],
            "Solicitud Enviada",
            "emails/formularioEnviado.html",
            {"username": nombre_completo, "user": data.get("email")},
        )
    )

    serializer = Proveedor_PendienteSerializer(proveedor_pend)
    return proveedor_pend, serializer


def authenticate_login(request, username, password, expected_role):
    """Replica de Login.post()/LoginAdmin.post() (api/views.py:4113-4210),
    generalizada para los 3 roles vía `expected_role` en vez de duplicar la
    lógica por rol (AuthService, ver docs/refactor/05-fase-3-solicitante.md).

    Corrige un bug latente encontrado al mover el código: si
    `authenticate_django` devuelve None, el `Login.post()` original no tenía
    un `else` para ese caso y devolvía implícitamente `None` en vez de un
    `Response` — DRF lanza un `AssertionError` (500). En `Login.post()` casi
    nunca se llegaba a ejecutar (AuthenticationForm ya rechaza credenciales
    inválidas antes), pero es la única validación de `LoginSolicitanteView`
    (que no usa AuthenticationForm), así que ahí sí hace falta el `else`.

    Devuelve (data: dict, http_status: int)."""
    user = authenticate_django(username=username, password=password)
    if user is None:
        return {"error": "Usuario no permitido", "active": True}, status.HTTP_400_BAD_REQUEST

    do_login(request, user)
    usuario = Datos.objects.get(user=user)
    tipo = usuario.tipo.name
    if tipo != expected_role:
        return {"error": "Usuario no permitido", "active": True}, status.HTTP_400_BAD_REQUEST
    if not usuario.estado:
        if expected_role == "Administrador":
            # Réplica exacta de LoginAdmin.post() (api/views.py:3198, Fase 5):
            # a diferencia de Proveedor/Solicitante (que acá mismo devuelven
            # 400 "Usuario no permitido"), una cuenta de Administrador
            # deshabilitada a nivel Datos respondía 200 con active=False, sin
            # token ni mensaje de error. Confirmado via `git diff` contra el
            # Login.post() original: Proveedor/Solicitante NUNCA tuvieron esta
            # rama, es exclusiva de LoginAdmin.
            return {"active": False}, status.HTTP_200_OK
        return {"error": "Usuario no permitido", "active": True}, status.HTTP_400_BAD_REQUEST

    token, _ = Token.objects.get_or_create(user=user)
    data = {"token": token.key, "active": True}

    if expected_role == "Proveedor":
        proveedor = Proveedor.objects.get(user_datos=usuario)
        if not proveedor.estado:
            data["clave"] = usuario.security_access
    elif expected_role == "Administrador":
        admin = Administrador.objects.get(user_datos=usuario)
        if not admin.estado:
            data["clave"] = usuario.security_access
    # Solicitante no tiene chequeo de estado adicional en el original.

    return data, status.HTTP_200_OK


def cambiar_contrasenia_firebase(firetoken, password):
    """Replica exacta de CambioContrasenia.post (api/views.py:798-843).
    Devuelve (data: dict, http_status: int)."""
    from firebase_admin import auth as fire_auth
    from django.contrib.auth.models import User
    from django.core.exceptions import ObjectDoesNotExist

    data = {"success": False}
    try:
        decoded_token = fire_auth.verify_id_token(firetoken)
        email = decoded_token.get("email")
        if not email:
            data["message"] = "El token no contiene un correo electrónico válido."
            return data, 400
        usuario = User.objects.get(email=email)
    except fire_auth.InvalidIdTokenError:
        data["message"] = "El token de Firebase es inválido."
        return data, 401
    except fire_auth.ExpiredIdTokenError:
        data["message"] = "El token de Firebase ha expirado."
        return data, 401
    except User.DoesNotExist:
        data["message"] = f"No existe un usuario con el correo {email} en la base de datos."
        return data, 404
    except Exception as e:
        data["message"] = f"Error inesperado al verificar el usuario: {str(e)}"
        return data, 500

    try:
        Datos.objects.get(user=usuario)
    except ObjectDoesNotExist:
        data["message"] = f"No existe un registro en la tabla Datos para el usuario {usuario.email}."
        return data, 404
    except Exception as e:
        data["message"] = f"Error al consultar Datos: {str(e)}"
        return data, 500

    usuario.set_password(password)
    usuario.save()
    data["success"] = True
    data["message"] = "Contraseña cambiada con éxito"
    return data, 200


def buscar_cvc_tarjeta(token):
    """Replica de CardsAuth.get (api/views.py:230-248)."""
    return Cardauth.objects.get(token=token).auth


def guardar_cvc_tarjeta(token, cvc):
    """Replica de CardsAuth.post (api/views.py:250-277). Si ya existe una
    credencial con ese token, el original NO la actualiza (solo crea si no
    existía) — devuelve False en ese caso, tal cual el 'valid': 'NO' viejo."""
    if Cardauth.objects.filter(token=token).exists():
        return False
    Cardauth.objects.create(token=token, auth=cvc)
    return True


def eliminar_cvc_tarjeta(token):
    """Replica de CardsAuth.delete (api/views.py:279-297). Devuelve
    (success: bool, message: str)."""
    try:
        Cardauth.objects.get(token=token).delete()
        return True, "Credencial eliminada exitosamente"
    except Cardauth.DoesNotExist:
        return False, "No se encontró la credencial con el token proporcionado"


def registrar_dispositivo(request, token):
    """Replica de DeviceNotification.post (api/views.py:591-609)."""
    from fcm_django.models import FCMDevice

    if FCMDevice.objects.filter(active=True, registration_id=token).exists():
        return {"message": "Token existente."}, 400
    if not request.user.is_authenticated:
        return {"message": "Usuario no identificado."}, 400
    device = FCMDevice(registration_id=token, active=True, user=request.user)
    device.save()
    return {"message": "Token guardado."}, 200


def registrar_proveedor(email, tipo, nombres, apellidos, telefono, genero, foto):
    """Replica de Register_Proveedor.post (api/views.py:1106-1160), Fase 4.

    Sin evidencia de llamador real en ninguno de los 4 frontends (grep
    confirmado): `ViveFacil_Provedor2022` usa el router DRF `registro/`
    (`postRegistro`) para el alta real, no este endpoint. Se migra igual
    por consistencia de namespace — ver docs/refactor/06-fase-4-proveedor.md.
    Devuelve (data: dict, http_status: int), status siempre 200 como el
    original (nunca seteaba status explícito).

    Bug real encontrado y corregido al mover el código: el original llamaba
    `email.send_email(user_email, ...)` pasando un string en vez de una
    lista — `EmailMultiAlternatives` exige `to` como lista/tupla, así que
    esto lanzaba un `TypeError` (500) cada vez que el registro se
    completaba con éxito, DESPUÉS de crear el usuario en la base. Se
    corrige envolviendo `email` en una lista, igual que hace
    `crear_proveedor_pendiente` más arriba en este mismo archivo.

    Segundo bug encontrado, NO corregido a propósito: la rama
    `tipo == "Proveedor"` hace `Proveedor.objects.create(user_datos=dato,
    bool_registro_completo=True)`, pero el modelo `Proveedor` (api/models.py)
    no tiene ningún campo `bool_registro_completo` — esto lanza un
    `TypeError` real e independiente del bug de arriba. No hay forma de
    inferir desde el código qué campo se quiso setear originalmente (pudo
    borrarse en una migración, o nunca haber existido); arreglarlo a
    ciegas sería inventar comportamiento nuevo, no migrar el existente.
    Entre los dos bugs, esta rama de éxito nunca pudo haber funcionado —
    confirma por qué no hay evidencia de llamador real en ningún frontend."""
    from django.contrib.auth.models import Group, User

    from api.views import FormatEmail

    if User.objects.filter(username=email).exists():
        return {"error": "Usuario ya existente!."}, 200

    password_user = User.objects.make_random_password()
    usuario = User.objects.create_user(email=email, username=email, password=password_user)
    dato, creado = Datos.objects.get_or_create(
        user=usuario,
        tipo=Group.objects.get(name="Proveedor"),
        nombres=nombres,
        apellidos=apellidos,
        telefono=telefono,
        genero=genero,
        foto=foto,
    )
    if not creado:
        return {"error": "Esta persona ya existe1!."}, 200

    format_email = FormatEmail()
    thread = threading.Thread(
        target=format_email.send_email(
            [email], "Bienvenido a Vive Fácil", "emails/welcome.html", {"username": nombres}
        )
    )
    thread.start()

    if tipo == "Proveedor":
        Proveedor.objects.create(user_datos=dato, bool_registro_completo=True)

    token = Token.objects.get(user=dato.user).key
    return {"email": dato.user.email, "username": dato.user.username, "token": token}, 200


def actualizar_documento_proveedor(username, descripcion, data):
    """Replica de Documentos_proveedor.put (api/views.py:2285-2295), Fase 4.

    La URL vieja capturaba `<str:username>` pero el método original nunca lo
    declaraba en su firma (`put(self, request, format=None)`) — con DRF,
    cualquier PUT real a esa ruta habría lanzado un TypeError por el kwarg
    inesperado (probablemente por eso nunca se detectó: sin llamador
    confirmado en ningún frontend). Se corrige acá aceptando `username` para
    que la ruta sea al menos invocable — no se usa en el cuerpo, igual que
    el original no lo necesitaba."""
    documento = Document.objects.get(descripcion=descripcion)
    serializer = DocumentSerializer(documento, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return serializer.data, 200
    return serializer.errors, 400


def actualizar_datos_usuario(email, data, files):
    """Replica exacta de Dato.put (api/views.py:2668-2692), Fase 4. Endpoint
    multi-rol (`dato/<user>`, confirmado usado por Solicitante2022 y
    Provedor2022 vía grep) — no estaba tageado como tal en `urls.py` ni se
    había detectado en la Fase 3, se resuelve acá con el mismo mecanismo de
    doble-registro.

    El `if persona:` original es código muerto: `Datos.objects.get(...)` ya
    lanza `DoesNotExist` antes de llegar ahí si no existe — se deja igual,
    es el comportamiento real de hoy (la excepción la maneja el
    EXCEPTION_HANDLER global desde la Fase 1, antes y después de este
    movimiento)."""
    persona = Datos.objects.get(user__email=email)
    persona.nombres = data.get("nombres")
    persona.ciudad = data.get("ciudad")
    persona.cedula = data.get("cedula")
    persona.apellidos = data.get("apellidos")
    persona.genero = data.get("genero")
    persona.telefono = data.get("telefono")
    if "foto" in files:
        persona.foto = files.get("foto")
    persona.codigo_invitacion = data.get("codigo_invitacion")
    persona.puntos = data.get("puntos")
    persona.save()


def eliminar_dispositivos_por_correo(correo):
    """Replica de DeviceNotification.delete (api/views.py:611-628).

    Bug real encontrado y corregido al mover el código: el original arma
    `'...#' + num_devices + '...'` concatenando un int con str, lo que lanza
    un TypeError (500) DESPUÉS de haber borrado los dispositivos de la base
    — y este endpoint sí lo llaman ambos frontends (Solicitante2022 y
    Provedor2022) vía DELETE en cada logout. Se corrige acá con `str(count)`;
    el resto del comportamiento (qué se borra, cuándo) queda idéntico."""
    from fcm_django.models import FCMDevice

    devices = FCMDevice.objects.filter(active=True, user__email=correo)
    count = devices.count()
    if count == 0:
        return {"success": False, "message": "No se han encontrados dispositivos con el correo: " + correo + " registrados en la base de datos"}, 200
    for device in devices:
        device.delete()
    return {"success": True, "message": "Se han eliminado #" + str(count) + " de los dispositivos registrados con el correo" + correo}, 200


# ---------------------------------------------------------------------------
# Fase 5, Bloque 2 — gestión de cuentas y usuarios (admin). Todas las vistas
# legacy de este bloque no tenían ningún permission_classes (comentado en el
# código original) — cualquiera, sin sesión, podía gestionar administradores,
# solicitantes y proveedores. La ruta nueva exige IsAdministrador
# estructuralmente; la legacy queda igual de abierta hasta observar tráfico.
# ---------------------------------------------------------------------------

def listar_administradores_queryset():
    return Administrador.objects.all().order_by("-id")


def crear_administrador(data, foto):
    """Replica de Administradores.post (api/views.py:2455-2522)."""
    from firebase_admin import auth as fire_auth

    out = {}
    email = data.get("email")
    try:
        if User.objects.filter(email=email).exists():
            raise Exception("Ya registrado")
        usuario = User.objects.create_user(email=email, username=email, password=data.get("password"))
        grupo = Group.objects.get(name=data.get("rol"))
        grupo.user_set.add(usuario)
    except Exception:
        out["error"] = "Usuario ya existente!."
        return out

    try:
        user_record = fire_auth.get_user_by_email(email)
        fire_auth.update_user(user_record.uid, password=data.get("password"))
    except fire_auth.UserNotFoundError:
        try:
            fire_auth.create_user(email=email, password=data.get("password"))
        except Exception as e:
            out["error"] = f"Error al crear el nuevo usuario en firebase: {e}"
            return out
    except Exception as e:
        out["error"] = f"Error inesperado al intentar verificar o gestionar el usuario: {e}"
        return out

    datoCreado = Datos.objects.create(
        user=usuario, tipo=Group.objects.get(name="Administrador"),
        nombres=data.get("nombres"), apellidos=data.get("apellidos"),
        telefono=data.get("telefono"), genero=data.get("genero"),
        ciudad=data.get("ciudad"), cedula=data.get("cedula"),
    )
    datoCreado.foto = foto
    datoCreado.save()
    Administrador.objects.create(user_datos=datoCreado)
    token = Token.objects.get(user=datoCreado.user).key
    out.update({
        "nombre": data.get("nombres"), "apellido": data.get("apellidos"),
        "telefono": data.get("telefono"), "ciudad": data.get("ciudad"),
        "cedula": data.get("cedula"), "genero": data.get("genero"),
        "email": email, "pass": data.get("password"), "token": token, "sucess": True,
    })
    return out


def cambiar_estado_administrador(admin_id, estado):
    """Replica de Administradores.put (api/views.py:2524-2532) — `estado`
    se aplica tanto a Administrador como a Datos."""
    admin = Administrador.objects.get(id=admin_id)
    persona = Datos.objects.get(id=admin.user_datos.id)
    admin.estado = estado
    persona.estado = estado
    persona.save()
    admin.save()


def eliminar_administrador(admin_id):
    """Replica de Administradores.delete / Admin_Details.delete (ambas
    hacen exactamente lo mismo: borrado duro del registro Administrador)."""
    Administrador.objects.get(id=admin_id).delete()


def obtener_administrador(pk):
    return Administrador.objects.get(id=pk)


def actualizar_administrador(pk, data, files):
    """Replica de Admin_Details.put (api/views.py:2548-2590). El `if
    persona:` original es código muerto (Datos.objects.get ya lanza
    DoesNotExist si no existe) — se deja igual, mismo patrón que
    actualizar_datos_usuario más arriba en este archivo."""
    admin = Administrador.objects.get(id=data.get("id"))
    persona = Datos.objects.get(user__email=data.get("email"))
    user = User.objects.get(email=data.get("email"))

    if User.objects.filter(email=data.get("emailNuevo")).exists():
        existente = User.objects.get(email=data.get("emailNuevo"))
        if user.id != existente.id:
            return {"error": "Email ya registrado"}, 200
        user.email = existente.email
    user.email = data.get("emailNuevo")
    user.username = data.get("emailNuevo")
    user.save()

    if data.get("rol"):
        if user.groups.all().count() > 0:
            Group.objects.get(id=user.groups.all()[0].id).user_set.remove(user)
        Group.objects.get(name=data.get("rol")).user_set.add(user)

    persona.nombres = data.get("nombres")
    persona.ciudad = data.get("ciudad")
    persona.cedula = data.get("cedula")
    persona.apellidos = data.get("apellidos")
    persona.telefono = data.get("telefono")
    persona.genero = data.get("genero")
    admin.save()
    persona.codigo_invitacion = data.get("codigo_invitacion")
    persona.puntos = data.get("puntos")
    if "foto" in files:
        persona.foto = files.get("foto")
    persona.save()
    return {}, 200


def listar_solicitantes_queryset(filtro):
    """Replica de Solicitantes.get (api/views.py:2367-2378)."""
    queryset = Solicitante.objects.all().order_by("-id")
    if filtro == "activos":
        queryset = queryset.filter(estado=True).order_by("-id")
    elif filtro == "inactivos":
        queryset = queryset.filter(estado=False).order_by("-id")
    return queryset


def actualizar_solicitante(id, data):
    """Replica de Solicitantes.put (api/views.py:2385-2396)."""
    from api.serializers import DatosSerializer, SolicitanteSerializer

    solicitante = Solicitante.objects.get(id=id)
    datoObj = Datos.objects.get(id=solicitante.user_datos.id)
    serializerDato = DatosSerializer(datoObj, data=data, partial=True)
    serializer = SolicitanteSerializer(solicitante, data=data, partial=True)
    if serializer.is_valid() and serializerDato.is_valid():
        serializer.save()
        serializerDato.save()
        return serializer.data, 200
    return serializer.errors, 400


def eliminar_solicitante(id):
    Solicitante.objects.get(id=id).delete()


def listar_proveedores_queryset():
    """Replica del queryset de Proveedores (api/views.py:1640)."""
    return Proveedor.objects.all().exclude(user_datos__tipo=4).order_by("-id")


def actualizar_proveedor(id, data):
    """Replica de Proveedores.put (api/views.py:1657-1668)."""
    from api.serializers import DatosSerializer, ProveedorSerializer

    proveedor = Proveedor.objects.get(id=id)
    datoObj = Datos.objects.get(id=proveedor.user_datos.id)
    serializerDato = DatosSerializer(datoObj, data=data, partial=True)
    serializer = ProveedorSerializer(proveedor, data=data, partial=True)
    if serializer.is_valid() and serializerDato.is_valid():
        serializer.save()
        serializerDato.save()
        return serializer.data, 200
    return serializer.errors, 400


def desactivar_proveedor(id):
    """Replica de Proveedores.delete (api/views.py:1670-1677) — pese al
    nombre del endpoint (`proveedor_delete/<id>`), es un soft-delete: solo
    desactiva `estado` en Proveedor y Datos, no borra ningún registro."""
    proveedor = Proveedor.objects.get(id=id)
    proveedor.estado = False
    proveedor.save()
    datos = proveedor.user_datos
    datos.estado = False
    datos.save()


# --- Trío Proveedores_Pendientes / Proveedores_Rechazados / Proveedores_Proveedores ---
# Las 3 clases legacy comparten put/delete byte-idénticos operando siempre
# sobre Proveedor_Pendiente (incluso la de "Proveedores_Proveedores", cuya
# lista es de Proveedor pero cuyo put/delete de gestión de documentos opera
# sobre Proveedor_Pendiente igual que las otras dos — copy-paste confirmado
# leyendo las 3 clases). Se comparte una sola implementación acá: no cambia
# el comportamiento de ningún endpoint, solo evita pegar el mismo código 3
# veces en la nueva base.

def eliminar_documento_pendiente_admin(username, desc):
    """Replica del `delete(self, request, username, desc)` compartido por
    Proveedores_Pendientes/Rechazados/Proveedores (api/views.py:2012-2029,
    2101-2118, 2203-2220)."""
    proveedor_pendiente = Proveedor_Pendiente.objects.get(
        proveedor__user_datos__user__username=username)
    descripcion = desc.split("|")
    documento = Document.objects.get(descripcion=descripcion[0])
    if descripcion[1] == "true":
        from api.serializers import DocumentSerializer as DocSer
        serializer = DocSer(documento, data={"estado": True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            proveedor_pendiente.delete()
            return serializer.data, 200
        return serializer.errors, 400
    documento.delete()
    proveedor_pendiente.delete()
    return None, 200


def actualizar_descripcion_documento_pendiente_admin(descripcion, profesion):
    """Replica del `put(self, request)` compartido por las 3 clases de
    arriba (api/views.py:2031-2045, 2120-2134, 2222-2236). El código muerto
    tras el `return` original (un segundo bloque que arma un `Cuenta`/
    `Proveedor_Pendiente` nuevo, inalcanzable porque siempre se retorna
    antes) no se replica — nunca se ejecutaba."""
    documento = Document.objects.get(descripcion=descripcion, estado=False)
    documento.descripcion = profesion
    documento.save()
    serializer = DocumentSerializer(documento, data={"descripcion": profesion}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return {"success": True}, 200
    return {"success": False}, 200


def listar_proveedores_pendientes_queryset():
    return Proveedor_Pendiente.objects.all().order_by("-id").filter(estado=0)


def listar_proveedores_rechazados_queryset():
    return Proveedor_Pendiente.objects.filter(estado=1).filter(
        Q(rechazo__isnull=False) & ~Q(rechazo="")).order_by("-id")


def listar_proveedores_proveedores_queryset():
    """Replica del queryset de listado de Proveedores_Proveedores
    (api/views.py:2192) — Proveedor, no Proveedor_Pendiente (a diferencia
    de su propio put/delete, ver nota del trío arriba).

    El escaneo de caducidad + envío de emails + desactivación de cuentas que
    la clase original ejecuta a nivel de módulo (api/views.py:2178-2191, NO
    dentro de ningún método — se dispara una vez por cada import de
    api.views, es decir en cada arranque del servidor o `manage.py`) NO se
    replica ni se mueve acá a propósito: es un hallazgo real de producción,
    ajeno a esta migración de namespaces, que requiere decisión de producto
    (ver docs/refactor/CHECKLIST-inventario-endpoints.md). Como la clase
    legacy `Proveedores_Proveedores` en api/views.py se mantiene definida
    (solo sus métodos pasan a delegar acá), ese efecto secundario sigue
    disparándose exactamente igual que antes — una sola vez, no duplicado."""
    return Proveedor.objects.all().order_by("-id")


def obtener_proveedor_pendiente(pk):
    return Proveedor_Pendiente.objects.get(id=pk)


def actualizar_proveedor_pendiente_detalle(pk, data, files):
    """Replica de Proveedores_Pendientes_Details.put (api/views.py:1077-1131)."""
    pendiente = Proveedor_Pendiente.objects.get(id=pk)
    if data.get("copiaCedula") is not None:
        pendiente.copiaCedula.delete()
    if data.get("copiaLicencia") is not None:
        pendiente.copiaLicencia.delete()
    if data.get("foto") is not None:
        pendiente.foto.delete()
    for doc in files.getlist("filesDocuments"):
        documento_creado = PendienteDocuments.objects.create(document=doc)
        pendiente.documentsPendientes.add(documento_creado)

    from django.utils import timezone
    pendiente.fecha_registro = timezone.now()
    serializer = Proveedor_PendienteSerializer(pendiente, data=data, partial=True)
    profesiones_lista = data.get("profesion").split(",")
    if profesiones_lista:
        Profesion_Proveedor.objects.all().filter(proveedor=pendiente).delete()
        for profesion in profesiones_lista:
            profesion_obj = Profesion.objects.filter(nombre=profesion)
            if profesion_obj:
                Profesion_Proveedor.objects.get_or_create(
                    proveedor=pendiente, profesion=profesion_obj.get())
    if serializer.is_valid():
        serializer.save()
        return serializer.data, 200
    return serializer.errors, 400


def pendiente_marcar_procesado(pk):
    """Replica de Proveedores_Pendientes_Details.delete (api/views.py:1133-1147)
    y de Proveedores_Proveedores_Details.delete (api/views.py:1292-1306) —
    ambas hacen exactamente lo mismo: `estado = 1` sobre Proveedor_Pendiente."""
    pendiente = Proveedor_Pendiente.objects.get(id=pk)
    pendiente.estado = 1
    pendiente.save()


def pendiente_aprobar_por_id(ident):
    """Replica de Proveedores_Pendientes_Estado.put (api/views.py:1151-1156)
    — mismo efecto que pendiente_marcar_procesado (estado=1)."""
    pendiente_marcar_procesado(ident)


def pendiente_rechazar(pk, razon):
    """Replica de Proveedores_Pendientes_Details2.put (api/views.py:1160-1171).

    El `threading.Thread(...)` de abajo se crea sin `.start()` en el
    original — mismo patrón repetido en todo api/views.py (el email se
    manda igual, de forma síncrona, al construir el Thread). Se deja igual
    a propósito, no es parte del alcance de esta migración."""
    from api.views import FormatEmail

    pendiente = Proveedor_Pendiente.objects.get(id=pk)
    pendiente.estado = 1
    pendiente.rechazo = razon
    pendiente.save()
    formatEmail = FormatEmail()
    threading.Thread(target=formatEmail.send_email(
        [pendiente.email], "Solicitud Rechazada", "emails/formularioRechazado.html",
        {"username": pendiente.nombres + " " + pendiente.apellidos, "user": pendiente.email, "razon": razon}))


def obtener_proveedor_rechazado(pk):
    """Replica de Proveedores_Rechazados_Details.get (api/views.py:1333-1337)
    — usa Proveedor_PendienteSerializer2, no el Serializer normal (ambos
    serializers son idénticos campo a campo, ver api/serializers.py:184-198;
    la distinción parece vestigial, se preserva igual)."""
    return Proveedor_Pendiente.objects.get(id=pk)


def actualizar_proveedor_rechazado_detalle(pk, data, files):
    """Replica de Proveedores_Rechazados_Details.put (api/views.py:1339-1360)."""
    pendiente = Proveedor_Pendiente.objects.get(id=pk)
    if data.get("copiaCedula") is not None:
        pendiente.copiaCedula.delete()
    if data.get("copiaLicencia") is not None:
        pendiente.copiaLicencia.delete()
    for doc in files.getlist("filesDocuments"):
        documento_creado = PendienteDocuments.objects.create(document=doc)
        pendiente.documentsPendientes.add(documento_creado)
    serializer = Proveedor_PendienteSerializer(pendiente, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return serializer.data, 200
    return serializer.errors, 400


def rechazado_revertir_a_pendiente(pk):
    """Replica de Proveedores_Rechazados_Details.delete (api/views.py:1362-1376)
    — pese a estar en un endpoint DELETE, no borra nada: pone `estado = 0`,
    lo que en la práctica revierte el rechazo (vuelve a aparecer como
    pendiente). Nombre del método deliberadamente distinto de
    `pendiente_marcar_procesado` porque el efecto es el opuesto (0, no 1)."""
    pendiente = Proveedor_Pendiente.objects.get(id=pk)
    pendiente.estado = 0
    pendiente.save()


def obtener_proveedor_proveedores_detalle(pk):
    """Replica de Proveedores_Proveedores_Details.get (api/views.py:1175-1179).

    Hallazgo real: pese a que la clase se llama "Proveedores_Proveedores" y
    su PUT/DELETE operan sobre el modelo `Proveedor`, su GET busca en
    `Proveedor_Pendiente` (mismo bug de copy-paste que el resto del trío).
    Se preserva tal cual — devuelve datos de Proveedor_Pendiente, no de
    Proveedor, para este endpoint específico."""
    return Proveedor_Pendiente.objects.get(id=pk)


def actualizar_proveedor_proveedores_detalle(pk, data, files):
    """Replica de Proveedores_Proveedores_Details.put (api/views.py:1181-1290).
    Único método de este archivo que además sincroniza el email en Firebase
    Auth cuando cambia — se preserva la transacción atómica y el manejo de
    excepciones (captura genérica que devuelve 400 con la excepción cruda
    como body, igual que el original, aunque no sea JSON-serializable en
    todos los casos — comportamiento preexistente, no se toca)."""
    from django.db import transaction
    from django.utils import timezone
    from firebase_admin import auth as fire_auth
    from api.serializers import ProveedorSerializer

    try:
        with transaction.atomic():
            pendiente = Proveedor.objects.get(id=pk)
            if data.get("copiaCedula") is not None:
                pendiente.copiaCedula.delete()
            if data.get("copiaLicencia") is not None:
                pendiente.copiaLicencia.delete()
            for doc in files.getlist("filesDocuments"):
                documento_creado = Document.objects.create(documento=doc)
                pendiente.document.add(documento_creado)

            if "user_datos" in data:
                import json as json_module
                user_datos_str = data["user_datos"]
                user_datos = json_module.loads(user_datos_str) if isinstance(user_datos_str, str) else user_datos_str
                pendiente.user_datos.nombres = user_datos.get("nombres")
                pendiente.user_datos.apellidos = user_datos.get("apellidos")
                pendiente.user_datos.cedula = user_datos.get("cedula")
                pendiente.user_datos.ciudad = user_datos.get("ciudad")
                pendiente.user_datos.telefono = user_datos.get("telefono")
                pendiente.user_datos.genero = user_datos.get("genero")
                pendiente.user_datos.foto = data.get("foto") or pendiente.user_datos.foto
                pendiente.user_datos.fecha_creacion = timezone.now()
                pendiente.user_datos.save()

                email_actual = pendiente.user_datos.user.email
                email_nuevo = data.get("email")
                if not email_nuevo:
                    raise Exception("Email no puede ser null")
                if email_actual != email_nuevo:
                    pendiente.user_datos.user.email = email_nuevo
                    pendiente.user_datos.user.save()
                    try:
                        user_record = fire_auth.get_user_by_email(email_actual)
                        fire_auth.update_user(user_record.uid, email=email_nuevo)
                    except fire_auth.UserNotFoundError:
                        fire_auth.create_user(email=email_nuevo, password=pendiente.user_datos.user.password)

            serializer = ProveedorSerializer(pendiente, data=data, partial=True)
            profesiones_lista = data.get("profesion").split(",")
            if profesiones_lista:
                Profesion_Proveedor.objects.all().filter(proveedor=pendiente).delete()
                for profesion in profesiones_lista:
                    profesion_obj = Profesion.objects.filter(nombre=profesion)
                    if profesion_obj:
                        Profesion_Proveedor.objects.get_or_create(
                            proveedor=pendiente, profesion=profesion_obj.get())
            pendiente.user_datos.save()
            if not serializer.is_valid():
                return serializer.errors, 400
            serializer.save()
            return serializer.data, 200
    except Exception as e:
        return str(e), 400


def eliminar_proveedor_cascade(proveedor_id):
    """Replica de ProveedorDeleteView.delete (api/views.py:1308-1328)."""
    from django.db import transaction
    from django.shortcuts import get_object_or_404
    from api.models import Envio_Interesados, Solicitud

    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    with transaction.atomic():
        Envio_Interesados.objects.filter(solicitud__proveedor=proveedor).delete()
        solicitudes_eliminadas = Solicitud.objects.filter(proveedor=proveedor).delete()
        proveedor.delete()
    return solicitudes_eliminadas[0]


def editar_proveedor_admin(data, files):
    """Replica de ProveedorEdicion.put (api/views.py:4006-4073). Endpoint
    confirmado (grep) llamado por Admin2022, no por Provedor2022, pese al
    nombre — un admin editando el perfil de un proveedor, no autoedición."""
    proveedor = Proveedor.objects.get(id=data.get("id"))
    datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
    user = User.objects.get(id=datos_prov.user.id)

    if User.objects.filter(email=data.get("emailNuevo")).exists():
        existente = User.objects.get(email=data.get("emailNuevo"))
        if user.id != existente.id:
            return {"errorEmail": "Email ya registrado"}, 200
        user.email = existente.email
    user.email = data.get("emailNuevo")
    user.username = data.get("emailNuevo")
    user.save()

    datos_prov.nombres = data.get("nombres")
    datos_prov.apellidos = data.get("apellidos")
    datos_prov.ciudad = data.get("ciudad")
    datos_prov.cedula = data.get("cedula")
    datos_prov.genero = data.get("genero")
    datos_prov.telefono = data.get("telefono")
    datos_prov.save()

    proveedor.direccion = data.get("direccion")
    proveedor.licencia = data.get("licencia")
    proveedor.descripcion = data.get("descripcion")
    proveedor.banco = data.get("banco")
    proveedor.numero_cuenta = data.get("numero_cuenta")
    proveedor.tipo_cuenta = data.get("tipo_cuenta")

    if data.get("copiaCedula") is not None:
        proveedor.copiaCedula.delete()
        proveedor.copiaCedula = data.get("copiaCedula")
    if data.get("copiaLicencia") is not None:
        proveedor.copiaLicencia.delete()
        proveedor.copiaLicencia = data.get("copiaLicencia")
    for doc in files.getlist("filesDocuments"):
        documento_creado = Document.objects.create(descripcion="Documento", documento=doc)
        proveedor.document.add(documento_creado)

    stringProfesiones = ",".join(
        p.profesion.nombre for p in Profesion_Proveedor.objects.all().filter(proveedor__id=proveedor.id))
    proveedor.profesion = stringProfesiones
    proveedor.save()
    return {"sucess": "Exito"}, 200


def listar_documentos_pendientes():
    return PendienteDocuments.objects.all()


def eliminar_documento_pendiente_por_id(doc_id):
    PendienteDocuments.objects.get(id=doc_id).delete()


def listar_documentos_proveedores():
    return Document.objects.all()


def eliminar_documento_proveedor_por_id(doc_id):
    Document.objects.get(id=doc_id).delete()


def obtener_grupo_por_nombre(nombre):
    return Group.objects.get(name=nombre)


def crear_grupo_con_permisos(nombre, permisos_nombres):
    """Replica de RolesPermisos.post (api/views.py:4260-4267)."""
    grupo = Group.objects.create(name=nombre)
    for permiso in permisos_nombres:
        grupo.permissions.add(Permission.objects.get(name=permiso))
    return grupo


def actualizar_permisos_grupo(grupo_id, permisos_enviados):
    """Replica EXACTA de RolesPermisos.put (api/views.py:4269-4291).

    Hallazgo real: la lógica de sincronización está invertida. Agrega
    correctamente los permisos nuevos que no estaban antes, pero el segundo
    bucle remueve los permisos que SÍ están en `permisos_enviados` (debería
    remover los que ya NO están, es decir los que el admin deselecciono) —
    en la práctica, marcar un permiso que el grupo ya tenía lo elimina, y
    los permisos no tocados nunca se remueven. El doc de la Fase 5 asegura
    que este panel 'ya funciona' — este bug contradice esa afirmación. No
    se corrige acá (no es un crash, es lógica de negocio, fuera del alcance
    de esta migración de namespaces) pero queda documentado en el checklist
    para que el equipo decida si vale la pena arreglarlo por separado."""
    grupo = Group.objects.get(id=grupo_id)
    permisos_actuales = [p.name for p in grupo.permissions.all()]

    for permiso in permisos_enviados:
        if permiso not in permisos_actuales:
            grupo.permissions.add(Permission.objects.get(name=permiso))

    for permiso in permisos_actuales:
        if permiso in permisos_enviados:
            grupo.permissions.remove(Permission.objects.get(name=permiso))

    return grupo


def eliminar_grupo(grupo_id):
    Group.objects.get(id=grupo_id).delete()


def listar_permisos_queryset():
    return Permission.objects.all()


def listar_grupos_queryset():
    return Group.objects.all()


# ---------------------------------------------------------------------------
# Cleanup post-Fase-5 — cierre de los endpoints del checklist maestro que
# quedaron en `no-empezado` (ninguna Fase 3/4/5 los cubría explícitamente en
# su tabla, pese a estar inventariados desde la Fase 0). Bloque 1: auth /
# social / password / versionamiento.
# ---------------------------------------------------------------------------

def crear_cuenta_registro(data, files):
    """Replica exacta de Registro.create (api/views.py:713-851), el viewset
    DRF registrado bajo `registro/`. Endpoint multi-rol confirmado: lo
    invocan ViveFacil_Solicitante2022 (alta real de Solicitante) y
    ViveFacil_Admin2022 (`pendientes.component.ts`, alta manual). Provedor2022
    define el mismo wrapper (`postRegistro`) pero ningún componente lo llama
    — su alta real no pasa por acá (grep confirmado, cero llamadores).

    `data`/`files` son `request.POST`/`request.FILES` (QueryDict), igual que
    el original. Devuelve el dict de respuesta tal cual — status siempre 200
    (el original nunca seteaba un status distinto, los errores van en el
    body como {'success': False, 'error': ...})."""
    import threading as _threading
    from django.contrib.auth.models import Group as _Group, User as _User
    from django.db import transaction
    from django.db.models import Q as _Q
    from rest_framework.authtoken.models import Token as _Token

    from api.models import (
        Banco, Cuenta, Document as _Document, Profesion as _Profesion,
        Profesion_Proveedor as _Profesion_Proveedor, Tipo_Cuenta,
    )

    out = {}
    try:
        with transaction.atomic():
            user_email = data.get('email')
            user_password = data.get('password')
            if _User.objects.filter(_Q(username=user_email) | _Q(email=user_email)).exists():
                raise Exception("Usuario ya existente")
            usuario = _User.objects.create_user(
                email=user_email, username=user_email, password=user_password,
            )
            tipo_user = data.get('tipo')
            nombre_user = data.get('nombres')
            apellido_user = data.get('apellidos')

            dato, creado = Datos.objects.get_or_create(
                user=usuario, tipo=_Group.objects.get(name=tipo_user),
                nombres=nombre_user, apellidos=apellido_user,
                telefono=data.get('telefono'), genero=data.get('genero'),
                ciudad=data.get('ciudad'), cedula=data.get('cedula'),
                foto=files.get('foto'),
            )
            if not creado:
                raise Exception("Esta persona ya existe en Datos")

            if tipo_user == 'Solicitante':
                Solicitante.objects.create(user_datos=dato, bool_registro_completo=True)
                _Group.objects.get(name='Solicitante').user_set.add(usuario)

                from api.views import FormatEmail
                format_email = FormatEmail()
                _threading.Thread(
                    target=format_email.send_email,
                    args=([user_email], 'Bienvenido a Vive Fácil', 'emails/welcome.html', {"username": nombre_user}),
                ).start()

            elif tipo_user == 'Proveedor':
                proveedor_user, created = Proveedor.objects.get_or_create(
                    user_datos=dato, ano_profesion=0, profesion=data.get('profesion'),
                )
                if not created:
                    raise Exception("No se pudo crear el perfil de proveedor")

                for profesion in data.get('profesion').split(','):
                    profesion_obj = _Profesion.objects.get(nombre=profesion)
                    _Profesion_Proveedor.objects.create(
                        proveedor=proveedor_user, profesion=profesion_obj,
                        ano_experiencia=data.get('ano_experiencia'),
                    )

                banco_user = Banco.objects.get_or_create(nombre=data.get('banco'))[0]
                tipo_cuenta_user = Tipo_Cuenta.objects.get_or_create(nombre=data.get('tipo_cuenta'))[0]
                Cuenta.objects.get_or_create(
                    banco=banco_user, tipo_cuenta=tipo_cuenta_user,
                    proveedor=proveedor_user, numero_cuenta=data.get('numero_cuenta'),
                )

                proveedor_user.banco = data.get('banco')
                proveedor_user.numero_cuenta = data.get('numero_cuenta')
                proveedor_user.tipo_cuenta = data.get('tipo_cuenta')
                proveedor_user.descripcion = data.get('descripcion')
                proveedor_user.ano_profesion = data.get('ano_experiencia')
                proveedor_user.licencia = data.get('licencia')
                proveedor_user.direccion = data.get('direccion')

                if 'filesDocuments' in data:
                    doc = _Document.objects.create(documento=data.get('filesDocuments')[7:])
                    proveedor_user.document.set([doc])
                if 'foto' in data:
                    proveedor_user.user_datos.foto = data.get('foto')[7:]
                if 'copiaCedula' in data:
                    proveedor_user.copiaCedula = data.get('copiaCedula')[7:]
                if 'copiaLicencia' in data:
                    proveedor_user.copiaLicencia = data.get('copiaLicencia')[7:]

                proveedor_user.save()
                proveedor_user.user_datos.save()

                asunto = "Solicitud Aceptada"
                from api.views import FormatEmail
                format_email = FormatEmail()
                _threading.Thread(
                    target=format_email.send_email,
                    args=([user_email], asunto, 'emails/formularioAceptado.html',
                          {"username": nombre_user + ' ' + apellido_user, "user": user_email, "password": user_password}),
                ).start()

            try:
                from firebase_admin import auth as fire_auth
                user_record = fire_auth.get_user_by_email(user_email)
                fire_auth.delete_user(user_record.uid)
            except Exception:
                pass

            out['success'] = True
            out['email'] = dato.user.email
            out['username'] = dato.user.username
            out['token'] = _Token.objects.get(user=dato.user).key
            return out
    except Exception as e:
        out['success'] = False
        out['error'] = f"Hubo un error: {e}"
        return out


def registrar_desde_redes(user, data, files):
    """Replica exacta de RegistroFromRedes.post (api/views.py:682-710).

    Sin evidencia de llamador real en ninguno de los 4 frontends (grep
    fresco, cero resultados incluso a nivel de definición de wrapper en los
    `python-anywhere.service.ts`) — se migra igual por consistencia de
    namespace, mismo criterio que Register_Proveedor en la Fase 4."""
    from django.contrib.auth.models import Group as _Group, User as _User

    usuario = _User.objects.get(email=user)
    if not usuario:
        return None, 400
    nombre_user = data.get('nombres')
    apellido_user = data.get('apellidos')
    telefono_user = data.get('telefono')
    ciudad_user = data.get('ciudad')
    cedula_user = data.get('cedula')
    foto_user = files.get('foto')
    usuario.username = user
    usuario.set_password(data.get('password'))
    usuario.save()
    try:
        dato, creado = Datos.objects.get_or_create(
            user=usuario, tipo=_Group.objects.get(name='Solicitante'),
            nombres=nombre_user, apellidos=apellido_user, telefono=telefono_user,
            foto=foto_user, ciudad=ciudad_user, cedula=cedula_user,
        )
        if creado:
            Solicitante.objects.create(user_datos=dato, bool_registro_completo=True)
            return {}, 200
        return None, 400
    except Exception:
        return None, 400


def obtener_solicitante_por_email(email):
    """Replica de SolicitanteUser.get (api/views.py:1639-1645). Endpoint
    multi-rol confirmado: Solicitante2022 (login/registro, perfil propio) y
    Admin2022 (`pendientes.component.ts`, búsqueda de un solicitante por
    correo) — no estaba tageado como tal, se resuelve acá con el mismo
    mecanismo de doble-registro que el resto de esta migración."""
    return Solicitante.objects.filter(user_datos__user__email=email)


def obtener_solicitante_por_user_datos_id(user_datos_id):
    """Replica de SolicitanteByUserDatos.get (api/views.py:1648-1654).
    Confirmado uso exclusivo de Provedor2022 (feature de chat)."""
    return Solicitante.objects.filter(user_datos__id=user_datos_id)


def reactivar_cuenta_proveedor(access_security, password):
    """Replica exacta de ChangePassword.post (api/views.py:1983-2005), Fase
    de reactivación de cuenta vía `security_access` (el mismo UUID que
    genera `authenticate_login` cuando un Proveedor está inactivo). Sin
    evidencia de llamador real en ningún frontend.

    Bug real preexistente, NO corregido (requiere decisión de producto, no
    es un crash evidente sin más contexto): `Proveedor.objects.get(user_datos=
    persona.nombres)` compara un FK contra un string (el nombre de pila),
    nunca contra el objeto `Datos` real — en la práctica esto no matchea
    casi nunca (`Proveedor.DoesNotExist` real), a menos que exista un
    Proveedor cuyo `user_datos_id` coincida numéricamente con la cadena de
    texto del nombre (no puede pasar, `user_datos` es un FK numérico). Se
    preserva tal cual — mismo criterio que otros bugs de este bloque."""
    persona = Datos.objects.get(security_access=access_security)
    proveedor = Proveedor.objects.get(user_datos=persona.nombres)
    persona.user.set_password(password)
    persona.user.save()
    proveedor.estado = True
    proveedor.save()
    import uuid as _uuid
    persona.security_access = _uuid.uuid4()
    persona.save()
    token, _ = Token.objects.get_or_create(user=persona.user)
    return {"token": token.key, "username": persona.user.username}


def obtener_datos_por_user_id(user_id):
    """Replica de Datos_Users.get (api/views.py:2221-2227). Endpoint
    multi-rol confirmado: Solicitante2022 y Provedor2022 lo usan igual
    (feature de chat, para mostrar datos básicos de la contraparte)."""
    return Datos.objects.all().filter(user__id=user_id)


def completar_datos_usuario(username, data):
    """Replica exacta de Complete_Data_User.put (api/views.py:2230-2252).
    Sin evidencia de llamador real en ningún frontend — opera sobre `Datos`
    genérico (cedula/ciudad), sin indicio de a qué rol pertenece; se
    registra bajo ambos namespaces (solicitante/proveedor) por consistencia,
    mismo criterio que `actualizar_datos_usuario` (Fase 4)."""
    try:
        dato = Datos.objects.get(user__username=username)
    except Exception:
        return {"success": False, "error": "No se encontró el usuario"}
    try:
        dato.cedula = data.get('cedula')
        dato.ciudad = data.get('ciudad')
        dato.save()
        return {"success": True, "msg": "Se guardaron los cambios"}
    except Exception:
        return {"success": False, "error": "No se pudo actualizar los datos"}


def recuperar_password_existe(user_email):
    """Replica exacta de RecuperarPassword.get (api/views.py:565-575).
    Confirmado real solo en Solicitante2022 — Provedor2022 define el mismo
    wrapper pero su página de recuperación real usa Firebase directo
    (`UserService.sendPasswordResetEmail`), grep confirmado, cero llamadas
    reales a este endpoint desde ningún componente de Provedor2022."""
    usuario = User.objects.filter(email=user_email)
    if usuario.count() > 0:
        user_dato = Datos.objects.get(user=usuario.first())
        if user_dato is not None:
            return True
    return False


def validar_codigo_recuperacion(email, codigo):
    """Replica exacta de ValidarCodigo.get (api/views.py:595-606). Mismo
    alcance real que recuperar_password_existe (solo Solicitante2022)."""
    from api.models import Codigos

    usuario = User.objects.filter(email=email)
    if usuario.count() > 0:
        user_dato = Datos.objects.get(user=usuario.first())
        if user_dato is not None:
            return Codigos.objects.filter(user_datos=user_dato, codigo=codigo, estado=True).count() > 0
    return False


def cambiar_password_con_codigo(email, password, codigo):
    """Replica exacta de CambioPasswordCodigo.get (api/views.py:609-627).

    Sin evidencia de llamador real en NINGÚN frontend (ni siquiera
    Solicitante2022, que sí usa recuperar_password_existe/validar_codigo —
    el flujo real de cambio de contraseña pasa por otro camino, no
    confirmado desde acá). Se migra igual por consistencia, junto a sus dos
    vecinas del mismo flujo."""
    from api.models import Codigos

    usuario = User.objects.filter(email=email)
    if usuario.count() > 0:
        user_dato = Datos.objects.get(user=usuario.first())
        if user_dato is not None:
            codigos = Codigos.objects.filter(user_datos=user_dato, codigo=codigo, estado=True)
            if codigos.count() > 0:
                codigo_first = codigos.first()
                codigo_first.estado = False
                codigo_first.save()
                user = usuario.first()
                user.set_password(password)
                user.save()
                return True
    return False


def obtener_admin_por_email(email):
    """Replica de AdminUser.get (api/views.py:2539-2546). Definido en el
    service de Admin2022 (`obtener_admin_user`) pero sin ningún llamador
    real (grep sobre componentes, cero resultados) — mismo hallazgo que
    `AdminUserPass` de abajo: el login real de Admin2022 pasa por Firebase
    directo, no por este mecanismo (ver Fase 5, Bloque 4)."""
    from api.serializers import AdministradorSerializer

    user = User.objects.get(email=email)
    user_datos = Datos.objects.get(user=user)
    admin = Administrador.objects.get(user_datos=user_datos)
    return AdministradorSerializer(admin).data


def autenticar_admin_user_pass(username, password, request):
    """Replica exacta de AdminUserPass.post (api/views.py:2549-2570 aprox.).
    Sin llamador real (ver obtener_admin_por_email) — es un segundo
    mecanismo de login de administrador, distinto del extraído en
    `authenticate_login` (Fase 5, Bloque 1: usa `AuthenticationForm` +
    `django.contrib.auth.login` directo en vez de la función genérica). Se
    preserva como una implementación separada, no se consolida con
    `authenticate_login` — fusionar dos rutas de login sin evidencia de uso
    real sería inventar comportamiento, no migrar el existente."""
    from django.contrib.auth import authenticate as authenticate_django
    from django.contrib.auth import login as do_login
    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm(data={"username": username, "password": password})
    if not form.is_valid():
        return None
    user = authenticate_django(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    if user is None:
        return None
    do_login(request, user)
    usuario = Datos.objects.get(user=user)
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key, "username": user.username, "tipo": usuario.tipo.name}


def obtener_proveedor_por_pk(pk):
    """Replica de Get_Proveedor.get (api/views.py:1330-1336). Sin evidencia
    de llamador real en ningún frontend ni indicio de a qué rol pertenece
    — se registra bajo `web/` (lectura pública de un perfil de proveedor
    por id), mismo criterio que otros endpoints de solo-lectura sin dueño
    claro de esta migración."""
    from api.serializers import ProveedorSerializer

    proveedor = Proveedor.objects.get(user_datos__id=pk)
    return ProveedorSerializer(proveedor).data


def obtener_proveedor_por_correo(correo):
    """Replica de Get_ProveedorByUser.get (api/views.py:1339-1345).
    Confirmado real: Provedor2022 lo usa en el login (`getProveedorByCorreo`,
    login.page.ts) — se llama antes de tener token, por eso queda público
    (IsPublic) en el namespace nuevo, igual que antes."""
    from api.serializers import ProveedorSerializer

    proveedor = Proveedor.objects.get(user_datos__user__username=correo)
    return ProveedorSerializer(proveedor).data


def obtener_puntos(email):
    """Replica exacta de Puntos.get (api/views.py:2824-2835). Confirmado
    real, solo Solicitante2022 (perfil/promociones, siempre con sesión
    activa) — se endurece a IsSolicitante en el namespace nuevo."""
    try:
        usuario = Datos.objects.get(user__email=email)
        return {"valid": "OK", "puntos": usuario.puntos}
    except Exception:
        return {"valid": "error", "puntos": 0}


def actualizar_caducidad_proveedor(pk, data):
    """Replica exacta de ActualizarCaducidad.put (api/views.py:2856-2882).
    Confirmado real, exclusivo de Admin2022 (`proveedores.component.ts`).

    Nota de implementación preservada tal cual: el `pk` de la URL no se usa
    — el id real del proveedor a actualizar viene de `data['id']` en el
    body. No es un bug de crash (la vista funciona), solo una firma rara;
    no se toca, mismo criterio que otros hallazgos "no es crash, no se
    corrige" de este checklist. También preserva el efecto secundario
    masivo: cada llamada además desactiva y notifica por email a TODOS los
    proveedores con `fecha_caducidad` vencida, no solo al que se está
    actualizando — comportamiento preexistente, documentado, no alcance de
    esta migración de namespace."""
    from datetime import date, datetime as _datetime

    from api.views import FormatEmail

    proveedor = Proveedor.objects.get(id=data.get('id'))
    numero = data.get('input')
    nueva_fecha = _datetime.strptime(numero, '%Y-%m-%d').date()
    proveedor.fecha_caducidad = nueva_fecha
    proveedor.estado = True
    proveedor.save()
    datos = proveedor.user_datos
    datos.estado = True
    datos.save()
    format_email = FormatEmail()
    threading.Thread(target=format_email.send_email(
        [proveedor.user_datos.user.username], "Cambio de fecha de contrato",
        'emails/enviarAlerta.html',
        {"username": proveedor.user_datos.user.username,
         "contenido": "Tu fecha de contrato a cambiado, tu contrato expira el " + numero}))

    for e in Proveedor.objects.all().order_by('-id').filter(fecha_caducidad__lt=date.today()):
        if e.estado != False:
            thread = threading.Thread(target=format_email.send_email(
                [e.user_datos.user.username], "Cuenta caducada", 'emails/enviarAlerta.html',
                {"username": e.user_datos.user.username,
                 "contenido": "Tu cuenta ha caducado, si deseas extender tu contrato contactanos por nuestros canales oficiales."}))
        e.estado = False
        e.save()
        datos = e.user_datos
        datos.estado = False
        datos.save()
    return proveedor.fecha_caducidad


def registrar_proveedor_manual(data, files):
    """Replica exacta de ProveedorRegistro.post (api/views.py:2662-2746).
    Sin evidencia de llamador real en ningún frontend — es un segundo
    mecanismo de alta de proveedor distinto de `registrar_proveedor`
    (Fase 4, `Register_Proveedor`) y del router `registro/`
    (`crear_cuenta_registro` de arriba). Se preserva como implementación
    separada, no se consolida — mismo criterio que `autenticar_admin_user_pass`."""
    import os as _os

    from django.core.files import File
    from django.contrib.auth.models import Group as _Group, User as _User

    from api.models import Profesion as _Profesion, Profesion_Proveedor as _Profesion_Proveedor, Proveedor_Pendiente, Document as _Document

    passw = _User.objects.make_random_password()
    grupo_proveedor = _Group.objects.get(name='Proveedor')
    out = {}
    try:
        usuario = _User.objects.create_user(email=data.get('email'), username=data.get('email'), password=passw)
        grupo_proveedor.user_set.add(usuario)
    except Exception:
        out['error'] = "Correo ya empleado"
        return out

    nombre_usuario = data.get('nombres')
    apellidos_usuario = data.get('apellidos')
    ciudad_usuario = data.get('ciudad')
    cedula_usuario = data.get('cedula')
    telefono_usuario = data.get('telefono')
    genero_usuario = data.get('genero')
    foto_user = files.get('foto')
    out.update({
        "nombre": nombre_usuario, "apellido": apellidos_usuario, "telefono": telefono_usuario,
        "ciudad": ciudad_usuario, "cedula": cedula_usuario, "genero": genero_usuario,
        "email": data.get('email'), "password": passw,
    })

    try:
        dato_creado = Datos.objects.create(
            user=usuario, tipo=_Group.objects.get(name='Proveedor'), nombres=nombre_usuario,
            apellidos=apellidos_usuario, telefono=telefono_usuario, genero=genero_usuario,
            foto=foto_user, ciudad=ciudad_usuario, cedula=cedula_usuario,
        )
    except Exception:
        out['error'] = "Error al almacenar Datos"
        return out

    pendiente = Proveedor_Pendiente.objects.get(id=data.get('id'))
    uploaded_cedula = pendiente.copiaCedula
    uploaded_licencia = pendiente.copiaLicencia
    uploaded_documents = pendiente.documentsPendientes
    try:
        proveedor_creado = Proveedor.objects.create(
            user_datos=dato_creado, descripcion=data.get('descripcion'), profesion=data.get('profesion'),
            direccion=data.get('direccion'), licencia=data.get('licencia'),
            ano_profesion=data.get('anio_experiencia'), banco=data.get('banco'),
            numero_cuenta=data.get('numero_cuenta'), tipo_cuenta=data.get('tipo_cuenta'),
        )
        if uploaded_cedula is not None:
            proveedor_creado.copiaCedula = File(uploaded_cedula, _os.path.basename(uploaded_cedula.name))
        if uploaded_licencia is not None:
            proveedor_creado.copiaLicencia = File(uploaded_licencia, _os.path.basename(uploaded_licencia.name))
        proveedor_creado.save()
    except Exception:
        out['error'] = "Error al crear Proveedor"
        return out

    for documento in uploaded_documents.all():
        documento_creado = _Document.objects.create(
            descripcion=data.get('descripcionDoc'),
            documento=File(documento.document, _os.path.basename(documento.document.name)),
        )
        proveedor_creado.document.add(documento_creado)

    proveedor_creado.save()
    profesion_obj = _Profesion.objects.get(nombre=data.get('profesion'))
    _Profesion_Proveedor.objects.create(
        proveedor=proveedor_creado, profesion=profesion_obj, ano_experiencia=data.get('anio_experiencia'))
    return out


def actualizar_caducidad_masiva_proveedores():
    """Replica exacta de ActualizarCaducidadProveedoresRequest.get
    (api/views.py:2929-2948). Sin evidencia de llamador real en ningún
    frontend — probablemente disparado manualmente o por un cron externo a
    este repo (PythonAnywhere), imposible de confirmar desde acá.

    DELIBERADAMENTE se preserva sin permiso reforzado (`IsPublic`, no
    `IsAdministrador`) al namespacearlo bajo `admin/`: si existe un script
    externo que lo golpea sin autenticación, endurecerlo lo rompería en
    silencio sin manera de detectarlo desde el repo. Ver
    docs/refactor/CHECKLIST-inventario-endpoints.md."""
    from django.utils import timezone

    from api.views import FormatEmail

    resultados = []
    format_email = FormatEmail()
    today = timezone.now()
    proveedores_caducados = Proveedor.objects.all().order_by('-id').filter(fecha_caducidad__lt=today, estado=True)
    if not proveedores_caducados:
        return {"error": ["No hay proveedores caducados"]}, 400
    for e in proveedores_caducados:
        if e.estado != False:
            thread = threading.Thread(target=format_email.send_email(
                [e.user_datos.user.username], "Cuenta caducada", 'emails/enviarAlerta.html',
                {"username": e.user_datos.user.username,
                 "contenido": "Tu cuenta ha caducado, si deseas extender tu contrato contactanos por nuestros canales oficiales."}))
            thread.start()
        e.estado = False
        e.save()
        datos = e.user_datos
        datos.estado = False
        datos.save()
        resultados.append("Proveedor " + e.user_datos.user.username + " actualizado, fecha: " + str(e.fecha_caducidad))
    return {"success": resultados}, 200


def listar_datos_queryset():
    """Réplica de DatosUsers.get (api/views.py:1364-1369). Sin evidencia de
    llamador real en ningún frontend — se migra igual por consistencia."""
    return Datos.objects.all().order_by('-id')


def eliminar_dato_por_id(dato_id):
    """Réplica de DatosUsers.delete (api/views.py:1371-1382)."""
    try:
        Datos.objects.get(id=dato_id).delete()
        return {'sucess': True, 'mensaje': 'Eliminacion del Objeto Dato realizado exitosamente.'}
    except Exception:
        return {'sucess': False, 'mensaje': 'Ha ocurrido un error al eliminar el Objeto Dato.'}


def listar_usuarios_queryset():
    """Réplica de Usuarios.get (api/views.py:1385-1390). Sin evidencia de
    llamador real en ningún frontend."""
    return User.objects.all().order_by('-id')


def eliminar_usuario_por_id(user_id):
    """Réplica de Usuarios.delete (api/views.py:1392-1403)."""
    try:
        User.objects.get(id=user_id).delete()
        return {'sucess': True, 'mensaje': 'Eliminacion del Objeto User realizado exitosamente.'}
    except Exception:
        return {'sucess': False, 'mensaje': 'Ha ocurrido un error al eliminar el Objeto User.'}


def buscar_proveedores_por_nombre_queryset(nombre):
    """Réplica de Proveedores_Search_Name (api/views.py:1249-1261). Sin
    evidencia de llamador real en ningún frontend — se migra igual por
    consistencia con su análogo confirmado FiltroNombres (solicitante)."""
    return Proveedor.objects.all().filter(
        Q(user_datos__nombres__icontains=nombre) | Q(user_datos__apellidos__icontains=nombre))


def filtrar_proveedores_por_fecha_queryset(fecha_inicio, fecha_fin):
    """Réplica de Proveedores_Filter_Date (api/views.py:1264-1279). Sin
    evidencia de llamador real en ningún frontend."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Proveedor.objects.all().filter(user_datos__fecha_creacion__date__range=[fecha_in, fecha_fi])


def buscar_solicitantes_por_nombre_queryset(nombre):
    """Réplica de FiltroNombres (api/views.py:1469-1481). Confirmado real,
    exclusivo de Admin2022."""
    return Solicitante.objects.all().filter(
        Q(user_datos__nombres__icontains=nombre) | Q(user_datos__apellidos__icontains=nombre))


def filtrar_solicitantes_por_fecha_queryset(fecha_inicio, fecha_fin):
    """Réplica de SolicitantesFilter (api/views.py:1452-1466). Confirmado
    real, exclusivo de Admin2022."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Solicitante.objects.all().filter(user_datos__fecha_creacion__date__range=[fecha_in, fecha_fi])


def buscar_proveedores_pendientes_por_nombre_queryset(nombre):
    """Réplica de Pendientes_Search_Name (api/views.py:875-887). Confirmado
    real, exclusivo de Admin2022."""
    return Proveedor_Pendiente.objects.all().filter(
        Q(nombres__icontains=nombre) | Q(apellidos__icontains=nombre))


def filtrar_proveedores_pendientes_por_fecha_queryset(fecha_inicio, fecha_fin):
    """Réplica de Pendientes_FilterDate (api/views.py:890-905). Confirmado
    real, exclusivo de Admin2022."""
    fecha_in = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fi = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    return Proveedor_Pendiente.objects.all().filter(fecha_registro__date__range=[fecha_in, fecha_fi])


def actualizar_datos_proveedor_pendiente(data):
    """Réplica exacta de Update_Proveedor_Pendiente.post (api/views.py:665-729).
    Sin evidencia de llamador real en ningún frontend — se migra igual por
    consistencia."""
    if data.get('tipo_user') != 'Proveedor_Pendiente':
        return {'error': 'El usuario no corresponde a Proveedor', 'success': False}, 200
    try:
        dato = Datos.objects.get(id=data.get('user_datos'))
        proveedor = Proveedor.objects.get(id=data.get('proveedor_id'))
        proveedor_pendiente = Proveedor_Pendiente.objects.get(id=data.get('pendiente_id'))
    except Exception:
        return {'error': 'No se pudo obtener la informacion del perfil', 'success': False}, 200

    dato.nombres = data.get('nombres')
    dato.apellidos = data.get('apellidos')
    dato.telefono = data.get('telefono')
    dato.cedula = data.get('cedula')
    dato.save()

    proveedor_pendiente.banco = data.get('banco')
    proveedor_pendiente.numero_cuenta = data.get('numero_cuenta')
    proveedor_pendiente.tipo_cuenta = data.get('tipo_cuenta')
    proveedor_pendiente.email = data.get('email')
    proveedor_pendiente.profesion = data.get('profesion')
    proveedor_pendiente.ano_experiencia = data.get('ano_experiencia')
    proveedor_pendiente.save()

    return {'success': True}, 200


def crear_proveedor_proveedor_manual(data):
    """Réplica exacta de Data_Proveedor_Proveedor.post (api/views.py:791-857).
    Confirmado real, único consumidor es Admin2022
    (`crear_proveedor_proveedor`, proveedores.component.ts:381).

    **Bug real preservado, no corregido**: al final del método el original
    asigna `proveedor_user.banco`/`numero_cuenta`/`profesion` pero nunca
    llama `.save()` — esos tres campos nunca quedan persistidos pese a que
    la respuesta reporta éxito. Además `numero_cuenta` se pisa con un valor
    hardcodeado ("0999990999999") sin importar el que mandó el admin, y
    `profesion` se hardcodea al string "si" en vez de la profesión real. No
    se corrige porque requeriría adivinar la intención original (¿guardar el
    banco/cuenta que mandó el admin? ¿ignorarlos a propósito?) — decisión de
    producto, no de arquitectura."""
    from api.models import Banco, Cuenta, Tipo_Cuenta

    if User.objects.filter(username=data.get('email')).count():
        return {'error': 'El usuario ya existe', 'success': False}

    try:
        dato, _ = Datos.objects.get_or_create(
            tipo=Group.objects.get(name="Proveedor"),
            nombres=data.get('nombres'), apellidos=data.get('apellidos'),
            telefono=data.get('telefono'), genero=data.get('genero'),
            foto=data.get('foto'), ciudad=data.get('ciudad'), cedula=data.get('cedula'))
    except Exception:
        return {'error': 'No se pudo guardar los datos', 'success': False}

    try:
        proveedor, _ = Proveedor.objects.get_or_create(
            user_datos=dato, descripcion=data.get('descripcion'), ano_profesion=0)
    except Exception:
        return {'error': 'No se pudo crear el perfil de proveedor 3', 'success': False}

    try:
        banco = Banco.objects.get_or_create(nombre=data.get('banco'))
        tipo_cuenta = Tipo_Cuenta.objects.get_or_create(nombre=data.get('tipo_cuenta'))
        Cuenta.objects.get_or_create(
            banco=banco[0], tipo_cuenta=tipo_cuenta[0], proveedor=proveedor,
            numero_cuenta=data.get('numero_cuenta'))
        proveedor.banco = banco[0]
        proveedor.numero_cuenta = "0999990999999"
        proveedor.profesion = "si"
        return {'success': True}
    except Exception:
        return {'error': 'No se pudo guardar la cuenta del usuario', 'success': False}


def cerrar_sesion(request, token):
    """Réplica exacta de Logout.get (api/views.py:639-645). Sin evidencia de
    llamador real en ningún frontend (Admin2022 define el wrapper pero
    ningún componente lo invoca — su logout real es Firebase `signOut`,
    mismo patrón que LoginAdmin/AdminUser). Se migra igual por consistencia."""
    Token.objects.get(key=token).delete()
    do_logout(request)


def obtener_admin_por_username(user):
    """Réplica exacta de Get_AdminByUser.get (api/views.py:1137-1143).
    **Nombre de clase engañoso, preservado tal cual**: pese a llamarse
    "AdminByUser", en realidad consulta y devuelve un `Proveedor`, no un
    `Administrador` — bug de nombres preexistente, no de comportamiento, no
    se corrige. Confirmado real, exclusivo de Admin2022 (usa una URL
    absoluta de producción hardcodeada en vez de `API_URL`, no se toca el
    frontend por eso — ver checklist)."""
    return Proveedor.objects.get(user_datos__user__username=user)
