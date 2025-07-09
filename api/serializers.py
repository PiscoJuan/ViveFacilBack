from rest_framework import serializers
from api.models import *
from django.contrib.auth.models import User, Group, Permission
from rest_framework.fields import IntegerField
from fcm_django.models import FCMDevice


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ('registration_id', 'active', 'user', 'date_created')


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


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'foto', 'foto2', 'estado']


class CuponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cupon
        fields = ['id', 'codigo', 'titulo', 'descripcion', 'porcentaje', 'participantes','fecha_creacion',
                  'fecha_iniciacion', 'fecha_expiracion', 'estado', 'puntos', 'foto','tipo_categoria', 'cantidad']
        


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
    servicio = ServicioSerializer(many=True)

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

    class Meta:
        model = Proveedor
        fields = ['id', 'user_datos', 'direccion', 'copiaCedula', 'licencia', 'copiaLicencia', 'rating', 'servicios', 'descripcion',
                  'profesion', 'ano_profesion', 'document', 'plan_proveedor', 'estado', 'banco', 'numero_cuenta', 'tipo_cuenta', 'fecha_caducidad']


class Profesion_ProveedorSerializer(serializers.ModelSerializer):
    profesion = ProfesionSerializer()
    print("PROFESION")
    print(profesion)
    proveedor = ProveedorSerializer()
    print("PROVEEDOR")
    print(proveedor)

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

    class Meta:
        model = Solicitante
        fields = ['id', 'user_datos', 'bool_registro_completo', 'estado']


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
                  'servicio', 'tipo_pago', 'proveedor', 'adjudicar', 'pagada', 'estado', 'termino', 'rating', 'descripcion_rating','descuento']


class Envio_InteresadosSerializer(serializers.ModelSerializer):
    solicitud = SolicitudSerializer(read_only=True)
    proveedor = ProveedorSerializer(read_only=True)

    class Meta:
        model = Envio_Interesados
        fields = ['interesado', 'oferta', 'solicitud', 'proveedor']

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
        fields = ['id', 'fecha_creacion', 'cvv', 'estado', 'titular',
                  'fecha_vencimiento', 'numero', 'brand', 'code', 'solicitante', 'token', 'tipo']


class NotificacionSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notificacion
        fields = [
            'id','user', 'nombre', 'titulo', 'descripcion', 'tipo_proveedores', 
            'frecuencia', 'ruta', 'fecha_creacion', 'fecha_iniciacion', 
            'fecha_expiracion', 'hora', 'estado','imagen'
        ]



class PromocionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promocion
        fields = ['id', 'codigo', 'titulo', 'descripcion', 'porcentaje', 'fecha_creacion', 'fecha_iniciacion',
                  'fecha_expiracion', 'estado', 'participantes', 'foto', 'tipo_categoria', 'cantidad']


class PromocionCategoriaSerializer(serializers.ModelSerializer):
    promocion = PromocionSerializer()
    categoria = CategoriaSerializer()

    class Meta:
        model = PromocionCategoria
        fields = ['id', 'promocion', 'categoria', 'fecha_creacion', 'estado']


class PagoTarjetaSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    tarjeta = TarjetaSerializer()
    promocion = PromocionSerializer()
    solicitud = SolicitudSerializer()

    class Meta:
        model = PagoTarjeta
        fields = ['id', 'user', 'concepto', 'promocion', 'tarjeta', 'valor', 'descripcion', 'carrier_id', 'carrier_code', 'impuesto', 'referencia', 'fecha_creacion',
                  'estado', 'pago_proveedor', 'cargo_paymentez', 'cargo_banco', 'cargo_sistema', 'proveedor', 'servicio', 'usuario', 'prov_correo', 'prov_telefono', 'solicitud']


class PagoEfectivoSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    promocion = PromocionSerializer()
    solicitud = SolicitudSerializer()

    class Meta:
        model = PagoEfectivo
        fields = ['id', 'user', 'concepto', 'promocion', 'valor', 'descripcion', 'referencia', 'fecha_creacion',
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
    class Meta:
        model = NotificacionMasiva
        fields = [
            'id', 'nombre', 'titulo', 'descripcion', 'tipo_proveedores', 
            'frecuencia', 'ruta', 'fecha_creacion', 'fecha_iniciacion', 
            'fecha_expiracion', 'hora', 'estado','imagen'
        ]


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
        fields = ['id', 'nombre', 'porcentaje', 'titulo']
