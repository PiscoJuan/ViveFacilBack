from django.contrib import admin
from content.models import Insignia, Suggestion, Publicidad
from catalog.models import Categoria, Servicio, Profesion, Profesion_Proveedor
from payments.models import Banco, Cuenta, PagoEfectivo, PagoSolicitud, PagoTarjeta, Plan, PlanProveedor, Tarjeta, Tipo_Cuenta
from promotions.models import Cupon, Cupon_Aplicado, CuponCategoria, Promocion, PromocionCategoria
from notifications.models import Notificacion
from solicitudes.models import Envio_Interesados, Solicitud, Tipo_Pago, Ubicacion
from accounts.models import Administrador, Codigos, Datos, Document, Proveedor, Proveedor_Pendiente, Solicitante

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Insignia)
admin.site.register(Suggestion)
admin.site.register(Servicio)
admin.site.register(Profesion)
admin.site.register(Profesion_Proveedor)
admin.site.register(Proveedor)
admin.site.register(Datos)
admin.site.register(Solicitud)
admin.site.register(Ubicacion)
admin.site.register(Tipo_Pago)
admin.site.register(Solicitante)
admin.site.register(Envio_Interesados)
admin.site.register(Document)
admin.site.register(Banco)
admin.site.register(Tipo_Cuenta)
admin.site.register(Cupon_Aplicado)
admin.site.register(Cuenta)
admin.site.register(Proveedor_Pendiente)
admin.site.register(Administrador)
admin.site.register(Notificacion)
admin.site.register(Tarjeta)
admin.site.register(Promocion)
admin.site.register(PromocionCategoria)
admin.site.register(Codigos)
admin.site.register(Cupon)
admin.site.register(CuponCategoria)
admin.site.register(PagoTarjeta)
admin.site.register(PagoEfectivo)
admin.site.register(PagoSolicitud)
admin.site.register(Plan)
admin.site.register(Publicidad)
admin.site.register(PlanProveedor)