from django.urls import path, re_path
#from rest_framework.urlpatterns import format_suffix_patterns
from api.views import *
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'registro',Registro)
urlpatterns = router.urls

urlpatterns += [
    path('tarjetaPaymentez/', CardsAuth.as_view()), #añade cvc de tarjeta #busca el cvc de la tarjeta segun el token #borra el cvc de la tarjeta segun el token
    path('cardAuth_delete/<str:token>', CardsAuth.as_view()),
    path('categorias/', Categorias.as_view()),
    path('insignias/', Insignias.as_view()),
    path('medallas/', Medallas.as_view()),
    path('medalla_update/<str:id>', Medallas.as_view()),
    path('insigniaspersonales/<str:id>', InsigniasPersonales.as_view()),
    path('medallaspersonales/', MedallasPersonales.as_view()),
    path('insignia_update/<str:id>', Insignias.as_view()),
    path('insignia_delete/<str:id>', Insignias.as_view()),
    path('insignias/<str:pk>', Insignia_Details.as_view()),
    path('insignia_estado/', Insignia_Details.as_view()),
    path('medalla_estado/', Medalla_Details.as_view()),
    path('insignias_proveedor/', InsigniasProveedor.as_view()),
    path('insignias_solicitantes/', InsigniaSolicitantes.as_view()),
    path('suggestions/', Suggestions.as_view()),
    path('read-suggestions/', ReadSuggestions.as_view()),
    path('unread-suggestions/', UnreadSuggestions.as_view()),
    path('suggestion/<str:pk>', Suggestions_Details.as_view()),
    path('suggestion_estado/', Suggestions_Details.as_view()),
    path('post-token/', DeviceNotification.as_view()),
    path('dispositivos-notificacion/', DeviceNotification.as_view()),  # solicitante y proveedor
    path('categoria_update/<str:id>', Categorias.as_view()),
    path('categoria_delete/<str:id>', Categorias.as_view()),
    path('servicios/', Servicios.as_view()), # app solicitante, administrador, web
    path('servicios_update/<str:id>', Servicios.as_view()),
    path('servicios_delete/<str:id>', Servicios.as_view()),
    path('servicios/<category_ID>', Service.as_view()),
    path('logout/<str:token>', Logout.as_view()),
    path('solicitud/', Solicituds.as_view()), # proveedor y solicitante
    path('cupon_aplicado/', Cupones_Aplicados.as_view()),
    path('get_cupon_aplicado/<str:user>',Get_Cupon_Aplicado.as_view()),
    #path('solicitud/<str:solicitud_ID>/<float:solicitud_Rate>', Solicituds.as_view()),
    path('solicitud/<str:solicitud_ID>', Solicituds.as_view()),
    path('solicitudID/<str:solicitud_ID>', SolicitudID.as_view()), # proveedor (cancelar)
    path('solicitudes/<str:user>', Solicitudes.as_view()),
    path('solicitudes_espera/<str:correo>', SolicitudesPending.as_view()),      # para Solicitante
    path('solicitudes_pasadas/<str:correo>', SolicitudesPast.as_view()),        # para Solicitante
    path('solicitudes_paid/<str:correo>', SolicitudesPaid.as_view()),           # para Solicitante
    path('solicitudes_no_paid/<str:correo>', SolicitudesNoPaid.as_view()),      # para Solicitante
    path('solicitudes_esperaPag/<str:correo>',SolicitudesPendingPag.as_view()), # para Solicitante
    path('solicitudes_pasadasPag/', SolicitudesPastPag.as_view()),  # Solicitante
    path('solicitudes_paidPag/<str:correo>',SolicitudesPaidPag.as_view()),      # para Solicitante
    path('solicitudes_no_paidPag/<str:correo>', SolicitudesNoPaidPag.as_view()),# para Solicitante
    path('solicitudes_enProceso/', SolicitudesEnProceso.as_view()),  # Solicitante    
    path('proveedores/', Proveedores.as_view()),
    path('proveedores/<str:id>', Proveedores.as_view()),
    # path('proveedor/<str:pk>', Proveedores_Details.as_view()),                #este endpoint es una basura.
    path('providers-search/<str:user>', Proveedores_Search_Name.as_view()),
    path('dates-providers/', Proveedores_Filter_Date.as_view()),
    path('proveedor_estado/<str:id>', Proveedores.as_view()),
    path('proveedor_delete/<str:id>', Proveedores.as_view()),
    path('dato/<str:user>', Dato.as_view()),
    path('datos/', DatosUsers.as_view()),
    path('usuarios/', Usuarios.as_view()),
    path('datoRedes/<str:user>', RegistroFromRedes.as_view()),
    path('profesiones/', Profesiones.as_view()), # web
    path('profesion/<str:pk>',ProfesionDetails.as_view()),
    path('profesiones/<str:pk>', Profesiones.as_view()),
    path('proveedor_profesiones/', Proveedor_Profesiones.as_view()), # proveedor
    path('profesion_prov/<str:pk>', Proveedor_Profesiones.as_view()),
    path('crear_profesiones_faltantes/', CrearProfesionesFaltantesView.as_view(), name='crear_profesiones_faltantes'),
    path('solicitud_servicio/<str:ID_servicio>/', Solicitud_Servicio_User.as_view()), # proveedor
    path('rest-auth/facebook/', FacebookLogin.as_view(), name='fb_login'),
    path('rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('envio/<str:solicitud_ID>', Envio.as_view()), # proveedor
    path('envio_interesados/<str:solicitud_ID>', Envio_Interesado.as_view()), # solicitante
    path('solicitante/<str:user>', SolicitanteUser.as_view()), # esto se usa para obtener el perfil y para validar el usuario cuando se registra
    path('solicitanteByUserDatosID/<str:UserDatosId>', SolicitanteByUserDatos.as_view()), #Endopint Add
    path('solicitantes/', Solicitantes.as_view()),
    path('fechas-filtro/', SolicitantesFilter.as_view()),
    path('filtro-usuario/<str:user>', FiltroNombres.as_view()),
    path('solicitante_estado/<str:id>', Solicitantes.as_view()),
    path('solicitante_delete/<str:id>', Solicitantes.as_view()),
    path('administradores/', Administradores.as_view()),
    path('admin-filtro/<str:user>', AdministradoresUser.as_view()),
    path('fechas_admin/', AdministradoresFilter.as_view()),
    path('fechas_efectivo/', EfectivosFilter.as_view()),
    path('fechas_tarjeta/', TarjetasFilter.as_view()),
    path('administrador/<str:pk>', Admin_Details.as_view()),
    path('administrador_estado/', Administradores.as_view()),
    path('administrador_delete/<str:id>', Administradores.as_view()),
    path('addsolicitud/' , AddSolicitud.as_view()), # solicitante
    path('proveedores_pendientes/', Proveedores_Pendientes.as_view()),
    path('proveedores_rechazados/', Proveedores_Rechazados.as_view()),
    path('proveedores_proveedores/', Proveedores_Proveedores.as_view()),
    path('proveedores_proveedores/<str:pk>', Proveedores_Proveedores_Details.as_view()),
    path('proveedores_proveedores/delete/<str:proveedor_id>', ProveedorDeleteView.as_view(), name='delete_proveedor'),
    path('pendientes-search/<str:user>', Pendientes_Search_Name.as_view()),
    path('pendientes-filterDate/', Pendientes_FilterDate.as_view()),
    path('proveedor_pendientes/', Proveedores_Pendientes.as_view()),
    path('proveedor_pendiente/', Proveedor_Pendiente_Admin.as_view()),
    path('proveedores_pendientes/<str:pk>', Proveedores_Pendientes_Details.as_view()),
    path('proveedores_pendientes_estado/', Proveedores_Pendientes_Estado.as_view()),
    path('proveedores_pendientes_email/<str:mail>', Proveedores_Pendientes_Email.as_view()), # web
    path('proveedores_pendientes2/<str:pk>', Proveedores_Pendientes_Details2.as_view()),
    path('proveedores_rechazados/<str:pk>', Proveedores_Rechazados_Details.as_view()),
    path('proveedores_pendientes/<str:username>/<str:desc>', Proveedores_Pendientes.as_view()),
    path('documentos_proveedor/<str:username>', Documentos_proveedor.as_view()),
    path('cuenta_proveedor/<proveedorID>', CuentaProveedor.as_view()),
    path('register_proveedor/', Register_Proveedor.as_view()),
    path('proveedor_pendiente/', Data_Proveedor_Pendiente.as_view()), # web
    path('proveedor_proveedor/', Data_Proveedor_Proveedor.as_view()),
    path('update_pendiente/', Update_Proveedor_Pendiente.as_view()),
    path('email/', Email.as_view()),
    path('login/', Login.as_view()), # proveedor y solicitante
    path('loginadmin/', LoginAdmin.as_view()), # administrador
    path('changePassword/<str:access_security>', ChangePassword.as_view()),
    path('adjudicarsolicitud/<str:solicitud_ID>', AdjudicarSolicitud.as_view()), # solicitante
    path('solicitud_adjudicada/<str:solicitud_ID>', SolicitudAdjudicada.as_view()),
    path('tarjeta/', Tarjetas.as_view()),
    path('tarjeta/<str:identifier>', TarjetaUser.as_view()),
    path('dato_usuario/<str:id>',Datos_Users.as_view()),
    path('complete_dato/<str:username>', Complete_Data_User.as_view()),
    path('proveedores_servicio/<str:servicio_id>',ProveedoresByProfesion.as_view()),
    path('sincronizar_profesion_proveedor/', SincronizarProfesionProveedorView.as_view(), name='sincronizar_profesion_proveedor'),

    path('confirmar_descuento/<str:mail>', ConfirmarDescuento.as_view()), # web
    path('revisar_descuento_unico/', RevisarDescuentoUnico.as_view()), # proveedor
    path('usar_descuento_unico/<str:mail>', UsarDescuentoUnico.as_view()),

    # ! Quitar, ya no se va a usar
    path('proveedores_interesados/<str:id_proveedor_user_datos>',
         Proveedores_Interesados.as_view()),
    path('proveedores_interesadosFecha/<str:id_proveedor_user_datos>',
         Proveedores_InteresadosFecha.as_view()),

    # Paginado
    path('proveedores_interesadosPag/<str:id_proveedor_user_datos>',
         Proveedores_Interesados_Pag.as_view()),
    path('proveedores_interesadosEfectivoPag/<str:id_proveedor_user_datos>',
         Proveedores_Interesados_Efectivo_Pag.as_view()),
    path('proveedores_interesadosTarjetaPag/<str:id_proveedor_user_datos>',
         Proveedores_Interesados_Tarjeta_Pag.as_view()),
    path('solicitudes-pagadas/<str:id>', SolicitudesPagadas.as_view()),
    path('notificaciones/', Notificaciones.as_view()),
    path('notificaciones/<str:id>', Notificaciones.as_view()),
    path('notificaciones_estado/', Notificaciones_Details.as_view()),
    path('notificaciones-envio/', Notificaciones_Details.as_view(), name='envio_notificacion'),
    path('notificacion_chat/',Notificacion_Chat.as_view()),
    path('notificacion_chat_proveedor/',Notificacion_Chat_Proveedor.as_view()),
    path('notificacion_general',Notificacion_General.as_view()),
    path('promociones/', Promociones.as_view()),
    path('promociones/<str:pk>', Promocion_Details.as_view()),
    path('promcategorias/<str:promCode>', PromocionesCategoria.as_view()),
    path('all_promcategorias/', AllPromocionesCategoria.as_view()),
    path('promocion_update/<str:id>', Promociones.as_view()),
    path('promocion_delete/<str:id>', Promociones.as_view()),
    path('promocion_estado/', Promocion_Details.as_view()),
    path('cupones/', Cupones.as_view()),
    path('all_cupones/', Cupones.as_view()),
    path('cupon_update/<str:id>', Cupones.as_view()),
    path('cupon_delete/<str:id>', Cupones.as_view()),
    path('cupones/<str:pk>', Cupon_Details.as_view()),
    path('cupon_estado/', Cupon_Details.as_view()),
    path('cupon_cant/<str:pk>', Cupon_Cant.as_view()),
    path('cupcategorias/<str:promCode>', CuponesCategoria.as_view()),
    path('all_cupcategorias/', AllCuponesCategoria.as_view()),
    path('grupos/', Grupos.as_view()),
    path('recuperarpassword/<str:user_email>', RecuperarPassword.as_view()),
    path('validarcodigo/<str:email>/<str:codigo>', ValidarCodigo.as_view()),
    path('recuperarpassword/<str:user_email>', RecuperarPassword.as_view()),
    path('cambiopasswordcodigo/<str:email>/<str:password>/<str:codigo>', CambioPasswordCodigo.as_view()),
    path('cambiocontrasenia/', CambioContrasenia.as_view()), # proveedor y solicitante
    path('pago_tarjeta/', PagosTarjeta.as_view()),
    path('pago_efectivo/', PagosEfectivo.as_view()), # solicitante
    path('pago_tarjetas/', PagosTarjetaUser.as_view()), # solicitante
    path('pago_efectivos/', PagosEfectivoUser.as_view()),
    path('pago_efectivosP/', PagosEfectivoUserP.as_view()),
    path('valor_total_efectivo/', ValorTotalEfectivo.as_view()),
    path('valor_total_tarjeta/', ValorTotalTarjeta.as_view()),
    path('valor_total_pay_tarjeta/', ValorTotalPayTarjeta.as_view()),
    path('valor_total_banc_tarjeta/', ValorTotalBancTarjeta.as_view()),
    path('valor_total_sis_tarjeta/', ValorTotalSisTarjeta.as_view()),
    path('valor_total/', ValorTotal.as_view()),
    path('pago_tarjetasP/', PagosTarjetaUserP.as_view()),
    path('tarjeta_pago/', PagosTarjetaUser.as_view()),
    path('factura/', EmailFactura.as_view()),
    path('pagosol_efectivo/<str:pago_ID>', PagosSolicitudesEfectivo.as_view()),
    path('pagosol_tarjeta/<str:pago_ID>', PagosSolicitudesTarjeta.as_view()),
    path('enviaralerta/<str:user_email>/<str:asunto>/<str:texto>', EnviarAlerta.as_view()),
    path('politics/', Politics.as_view()), # solicitante
    path('politics/<str:identifier>/', Politics.as_view(), name='politica-detail'),
    path('planes/', Planes.as_view()),
    path('planes/<str:id>', Planes.as_view()),
    path('planesEstado/', PlanesEstado.as_view()),
    path('publicidades/', Publicidades.as_view()),
    path('publicidades/<str:id>', Publicidades.as_view()),
    path('publicidades_search/', FiltroPublicidadesNombres.as_view()),
    path('adminUser/<str:user>', AdminUser.as_view()),
    path('adminUserPass/', AdminUserPass.as_view()),
    path('ciudades/', Ciudades.as_view()),
    path('planProveedor/', PlanProveedorView.as_view()),
    path('planProveedor/<str:id>', PlanProveedorView.as_view()),
    path('dates-planproviders/', PlanProveedores_Filter_Date.as_view()),
    path('providersdate_search/', ProveedoresDate_Search_Name.as_view()),
    path('documentos_pendientes/', PendientesDocumentsView.as_view()),
    path('documentos_proveedores/',ProveedoresDocumentsView.as_view()),
    path('proveedores_registro/', ProveedorRegistro.as_view()),
    path('edicion_proveedor/', ProveedorEdicion.as_view()),
    path('notificacion-anuncio/', SendNotificacion.as_view()),
    path('notificacion-anuncio/<str:id>', SendNotificacion.as_view(), name='notificacion-anuncio-detail'),
    path('notificacion-anuncio-estado/', SendNotificacion_Details.as_view()),
    path('notificacion-anuncio-envio/', SendNotificacion_Details.as_view(), name='envio_notificacionmasi'),
    path('roles-permisos/', RolesPermisos.as_view()),
    path('roles-permisos/<str:id>', RolesPermisos.as_view()),
    path('obtener-proveedor/<str:pk>', Get_Proveedor.as_view()),
    path('datos-proveedor/<str:user>', Get_ProveedorByUser.as_view()),
    path('datos-admin/<str:user>', Get_AdminByUser.as_view()),
    path('solicitudes-proveedores/', SolicitudProfesionProveedor.as_view()),
    path('solicitudes-proveedores/<str:user>', SolicitudByName.as_view()),
    path('solicitud-profesion/<str:pk>', SolicitudDetails.as_view()),
    path('obtener_solicitudes_profesiones/', ManejoSolicitud.as_view()),
    path('crear_solicitud_profesion/', ManejoSolicitud.as_view()),
    path('change-solicitud/<str:pk>', ManejoSolicitud.as_view()),
    path('solicitudesDate_search/', Solicitudes_Filter_Date.as_view()),
    path('solicitudesUser_search/<str:user>', Solicitudes_Search_Name.as_view()),
    path('correo-solicitud/', CorreoSolicitud.as_view()),
    path('permisos', Permisos.as_view()),
    path('cargos/', Cargos.as_view()),
    path('cargo_delete/<str:id>', Cargos.as_view()),
    path('cargos/<str:pk>', Cargo_Details.as_view()),
    path('cargo_update/<str:id>', Cargos.as_view()),
    path('valor_total_provider/', ValorTotalProveedores.as_view()),
    path('profesion_proveedor/<str:proveedor_id>',ProfesionProveedor.as_view()),
    path('puntos/<str:email>',Puntos.as_view()),
    path('politica/',Politica.as_view()),
    re_path("static/", AdminPage.as_view()),
    path('actualizar_caducidad/<str:pk>', ActualizarCaducidad.as_view()),
    path('bancos/', Bancos.as_view()), # web
    path('bancos/delete/<int:id>', Bancos.as_view()),

    path('version_android_solicitante/', VerionAndroidSolicitante.as_view()),
    path('version_ios_solicitante/', VerionIosProveedor.as_view()),
    path('version_android_proveedor/', VerionAndroidProveedor.as_view()),
    path('version_ios_proveedor/', VerionIosProveedor.as_view()),

    # path('pagos/', Pagos.as_view()),
    # path('send_correo/', EnviarCorreoProveedor.as_view()),

]
#urlpatterns = format_suffix_patterns(urlpatterns)
