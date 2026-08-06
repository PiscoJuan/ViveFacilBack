from rest_framework import serializers
from content.models import Cargo, Insignia, Medalla, Politicas, Publicidad, Suggestion, clientexmedalla
from catalog.models import Categoria, Ciudad, Ciudad_Disponible, Profesion, Profesion_Proveedor, Servicio, SolicitudProfesion
from payments.models import Banco, Cuenta, PagoEfectivo, PagoSolicitud, PagoTarjeta, Plan, PlanProveedor, Tarjeta, Tipo_Cuenta
from promotions.models import Cupon, Cupon_Aplicado, CuponCategoria
from notifications.models import Notificacion, NotificacionMasiva
from solicitudes.models import Envio_Interesados, Solicitud, Tipo_Pago, Ubicacion
from accounts.models import Administrador, Codigos, Datos, Document, Invitacion, MovimientoPuntos, PendienteDocuments, Proveedor, Proveedor_Pendiente, Solicitante
from pagos.serializers import TransaccionPaymentezAdminSerializer
from django.contrib.auth.models import User, Group, Permission
from rest_framework.fields import IntegerField
from fcm_django.models import FCMDevice


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ('registration_id', 'active', 'user', 'date_created')


class MovimientoPuntosSerializer(serializers.ModelSerializer):
    usuario_email = serializers.CharField(source='usuario.user.email', read_only=True, default='')
    usuario_nombre = serializers.SerializerMethodField()
    motivo_display = serializers.CharField(source='get_motivo_display', read_only=True)
    referencia_display = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoPuntos
        fields = ['id', 'usuario_email', 'usuario_nombre', 'monto', 'motivo',
                  'motivo_display', 'saldo_resultante', 'referencia', 'referencia_display', 'fecha']

    def get_usuario_nombre(self, obj):
        d = obj.usuario
        if not d:
            return ''
        return ((d.nombres or '') + ' ' + (d.apellidos or '')).strip()

    def get_referencia_display(self, obj):
        # ponytail: solo resuelve medalla y cupón; otros motivos usan referencia tal cual
        if not obj.referencia:
            return '-'
        if obj.motivo == 'medalla':
            try:
                medalla = Medalla.objects.get(id=obj.referencia)
                return f"{medalla.nombre} ({medalla.puntos}pts)"
            except:
                return obj.referencia
        elif obj.motivo == 'cupon':
            try:
                cupon = Cupon.objects.get(id=obj.referencia)
                return cupon.titulo
            except:
                return obj.referencia
        return obj.referencia


class InsigniaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insignia
        fields = ['id', 'nombre', 'imagen', 'servicio', 'tipo_usuario',
                  'estado', 'pedidos', 'fecha_creacion', 'descripcion', 'tipo']

class MedallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medalla
        fields = ['id', 'nombre', 'descripcion', 'imagen',
                  'estado', 'tiempo', 'valor', 'cantidad', 'fecha_creacion']


# Los dos de abajo solo sirven para las vistas "personales", que anotan
# `fecha_obtencion` en el queryset. Los serializers base los usa el panel admin
# sobre querysets sin anotar, por eso el campo va acá y no allá.
class InsigniaPersonalSerializer(InsigniaSerializer):
    fecha_obtencion = serializers.DateTimeField(read_only=True, required=False, allow_null=True)

    class Meta(InsigniaSerializer.Meta):
        fields = InsigniaSerializer.Meta.fields + ['fecha_obtencion']


class MedallaPersonalSerializer(MedallaSerializer):
    fecha_obtencion = serializers.DateTimeField(read_only=True, required=False, allow_null=True)

    class Meta(MedallaSerializer.Meta):
        fields = MedallaSerializer.Meta.fields + ['fecha_obtencion']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'foto', 'foto2', 'estado']


class CuponSerializer(serializers.ModelSerializer):
    # Dos cosas distintas, a propósito en dos campos:
    #   `estado`   -> interruptor manual del admin (booleano del modelo)
    #   `vigencia` -> si sirve por fechas y cupos, sin mirar el interruptor
    # Un cupón puede estar habilitado y aun así expirado o agotado.
    vigencia = serializers.SerializerMethodField()
    usos = serializers.SerializerMethodField()
    # `categoria` es el id (FK) para escribir/comparar; `categoria_nombre` es
    # para mostrar en las apps sin que tengan que resolver el id ellas mismas.
    categoria_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Cupon
        fields = ['id', 'codigo', 'titulo', 'descripcion', 'porcentaje', 'participantes','fecha_creacion',
                  'fecha_iniciacion', 'fecha_expiracion', 'estado', 'puntos', 'foto', 'categoria',
                  'categoria_nombre', 'cantidad', 'vigencia', 'usos']

    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre if obj.categoria_id else None

    def get_vigencia(self, obj):
        from promotions.services import vigencia_cupon

        return vigencia_cupon(obj)

    def get_usos(self, obj):
        """canjeados / usados / pendientes / restantes. Ver
        promotions.services.estadisticas_cupon."""
        from promotions.services import estadisticas_cupon

        return estadisticas_cupon(obj)




class PublicidadSerializer(serializers.ModelSerializer):

    fecha_creacion = serializers.DateTimeField(
        read_only=True, format="%d-%m-%Y %H:%M:%S")
    fecha_expiracion = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
    fecha_inicio = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")

    class Meta:
        model = Publicidad
        fields = ['id', 'titulo', 'descripcion', 'fecha_creacion',
                  'fecha_inicio', 'fecha_expiracion', 'imagen', 'url']


class CuponCategoriaSerializer(serializers.ModelSerializer):
    cupon = CuponSerializer()
    categoria = CategoriaSerializer()

    class Meta:
        model = CuponCategoria
        fields = ['id', 'cupon', 'categoria', 'fecha_creacion', 'estado']


# Subcategorias
class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'categoria', 'estado', 'foto']


class ProfesionSerializer(serializers.ModelSerializer):
    servicio = ServicioSerializer(read_only=True)

    class Meta:
        model = Profesion
        fields = ['id', 'nombre', 'descripcion', 'foto', 'servicio', 'estado']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['name']


class GroupSerializer(serializers.ModelSerializer):

    permissions = PermissionSerializer(read_only=True, many=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name',
                  'last_name', 'password', 'groups', 'is_superuser']


class DatosSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Datos
        fields = ['id', 'user', 'tipo', 'nombres', 'apellidos', 'ciudad', 'cedula',
                  'codigo_invitacion', 'telefono', 'genero', 'foto', 'estado', 'fecha_creacion', 'puntos']


class DatosContraparteSerializer(serializers.ModelSerializer):
    """Datos de la *otra* persona en un chat (ver `DatosUsuarioSolicitanteView`
    / `DatosUsuarioProveedorView`). Cubre lo que muestra el modal de detalle
    del proveedor, que se abre tanto desde el listado de proveedores como
    desde la lista de chats.

    No usa `DatosSerializer` porque ese expone el hash de la contraseña, los
    grupos y el flag de superusuario, y este endpoint recibe un id arbitrario
    en la URL. Los datos de contacto sí van: son los mismos que
    `proveedores-por-servicio` ya entrega a cualquier solicitante autenticado.

    ponytail: se filtra por campos, no por permiso. Verificar que exista un
    chat entre los dos exigiría consultar Firebase desde el backend; si
    aparece esa necesidad, ese es el upgrade.
    """

    user = serializers.SerializerMethodField()
    correo = serializers.SerializerMethodField()
    profesion = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    descripcion = serializers.SerializerMethodField()

    class Meta:
        model = Datos
        fields = ['id', 'user', 'tipo', 'nombres', 'apellidos', 'foto', 'estado',
                  'cedula', 'telefono', 'correo', 'ciudad', 'genero', 'profesion', 'rating', 'descripcion']

    def get_user(self, obj):
        # se mantiene como objeto (no id plano) para no romper el shape que ya consumen las apps
        return {'id': obj.user_id}

    def get_correo(self, obj):
        return obj.user.email if obj.user else ''

    def get_profesion(self, obj):
        """Oficio del proveedor, para el chip de la lista de chats del
        solicitante. Vive en `Proveedor.profesion` (texto libre, separado por
        comas si tiene varios); vacío si la contraparte no es proveedor."""
        proveedor = getattr(obj, 'proveedor', None)
        return (proveedor.profesion or '') if proveedor else ''

    def get_rating(self, obj):
        """Calificación promedio, para el detalle que se abre desde la lista de
        chats. Sirve para ambos roles: `Proveedor.rating` y `Solicitante.rating`
        son la misma propiedad calculada (base bayesiana, ver accounts/models.py).
        None si la persona no tiene ninguno de los dos perfiles."""
        perfil = getattr(obj, 'proveedor', None) or getattr(obj, 'solicitante', None)
        return perfil.rating if perfil else None

    def get_descripcion(self, obj):
        """Presentación pública del proveedor; vacía si no es proveedor."""
        proveedor = getattr(obj, 'proveedor', None)
        return (proveedor.descripcion or '') if proveedor else ''


class CodigosSerializer(serializers.ModelSerializer):
    user_datos = DatosSerializer()

    class Meta:
        model = Codigos
        fields = ['id', 'user_datos', 'codigo', 'estado', 'fecha_creacion']


class Cupon_AplicadoSerializer(serializers.ModelSerializer):
    cupon = CuponSerializer()

    class Meta:
        model = Cupon_Aplicado
        fields = ['id', 'cupon', 'user', 'estado']


class CuponUsoAdminSerializer(serializers.ModelSerializer):
    """Una fila de la tabla "quién usó este cupón" del admin. No anida el cupón
    (ya se conoce, es el de la pantalla) y en cambio resuelve los datos de la
    persona, que en el modelo solo está como un username suelto."""

    usuario = serializers.SerializerMethodField()
    usado = serializers.SerializerMethodField()

    class Meta:
        model = Cupon_Aplicado
        fields = ['id', 'user', 'usuario', 'estado', 'usado', 'fecha_canje', 'fecha_uso']

    def get_usado(self, obj):
        # estado=False significa "ya se consumió en un pago".
        return not obj.estado

    def get_usuario(self, obj):
        """`Cupon_Aplicado.user` guarda el username (el correo), no un FK, así
        que hay que ir a buscar la persona. Devuelve None si el usuario ya no
        existe: el canje histórico igual se muestra."""
        datos = Datos.objects.filter(user__username=obj.user).select_related('user').first()
        if not datos:
            return None
        return {
            'nombres': datos.nombres,
            'apellidos': datos.apellidos,
            'correo': datos.user.email if datos.user else obj.user,
            'telefono': datos.telefono,
            'foto': datos.foto.url if datos.foto else None,
        }


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'descripcion', 'documento', 'estado']


class PlanSerializer(serializers.ModelSerializer):

    fecha_creacion = serializers.DateTimeField(
        read_only=True, format="%d-%m-%Y %H:%M:%S")

    class Meta:
        model = Plan
        fields = ['id', 'nombre', 'descripcion', 'imagen',
                  'precio', 'duracion', 'fecha_creacion', 'estado']


class PlanProveedorSerializer(serializers.ModelSerializer):

    fecha_inicio = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
    fecha_expiracion = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
    plan = PlanSerializer(source='planProveedor', read_only=True)

    class Meta:
        model = PlanProveedor
        fields = ['id', 'planProveedor', 'plan', 'proveedor',
                  'fecha_inicio', 'fecha_expiracion', 'estado']


class ProveedorSerializer(serializers.ModelSerializer):
    user_datos = DatosSerializer()
    document = DocumentSerializer(many=True)
    plan_proveedor = PlanProveedorSerializer(
        source='planproveedor_set', many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)  # propiedad calculada del modelo

    class Meta:
        model = Proveedor
        fields = ['id', 'user_datos', 'direccion', 'copiaCedula', 'licencia', 'copiaLicencia', 'rating', 'servicios', 'descripcion',
                  'total_resenas_dejadas', 'total_resenas_dejadas_puntos',
                  'profesion', 'ano_profesion', 'document', 'plan_proveedor', 'estado', 'banco', 'numero_cuenta', 'tipo_cuenta', 'fecha_caducidad']


class Profesion_ProveedorSerializer(serializers.ModelSerializer):
    profesion = ProfesionSerializer()
    proveedor = ProveedorSerializer()

    class Meta:
        model = Profesion_Proveedor
        fields = ['id', 'profesion', 'proveedor', 'ano_experiencia', 'estado']


class PendientesDocumentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = PendienteDocuments
        fields = ['id', 'document']


class Proveedor_PendienteSerializer(serializers.ModelSerializer):
    documentsPendientes = PendientesDocumentsSerializer(many=True)

    class Meta:
        model = Proveedor_Pendiente
        fields = ['id', 'nombres', 'apellidos', 'ciudad', 'direccion', 'genero', 'fecha_registro', 'licencia', 'copiaLicencia', 'email', 'telefono', 'cedula',
                  'copiaCedula', 'descripcion', 'estado', 'profesion', 'ano_experiencia', 'banco', 'numero_cuenta', 'tipo_cuenta', 'documentsPendientes', 'foto', 'rechazo']

class Proveedor_PendienteSerializer2(serializers.ModelSerializer):
    documentsPendientes = PendientesDocumentsSerializer(many=True)

    class Meta:
        model = Proveedor_Pendiente
        fields = ['id', 'nombres', 'apellidos', 'ciudad', 'direccion', 'genero', 'fecha_registro', 'licencia', 'copiaLicencia', 'email', 'telefono', 'cedula',
                  'copiaCedula', 'descripcion', 'estado', 'profesion', 'ano_experiencia', 'banco', 'numero_cuenta', 'tipo_cuenta', 'documentsPendientes', 'foto', 'rechazo']

class BancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banco
        fields = ['id', 'nombre']


class Tipo_CuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Cuenta
        fields = ['id', 'nombre']


class CuentaSerializer(serializers.ModelSerializer):
    proveedor = ProveedorSerializer()
    tipo_cuenta = Tipo_CuentaSerializer()
    banco = BancoSerializer()

    class Meta:
        model = Cuenta
        fields = ['id', 'numero_cuenta', 'proveedor',
                  'banco', 'tipo_cuenta', 'estado']


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = ['id', 'latitud', 'altitud',
                  'direccion', 'referencia', 'foto_ubicacion']


class Tipo_PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Pago
        fields = ['id', 'nombre', 'estado']


class SolicitanteSerializer(serializers.ModelSerializer):
    user_datos = DatosSerializer()
    rating = serializers.FloatField(read_only=True)  # propiedad calculada del modelo

    class Meta:
        model = Solicitante
        fields = ['id', 'user_datos', 'bool_registro_completo', 'estado',
                  'rating', 'total_resenas_dejadas', 'total_resenas_dejadas_puntos']


class AdministradorSerializer(serializers.ModelSerializer):
    user_datos = DatosSerializer(read_only=True)

    class Meta:
        model = Administrador
        fields = ['id', 'user_datos', 'estado']


class SolicitudSerializer(serializers.ModelSerializer):
    solicitante = SolicitanteSerializer()
    ubicacion = UbicacionSerializer()
    tipo_pago = Tipo_PagoSerializer()
    servicio = ServicioSerializer()
   # proveedor=UserSerializer()
    proveedor = ProveedorSerializer(read_only=True)

    class Meta:
        model = Solicitud
        fields = ['id', 'descripcion', 'foto_descripcion', 'fecha_creacion', 'fecha_expiracion', 'solicitante', 'ubicacion',
                  'servicio', 'tipo_pago', 'proveedor', 'adjudicar', 'pagada', 'estado', 'termino', 'rating', 'descripcion_rating',
                  'rating_solicitante', 'descripcion_rating_solicitante', 'descuento']

class SolicitudEnProcesoSerializer(SolicitudSerializer):
    estado_proceso = serializers.CharField(read_only=True)
    class Meta(SolicitudSerializer.Meta):
        fields = SolicitudSerializer.Meta.fields + ['estado_proceso']


class EnvioInteresadoAdminSerializer(serializers.ModelSerializer):
    """Candidato al que se le envió la solicitud (sin anidar 'solicitud' de
    vuelta, a diferencia de Envio_InteresadosSerializer, para no duplicar
    toda la solicitud una vez por cada proveedor candidato)."""
    proveedor = ProveedorSerializer(read_only=True)

    class Meta:
        model = Envio_Interesados
        fields = ['id', 'proveedor', 'interesado', 'oferta', 'fecha_creacion',
                  'rechazada', 'fecha_rechazo', 'motivo_rechazo']


class SolicitudAdminSerializer(SolicitudEnProcesoSerializer):
    """Vista admin de solicitudes: agrega el monto cobrado, leído desde el
    pago (tarjeta o efectivo) asociado, ya que Solicitud no lo guarda, y los
    proveedores candidatos (a quienes se les envió la solicitud) para poder
    ver a quién se le ofreció vs. quién quedó adjudicado en 'proveedor'."""
    valor = serializers.SerializerMethodField()
    candidatos = EnvioInteresadoAdminSerializer(source='envio_interesados_set', many=True, read_only=True)
    transacciones_paymentez = TransaccionPaymentezAdminSerializer(many=True, read_only=True)

    class Meta(SolicitudEnProcesoSerializer.Meta):
        fields = SolicitudEnProcesoSerializer.Meta.fields + ['valor', 'candidatos', 'transacciones_paymentez']

    def get_valor(self, obj):
        pago = obj.pagotarjeta_set.first() or obj.pagoefectivo_set.first()
        return pago.valor if pago else None

class Envio_InteresadosSerializer(serializers.ModelSerializer):
    solicitud = SolicitudSerializer(read_only=True)
    proveedor = ProveedorSerializer(read_only=True)

    class Meta:
        model = Envio_Interesados
        fields = ['interesado', 'oferta', 'solicitud', 'proveedor',
                  'rechazada', 'fecha_rechazo', 'motivo_rechazo']

    def update(self, instance, validated_data):
        instance.interesado = validated_data.get(
            'interesado', instance.interesado)
        instance.oferta = validated_data.get('oferta', instance.oferta)
        instance.save()
        return instance


class TarjetaSerializer(serializers.ModelSerializer):
    solicitante = SolicitanteSerializer()

    class Meta:
        model = Tarjeta
        # No se exponen 'cvv' ni 'numero' (PAN): datos sensibles de tarjeta.
        # Las tarjetas viven en Paymentez; esta tabla queda solo por histórico.
        fields = ['id', 'fecha_creacion', 'estado', 'titular',
                  'fecha_vencimiento', 'brand', 'code', 'solicitante', 'token', 'tipo']


class NotificacionSerializer(serializers.ModelSerializer):
    # Sin `user`: iba anidado con UserSerializer, que incluye el hash de la
    # contraseña, y ningún componente del admin lo lee. Además, al ser anidado y
    # escribible rompía cualquier PUT que trajera `user`.
    # Las profesiones se escriben en services.aplicar_profesiones, que además
    # aplica la regla de "solo si va dirigida a proveedores". Acá solo se leen,
    # para no tener dos caminos de escritura con reglas distintas.
    profesiones = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    profesiones_nombres = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        # Sin `tipo_proveedores`: la columna sigue en la tabla pero está
        # deprecada (la reemplazan dirigida_a + profesiones) y nadie la lee.
        fields = [
            'id', 'nombre', 'titulo', 'descripcion',
            'frecuencia', 'ruta', 'fecha_creacion', 'fecha_iniciacion',
            'fecha_expiracion', 'hora', 'estado', 'imagen',
            'dirigida_a', 'profesiones', 'profesiones_nombres', 'dias_semana',
            'veces_enviada', 'ultimo_envio',
        ]
        read_only_fields = ['fecha_creacion', 'veces_enviada', 'ultimo_envio']

    def get_profesiones_nombres(self, obj):
        # Sin N+1: los querysets de services traen prefetch_related.
        return [p.nombre for p in obj.profesiones.all()]



class PagoTarjetaSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    tarjeta = TarjetaSerializer()
    solicitud = SolicitudSerializer()

    class Meta:
        model = PagoTarjeta
        fields = ['id', 'user', 'concepto', 'tarjeta', 'valor', 'descripcion', 'carrier_id', 'carrier_code', 'impuesto', 'referencia', 'fecha_creacion',
                  'estado', 'pago_proveedor', 'cargo_paymentez', 'cargo_banco', 'cargo_sistema', 'proveedor', 'servicio', 'usuario', 'prov_correo', 'prov_telefono', 'solicitud']


class PagoEfectivoSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    solicitud = SolicitudSerializer()

    class Meta:
        model = PagoEfectivo
        fields = ['id', 'user', 'concepto', 'valor', 'descripcion', 'referencia', 'fecha_creacion',
                  'estado', 'proveedor', 'servicio', 'usuario', 'prov_correo', 'prov_telefono', 'user_telefono', 'solicitud']


class PagoSolicitudSerializer(serializers.ModelSerializer):
    pago_tarjeta = PagoTarjetaSerializer(required=False, allow_null=True)
    pago_efectivo = PagoEfectivoSerializer(required=False, allow_null=True)
    solicitud = SolicitudSerializer()

    class Meta:
        model = PagoSolicitud
        fields = ['id', 'pago_tarjeta', 'pago_efectivo',
                  'solicitud', 'estado', 'fecha_creacion']


class SuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suggestion
        fields = ['id', 'usuario', 'correo', 'descripcion',
                  'foto', 'estado', 'fecha_creacion']


class PoliticasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Politicas
        fields = ['identifier', 'terminos']


class CiudadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = ['id', 'nombre']


class NotificacionMasivaSerializer(serializers.ModelSerializer):
    profesiones = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    profesiones_nombres = serializers.SerializerMethodField()

    class Meta:
        model = NotificacionMasiva
        # Una masiva se envía una sola vez y no expira, así que `frecuencia`,
        # `hora`, `fecha_iniciacion`, `fecha_expiracion` y `tipo_proveedores`
        # quedan fuera: las columnas siguen en la tabla, deprecadas.
        fields = [
            'id', 'nombre', 'titulo', 'descripcion', 'ruta', 'fecha_creacion',
            'estado', 'imagen',
            'dirigida_a', 'profesiones', 'profesiones_nombres',
            'programada_para', 'enviada_en',
        ]
        # `enviada_en` la ponen el job y "enviar ahora", nunca el cliente.
        read_only_fields = ['fecha_creacion', 'enviada_en']

    def get_profesiones_nombres(self, obj):
        return [p.nombre for p in obj.profesiones.all()]


# class PagosSerializer(serializers.Serializer):

#     pagosTarjetas = PagoTarjetaSerializer(many=True)
#     pagosEfectivo = PagoEfectivoSerializer(many = True)


class SolicitudProfesionSerializer(serializers.ModelSerializer):
    proveedor = ProveedorSerializer(read_only=True)

    class Meta:
        model = SolicitudProfesion
        fields = ['id', 'proveedor', 'profesion', 'anio_experiencia',
                  'fecha_solicitud', 'documento', 'estado', 'fecha']


class CargoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cargo
        fields = ['id', 'nombre', 'porcentaje', 'titulo', 'tipo']
