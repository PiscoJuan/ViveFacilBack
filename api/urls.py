from django.urls import path, re_path
#from rest_framework.urlpatterns import format_suffix_patterns
from api.views import *
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from . import views

# Endpoints movidos a apps de dominio (docs/refactor/04-fase-2-web.md) — se
# importan acá para que las rutas legacy de abajo sigan sirviendo el mismo
# código que las rutas nuevas bajo /web/, sin duplicar la implementación.
from accounts.api.web.views import (
    ProveedorPendienteWebView,
    ProveedoresPendientesEmailWebView,
)
from promotions.api.web.views import ConfirmarDescuentoWebView

# Endpoints movidos a apps de dominio (docs/refactor/05-fase-3-solicitante.md)
from accounts.api.solicitante.views import TarjetaCvcSolicitanteView
from catalog.api.solicitante.views import ProveedoresPorServicioSolicitanteView
from promotions.api.solicitante.views import (
    CuponAplicadoSolicitanteView,
    CuponCategoriaSolicitanteView,
    RevisarDescuentoUnicoSolicitanteView,
    UsarDescuentoUnicoSolicitanteView,
)
from payments.api.solicitante.views import (
    EmailFacturaSolicitanteView,
    PagoEfectivoSolicitanteView,
    PagoTarjetaSolicitanteView,
)

# Endpoints movidos a apps de dominio (docs/refactor/06-fase-4-proveedor.md, Tanda A)
from accounts.api.proveedor.views import (
    DocumentoProveedorView,
    RegistroProveedorView,
    VersionAndroidProveedorView,
    VersionIosProveedorView,
)
from catalog.api.proveedor.views import MisProfesionesProveedorView
from payments.api.proveedor.views import CuentaProveedorView
from content.api.proveedor.views import InsigniasProveedorView
from notifications.api.proveedor.views import NotificacionChatProveedorView

# Endpoints movidos a apps de dominio (docs/refactor/06-fase-4-proveedor.md, Tanda B)
from solicitudes.api.proveedor.views import (
    EnvioProveedorView,
    InteresadosEnProcesoPagProveedorView,
    InteresadosPagProveedorView,
    InteresadosPagEfectivoProveedorView,
    InteresadosPagTarjetaProveedorView,
    InteresadosPasadasPagProveedorView,
    InteresadosPorFechaProveedorView,
    SolicitudesPagadasProveedorView,
    SolicitudPorServicioProveedorView,
)
from solicitudes.api.solicitante.views import (
    AdjudicarSolicitudSolicitanteView,
    EnvioInteresadosSolicitanteView,
    SolicitudDetalleSolicitanteView,
    SolicitudesEnProcesoSolicitanteView,
    SolicitudesNoPagadasPagSolicitanteView,
    SolicitudesNoPagadasSolicitanteView,
    SolicitudesPagadasPagSolicitanteView,
    SolicitudesPagadasSolicitanteView,
    SolicitudesPasadasPagSolicitanteView,
    SolicitudesPasadasSolicitanteView,
    SolicitudesPendientesPagSolicitanteView,
    SolicitudesPendientesSolicitanteView,
)
# Endpoints movidos a apps de dominio (docs/refactor/07-fase-5-admin.md, Bloque 1)
from catalog.api.admin.views import (
    CategoriasAdminView,
    CiudadesAdminView,
    ProfesionesAdminView,
    ServiciosAdminView,
)
from content.api.admin.views import (
    CargoDetailsAdminView,
    CargosAdminView,
    InsigniaDetailsAdminView,
    InsigniasAdminView,
    MedallaEstadoAdminView,
    MedallasAdminView,
    PublicidadesAdminView,
    PublicidadesBuscarAdminView,
)
from payments.api.admin.views import PlanesAdminView, PlanesEstadoAdminView, PlanProveedorAdminView
from promotions.api.admin.views import (
    CuponDetailsAdminView,
    CuponesAdminView,
    PromocionDetailsAdminView,
    PromocionesAdminView,
)

# Endpoints movidos a apps de dominio (docs/refactor/07-fase-5-admin.md, Bloque 2)
from accounts.api.admin.views import (
    AdminDetailsAdminView,
    AdministradoresAdminView,
    GruposAdminView,
    PendientesDocumentsAdminView,
    PermisosAdminView,
    ProveedorDeleteAdminView,
    ProveedorEdicionAdminView,
    ProveedoresAdminView,
    ProveedoresDocumentsAdminView,
    ProveedoresPendientesAdminView,
    ProveedoresPendientesDetailsAdminView,
    ProveedoresPendientesEstadoAdminView,
    ProveedoresPendientesRechazoAdminView,
    ProveedoresProveedoresAdminView,
    ProveedoresProveedoresDetailsAdminView,
    ProveedoresRechazadosAdminView,
    ProveedoresRechazadosDetailsAdminView,
    RolesPermisosAdminView,
    SolicitantesAdminView,
)

# Endpoints movidos a apps de dominio (docs/refactor/07-fase-5-admin.md, Bloque 3)
from payments.api.admin.views import (
    PagosEfectivoAdminView,
    PagosEfectivoFechasAdminView,
    PagosEfectivoPaginadoAdminView,
    PagosSolicitudEfectivoAdminView,
    PagosSolicitudTarjetaAdminView,
    PagosTarjetaAdminView,
    PagosTarjetaFechasAdminView,
    PagosTarjetaPaginadoAdminView,
    PlanProveedoresFiltroFechaAdminView,
    ProveedoresFiltroFechaYNombreAdminView,
    ValorTotalAdminView,
    ValorTotalBancTarjetaAdminView,
    ValorTotalEfectivoAdminView,
    ValorTotalPayTarjetaAdminView,
    ValorTotalProveedoresAdminView,
    ValorTotalSisTarjetaAdminView,
    ValorTotalTarjetaAdminView,
)
from notifications.api.admin.views import (
    NotificacionAnuncioDetalleAdminView,
    NotificacionesAdminView,
    NotificacionesDetalleAdminView,
)
from content.api.admin.views import (
    ReadSuggestionsAdminView,
    SuggestionsDetalleAdminView,
    UnreadSuggestionsAdminView,
)

# Endpoints movidos a apps de dominio (docs/refactor/07-fase-5-admin.md, Bloque 4)
from catalog.api.admin.views import (
    ManejoSolicitudAdminView,
    SolicitudesProfesionAdminView,
    SolicitudesProfesionBusquedaAdminView,
    SolicitudesProfesionFechaAdminView,
    SolicitudPorUsuarioAdminView,
    SolicitudProfesionDetalleAdminView,
)

# Endpoints movidos a apps de dominio (cleanup post-Fase-5, checklist maestro,
# Bloque 1: auth/social/password/versionamiento)
from accounts.api.web.views import ProveedorPublicoWebView, RegistroWebView
from accounts.api.solicitante.views import (
    CambioPasswordCodigoSolicitanteView,
    CompleteDataUserSolicitanteView,
    DatosUsuarioSolicitanteView,
    FacebookLoginSolicitanteView,
    GoogleLoginSolicitanteView,
    PuntosSolicitanteView,
    RecuperarPasswordSolicitanteView,
    RegistroRedesSolicitanteView,
    SolicitanteUserSolicitanteView,
    ValidarCodigoSolicitanteView,
    VersionAndroidSolicitanteView,
    VersionIosSolicitanteView,
)
from accounts.api.proveedor.views import (
    ChangePasswordProveedorView,
    CompleteDataUserProveedorView,
    DatosUsuarioProveedorView,
    ProveedorPorCorreoProveedorView,
    ProveedorRegistroManualView,
    SolicitanteByUserDatosProveedorView,
)
from accounts.api.admin.views import (
    ActualizarCaducidadAdminView,
    ActualizarCaducidadProveedoresAdminView,
    AdminUserPassView,
    AdminUserView,
    DataProveedorProveedorAdminView,
    DatosAdminView,
    FiltroNombresAdminView,
    GetAdminByUserAdminView,
    LogoutAdminView,
    PendientesFilterDateAdminView,
    PendientesSearchAdminView,
    ProveedoresFilterDateAdminView,
    ProveedoresSearchAdminView,
    SolicitantesFilterAdminView,
    SolicitanteUserAdminView,
    UpdateProveedorPendienteAdminView,
    UsuariosAdminView,
)

# Endpoints movidos a apps de dominio (cleanup post-Fase-5, checklist maestro,
# Bloque 4: notifications + catalog + content)
from content.api.web.views import TerminosCondicionesWebView
from content.api.solicitante.views import InsigniasSolicitanteView
from promotions.api.solicitante.views import CuponAplicadoCrearSolicitanteView
from notifications.api.solicitante.views import NotificacionChatSolicitanteView
from notifications.api.admin.views import (
    CorreoSolicitudAdminView,
    EmailBienvenidaAdminView,
    EnviarAlertaAdminView,
    NotificacionGeneralAdminView,
)
from catalog.api.admin.views import (
    CrearProfesionesFaltantesAdminView,
    ProfesionProveedorAdminView,
    SincronizarProfesionProveedorAdminView,
)

router = DefaultRouter()
router.register(r'registro', RegistroWebView)
urlpatterns = router.urls

urlpatterns += [
    path('tarjetaPaymentez/', TarjetaCvcSolicitanteView.as_view()),  # movido a accounts, Fase 3
    path('cardAuth_delete/<str:token>', TarjetaCvcSolicitanteView.as_view()),  # movido a accounts, Fase 3
    path('categorias/', CategoriasAdminView.as_view()),  # movido a catalog, Fase 5
    path('insignias/', Insignias.as_view()),
    path('medallas/', MedallasAdminView.as_view()),  # movido a content, Fase 5
    path('medalla_update/<str:id>', MedallasAdminView.as_view()),  # movido a content, Fase 5
    path('insigniaspersonales/<str:id>', InsigniasPersonales.as_view()),
    path('medallaspersonales/', MedallasPersonales.as_view()),
    path('insignia_update/<str:id>', InsigniasAdminView.as_view()),  # movido a content, Fase 5
    path('insignia_delete/<str:id>', InsigniasAdminView.as_view()),  # movido a content, Fase 5
    path('insignias/<str:pk>', InsigniaDetailsAdminView.as_view()),  # movido a content, Fase 5
    path('insignia_estado/', InsigniaDetailsAdminView.as_view()),  # movido a content, Fase 5
    path('medalla_estado/', MedallaEstadoAdminView.as_view()),  # movido a content, Fase 5
    path('insignias_proveedor/', InsigniasProveedorView.as_view()),  # movido a content, Fase 4
    path('insignias_solicitantes/', InsigniasSolicitanteView.as_view()),  # movido a content, cleanup post-Fase-5
    path('suggestions/', Suggestions.as_view()),  # multi-rol (Provedor2022/Solicitante2022 crean), fuera de alcance de Fase 5
    path('read-suggestions/', ReadSuggestionsAdminView.as_view()),  # movido a content, Fase 5
    path('unread-suggestions/', UnreadSuggestionsAdminView.as_view()),  # movido a content, Fase 5
    path('suggestion/<str:pk>', SuggestionsDetalleAdminView.as_view()),  # movido a content, Fase 5
    path('suggestion_estado/', SuggestionsDetalleAdminView.as_view()),  # movido a content, Fase 5 — bug de 500 corregido (ver content.services.actualizar_estado_sugerencia)
    path('post-token/', DeviceNotification.as_view()),
    path('dispositivos-notificacion/', DeviceNotification.as_view()),  # solicitante y proveedor
    path('categoria_update/<str:id>', CategoriasAdminView.as_view()),  # movido a catalog, Fase 5
    path('categoria_delete/<str:id>', CategoriasAdminView.as_view()),  # movido a catalog, Fase 5
    path('servicios/', Servicios.as_view()), # GET compartido (solicitante, proveedor, web); POST admin delega a catalog.services, Fase 5
    path('servicios/<int:id>', ServiciosAdminView.as_view()),  # movido a catalog, Fase 5
    path('servicios_update/<str:id>', ServiciosAdminView.as_view()),  # movido a catalog, Fase 5
    path('servicios_delete/<str:id>', ServiciosAdminView.as_view()),  # movido a catalog, Fase 5
    path('logout/<str:token>', LogoutAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('solicitud/', Solicituds.as_view()), # proveedor y solicitante
    path('cupon_aplicado/', CuponAplicadoCrearSolicitanteView.as_view()),  # movido a promotions, cleanup post-Fase-5
    path('get_cupon_aplicado/<str:user>', CuponAplicadoSolicitanteView.as_view()), # movido a promotions, Fase 3
    #path('solicitud/<str:solicitud_ID>/<float:solicitud_Rate>', Solicituds.as_view()),
    path('solicitud/<str:solicitud_ID>', Solicituds.as_view()),
    # BUGFIX post-Fase-4: esta ruta legacy la sigue llamando ViveFacil_Solicitante2022
    # (getSolicitudById, sin migrar a namespace todavía) — el doc de Fase 4 la
    # tageó como solo-proveedor y se había repuntado a la vista IsProveedor,
    # devolviendo 403 real a solicitantes. Provedor2022 ya migró por completo a
    # `proveedor/solicitudes/<id>/detalle/`, así que el único consumidor real de
    # esta ruta legacy es solicitante — se repunta a esa vista.
    path('solicitudID/<str:solicitud_ID>', SolicitudDetalleSolicitanteView.as_view()),
    path('solicitudes/<str:user>', Solicitudes.as_view()),
    path('solicitudes_espera/<str:correo>', SolicitudesPendientesSolicitanteView.as_view()),      # movido a solicitudes, Fase 3
    path('solicitudes_pasadas/<str:correo>', SolicitudesPasadasSolicitanteView.as_view()),        # movido a solicitudes, Fase 3
    path('solicitudes_paid/<str:correo>', SolicitudesPagadasSolicitanteView.as_view()),           # movido a solicitudes, Fase 3
    path('solicitudes_no_paid/<str:correo>', SolicitudesNoPagadasSolicitanteView.as_view()),      # movido a solicitudes, Fase 3
    path('solicitudes_esperaPag/<str:correo>', SolicitudesPendientesPagSolicitanteView.as_view()), # movido a solicitudes, Fase 3
    path('solicitudes_pasadasPag/', SolicitudesPasadasPagSolicitanteView.as_view()),  # movido a solicitudes, Fase 3
    path('solicitudes_paidPag/<str:correo>', SolicitudesPagadasPagSolicitanteView.as_view()),      # movido a solicitudes, Fase 3
    path('solicitudes_no_paidPag/<str:correo>', SolicitudesNoPagadasPagSolicitanteView.as_view()),# movido a solicitudes, Fase 3
    path('solicitudes_enProceso/', SolicitudesEnProcesoSolicitanteView.as_view()),  # movido a solicitudes, Fase 3
    path('proveedores/', ProveedoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores/<str:id>', ProveedoresAdminView.as_view()),  # movido a accounts, Fase 5
    # path('proveedor/<str:pk>', Proveedores_Details.as_view()),                #este endpoint es una basura.
    path('providers-search/<str:user>', ProveedoresSearchAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('dates-providers/', ProveedoresFilterDateAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('proveedor_estado/<str:id>', ProveedoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedor_delete/<str:id>', ProveedoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('dato/<str:user>', Dato.as_view()),  # multi-rol; PUT delegado a accounts.services (Fase 4)
    path('datos/', DatosAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('usuarios/', UsuariosAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('datoRedes/<str:user>', RegistroRedesSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('profesiones/', Profesiones.as_view()), # GET compartido (web, Fase 2); POST/PUT admin delegan a catalog.services, Fase 5
    path('profesion/<str:pk>',ProfesionDetails.as_view()),
    path('profesiones/<str:pk>', ProfesionesAdminView.as_view()),  # movido a catalog, Fase 5
    path('proveedor_profesiones/', Proveedor_Profesiones.as_view()), # legacy; GET movido a catalog (Fase 4), sigue sirviendo también acá
    path('profesion_prov/<str:pk>', Proveedor_Profesiones.as_view()), # PUT usado por Admin, se migra en Fase 5
    path('crear_profesiones_faltantes/', CrearProfesionesFaltantesAdminView.as_view(), name='crear_profesiones_faltantes'),  # movido a catalog, cleanup post-Fase-5
    path('solicitud_servicio/<str:ID_servicio>/', SolicitudPorServicioProveedorView.as_view()),  # movido a solicitudes, Fase 4
    path('rest-auth/facebook/', FacebookLoginSolicitanteView.as_view(), name='fb_login'),  # movido a accounts, cleanup post-Fase-5
    path('rest-auth/google/', GoogleLoginSolicitanteView.as_view(), name='google_login'),  # movido a accounts, cleanup post-Fase-5
    path('envio/<str:solicitud_ID>', EnvioProveedorView.as_view()),  # movido a solicitudes, Fase 4
    path('envio_interesados/<str:solicitud_ID>', EnvioInteresadosSolicitanteView.as_view()), # movido a solicitudes, Fase 3
    path('solicitante/<str:user>', SolicitanteUser.as_view()),  # multi-rol; GET delegado a accounts.services (cleanup post-Fase-5)
    path('solicitanteByUserDatosID/<str:UserDatosId>', SolicitanteByUserDatosProveedorView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('solicitantes/', SolicitantesAdminView.as_view()),  # movido a accounts, Fase 5
    path('fechas-filtro/', SolicitantesFilterAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('filtro-usuario/<str:user>', FiltroNombresAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('solicitante_estado/<str:id>', SolicitantesAdminView.as_view()),  # movido a accounts, Fase 5
    path('solicitante_delete/<str:id>', SolicitantesAdminView.as_view()),  # movido a accounts, Fase 5
    path('administradores/', AdministradoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('admin-filtro/<str:user>', AdministradoresUser.as_view()),
    path('fechas_admin/', AdministradoresFilter.as_view()),
    path('fechas_efectivo/', PagosEfectivoFechasAdminView.as_view()),  # movido a payments, Fase 5 — también lo llama Provedor2022 (ver Fase 4, decisión de producto pendiente)
    path('fechas_tarjeta/', PagosTarjetaFechasAdminView.as_view()),  # movido a payments, Fase 5
    path('administrador/<str:pk>', AdminDetailsAdminView.as_view()),  # movido a accounts, Fase 5
    path('administrador_estado/', AdministradoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('administrador_delete/<str:id>', AdministradoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('addsolicitud/' , AddSolicitud.as_view()), # multi-rol (solicitante y proveedor, ver Fase 3)
    path('proveedores_pendientes/', ProveedoresPendientesAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_rechazados/', ProveedoresRechazadosAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_proveedores/', ProveedoresProveedoresAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_proveedores/<str:pk>', ProveedoresProveedoresDetailsAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_proveedores/delete/<str:proveedor_id>', ProveedorDeleteAdminView.as_view(), name='delete_proveedor'),  # movido a accounts, Fase 5
    path('pendientes-search/<str:user>', PendientesSearchAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('pendientes-filterDate/', PendientesFilterDateAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('proveedor_pendientes/', ProveedoresPendientesAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedor_pendiente/', ProveedorPendienteWebView.as_view()),  # movido a accounts, Fase 2
    path('proveedores_pendientes/<str:pk>', ProveedoresPendientesDetailsAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_pendientes_estado/', ProveedoresPendientesEstadoAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_pendientes_email/<str:mail>', ProveedoresPendientesEmailWebView.as_view()), # web (movido a accounts, Fase 2)
    path('proveedores_pendientes2/<str:pk>', ProveedoresPendientesRechazoAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_rechazados/<str:pk>', ProveedoresRechazadosDetailsAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_pendientes/<str:username>/<str:desc>', ProveedoresPendientesAdminView.as_view()),  # movido a accounts, Fase 5
    path('documentos_proveedor/<str:username>', DocumentoProveedorView.as_view()),  # movido a accounts, Fase 4
    path('cuenta_proveedor/<str:proveedorID>', CuentaProveedorView.as_view()),  # movido a payments, Fase 4
    path('register_proveedor/', RegistroProveedorView.as_view()),  # movido a accounts, Fase 4
    # segundo registro de 'proveedor_pendiente/' borrado (Fase 2): apuntaba
    # a Data_Proveedor_Pendiente, una vista inalcanzable por el shadowing de
    # Django (la de arriba siempre ganaba) y con un bug de todos modos —
    # ver docs/refactor/04-fase-2-web.md.
    path('proveedor_proveedor/', DataProveedorProveedorAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('update_pendiente/', UpdateProveedorPendienteAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('email/', EmailBienvenidaAdminView.as_view()),  # movido a notifications, cleanup post-Fase-5
    path('login/', Login.as_view()), # proveedor y solicitante
    path('loginadmin/', LoginAdmin.as_view()), # administrador
    path('changePassword/<str:access_security>', ChangePasswordProveedorView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('adjudicarsolicitud/<str:solicitud_ID>', AdjudicarSolicitudSolicitanteView.as_view()), # movido a solicitudes, Fase 3
    path('solicitud_adjudicada/<str:solicitud_ID>', SolicitudAdjudicada.as_view()),
    path('tarjeta/', Tarjetas.as_view()),
    path('tarjeta/<str:identifier>', TarjetaUser.as_view()),
    path('dato_usuario/<str:id>', Datos_Users.as_view()),  # multi-rol; GET delegado a accounts.services (cleanup post-Fase-5)
    path('complete_dato/<str:username>', Complete_Data_User.as_view()),  # multi-rol; PUT delegado a accounts.services (cleanup post-Fase-5)
    path('proveedores_servicio/<str:servicio_id>', ProveedoresPorServicioSolicitanteView.as_view()), # movido a catalog, Fase 3
    path('sincronizar_profesion_proveedor/', SincronizarProfesionProveedorAdminView.as_view(), name='sincronizar_profesion_proveedor'),  # movido a catalog, cleanup post-Fase-5

    path('confirmar_descuento/<str:mail>', ConfirmarDescuentoWebView.as_view()), # web (movido a promotions, Fase 2)
    path('revisar_descuento_unico/', RevisarDescuentoUnicoSolicitanteView.as_view()), # movido a promotions, Fase 3 (no es multi-rol, ver checklist)
    path('usar_descuento_unico/<str:mail>', UsarDescuentoUnicoSolicitanteView.as_view()), # movido a promotions, Fase 3

    # ! Quitar, ya no se va a usar
    path('proveedores_interesados/<str:id_proveedor_user_datos>',
         Proveedores_Interesados.as_view()),
    path('proveedores_interesadosFecha/<str:id_proveedor_user_datos>',
         InteresadosPorFechaProveedorView.as_view()),  # movido a solicitudes, cleanup post-Fase-5

    # Paginado (movido a solicitudes, Fase 4)
    path('proveedores_interesadosPag/<str:id_proveedor_user_datos>',
         InteresadosPagProveedorView.as_view()),


    # Paginado (movido a solicitudes, Fase 4)
    path('proveedores_interesadosPagEnProceso/<str:id_proveedor_user_datos>',
         InteresadosEnProcesoPagProveedorView.as_view()),
    # Paginado (movido a solicitudes, Fase 4)
    path('proveedores_interesadosPagPasados/<str:id_proveedor_user_datos>',
         InteresadosPasadasPagProveedorView.as_view()),


    path('proveedores_interesadosEfectivoPag/<str:id_proveedor_user_datos>',
         InteresadosPagEfectivoProveedorView.as_view()),  # movido a solicitudes, cleanup post-Fase-5
    path('proveedores_interesadosTarjetaPag/<str:id_proveedor_user_datos>',
         InteresadosPagTarjetaProveedorView.as_view()),  # movido a solicitudes, cleanup post-Fase-5
    path('solicitudes-pagadas/<str:id>', SolicitudesPagadasProveedorView.as_view()),  # movido a solicitudes, cleanup post-Fase-5
    path('notificaciones/', NotificacionesAdminView.as_view()),  # movido a notifications, Fase 5
    path('notificaciones/<str:id>', NotificacionesAdminView.as_view()),  # movido a notifications, Fase 5
    path('notificaciones_estado/', NotificacionesDetalleAdminView.as_view()),  # movido a notifications, Fase 5
    path('notificaciones-envio/', NotificacionesDetalleAdminView.as_view(), name='envio_notificacion'),  # movido a notifications, Fase 5
    path('notificacion_chat/', NotificacionChatSolicitanteView.as_view()),  # movido a notifications, cleanup post-Fase-5
    path('notificacion_chat_proveedor/', NotificacionChatProveedorView.as_view()),  # movido a notifications, Fase 4
    path('notificacion_general', NotificacionGeneralAdminView.as_view()),  # movido a notifications, cleanup post-Fase-5
    path('promociones/', Promociones.as_view()),  # GET compartido con Solicitante2022; POST admin delega a promotions.services, Fase 5
    path('promociones/<str:pk>', PromocionDetailsAdminView.as_view()),  # movido a promotions, Fase 5
    path('promcategorias/<str:promCode>', PromocionesCategoria.as_view()),
    path('all_promcategorias/', AllPromocionesCategoria.as_view()),
    path('promocion_update/<str:id>', PromocionesAdminView.as_view()),  # movido a promotions, Fase 5
    path('promocion_delete/<str:id>', PromocionesAdminView.as_view()),  # movido a promotions, Fase 5
    path('promocion_estado/', PromocionDetailsAdminView.as_view()),  # movido a promotions, Fase 5
    path('cupones/', CuponesAdminView.as_view()),  # movido a promotions, Fase 5 (lista admin-exclusiva, a diferencia de promociones/)
    path('all_cupones/', CuponesAdminView.as_view()),  # movido a promotions, Fase 5
    path('cupon_update/<str:id>', CuponesAdminView.as_view()),  # movido a promotions, Fase 5
    path('cupon_delete/<str:id>', CuponesAdminView.as_view()),  # movido a promotions, Fase 5
    path('cupones/<str:pk>', Cupon_Details.as_view()),  # GET compartido con Solicitante2022, sin tocar
    path('cupon_estado/', CuponDetailsAdminView.as_view()),  # movido a promotions, Fase 5
    path('cupon_cant/<str:pk>', Cupon_Cant.as_view()),
    path('cupcategorias/<str:promCode>', CuponesCategoria.as_view()),
    path('all_cupcategorias/', CuponCategoriaSolicitanteView.as_view()), # movido a promotions, Fase 3
    path('grupos/', GruposAdminView.as_view()),  # movido a accounts, Fase 5
    path('recuperarpassword/<str:user_email>', RecuperarPasswordSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('validarcodigo/<str:email>/<str:codigo>', ValidarCodigoSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    # (la 2da declaración duplicada de recuperarpassword/ que había acá era inalcanzable — Django resuelve en orden, se quita al migrar)
    path('cambiopasswordcodigo/<str:email>/<str:password>/<str:codigo>', CambioPasswordCodigoSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('cambiocontrasenia/', CambioContrasenia.as_view()), # proveedor y solicitante
    path('pago_tarjeta/', PagoTarjetaSolicitanteView.as_view()),  # movido a payments, cleanup post-Fase-5
    path('pago_efectivo/', PagoEfectivoSolicitanteView.as_view()), # movido a payments, Fase 3
    path('pago_tarjetas/', PagosTarjetaAdminView.as_view()), # movido a payments, Fase 5 (GET admin-exclusivo; PUT real se sirve por el alias tarjeta_pago/)
    path('pago_efectivos/', PagosEfectivoAdminView.as_view()),  # movido a payments, Fase 5
    path('pago_efectivosP/', PagosEfectivoPaginadoAdminView.as_view()),  # movido a payments, Fase 5
    path('valor_total_efectivo/', ValorTotalEfectivoAdminView.as_view()),  # movido a payments, Fase 5
    path('valor_total_tarjeta/', ValorTotalTarjetaAdminView.as_view()),  # movido a payments, Fase 5
    path('valor_total_pay_tarjeta/', ValorTotalPayTarjetaAdminView.as_view()),  # movido a payments, Fase 5
    path('valor_total_banc_tarjeta/', ValorTotalBancTarjetaAdminView.as_view()),  # movido a payments, Fase 5
    path('valor_total_sis_tarjeta/', ValorTotalSisTarjetaAdminView.as_view()),  # movido a payments, Fase 5
    path('valor_total/', ValorTotalAdminView.as_view()),  # movido a payments, Fase 5
    path('pago_tarjetasP/', PagosTarjetaPaginadoAdminView.as_view()),  # movido a payments, Fase 5
    path('tarjeta_pago/', PagosTarjetaAdminView.as_view()),  # movido a payments, Fase 5 (alias real del PUT, confirmado por grep)
    path('factura/', EmailFacturaSolicitanteView.as_view()),  # movido a payments, cleanup post-Fase-5
    path('pagosol_efectivo/<str:pago_ID>', PagosSolicitudEfectivoAdminView.as_view()),  # movido a payments, Fase 5
    path('pagosol_tarjeta/<str:pago_ID>', PagosSolicitudTarjetaAdminView.as_view()),  # movido a payments, Fase 5
    path('enviaralerta/<str:user_email>/<str:asunto>/<str:texto>', EnviarAlertaAdminView.as_view()),  # movido a notifications, cleanup post-Fase-5
    path('politics/', Politics.as_view()), # solicitante
    path('politics/<str:identifier>/', Politics.as_view(), name='politica-detail'),
    path('planes/', PlanesAdminView.as_view()),  # movido a payments, Fase 5
    path('planes/<str:id>', PlanesAdminView.as_view()),  # movido a payments, Fase 5
    path('planesEstado/', PlanesEstadoAdminView.as_view()),  # movido a payments, Fase 5
    path('publicidades/', PublicidadesAdminView.as_view()),  # movido a content, Fase 5
    path('publicidades/<str:id>', PublicidadesAdminView.as_view()),  # movido a content, Fase 5
    path('publicidades_search/', PublicidadesBuscarAdminView.as_view()),  # movido a content, Fase 5
    path('adminUser/<str:user>', AdminUserView.as_view()),  # movido a accounts, cleanup post-Fase-5 (dead code, ver checklist)
    path('adminUserPass/', AdminUserPassView.as_view()),  # movido a accounts, cleanup post-Fase-5 (dead code, ver checklist)
    path('ciudades/', Ciudades.as_view()),  # GET compartido (proveedor, solicitante); POST admin delega a catalog.services, Fase 5
    path('planProveedor/', PlanProveedorAdminView.as_view()),  # movido a payments, Fase 5
    path('planProveedor/<str:id>', PlanProveedorAdminView.as_view()),  # movido a payments, Fase 5
    path('dates-planproviders/', PlanProveedoresFiltroFechaAdminView.as_view()),  # movido a payments, cleanup post-Fase-5
    path('providersdate_search/', ProveedoresFiltroFechaYNombreAdminView.as_view()),  # movido a payments, cleanup post-Fase-5
    path('documentos_pendientes/', PendientesDocumentsAdminView.as_view()),  # movido a accounts, Fase 5
    path('documentos_proveedores/', ProveedoresDocumentsAdminView.as_view()),  # movido a accounts, Fase 5
    path('proveedores_registro/', ProveedorRegistroManualView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('edicion_proveedor/', ProveedorEdicionAdminView.as_view()),  # movido a accounts, Fase 5
    path('notificacion-anuncio/', SendNotificacion.as_view()),
    path('notificacion-anuncio/<str:id>', SendNotificacion.as_view(), name='notificacion-anuncio-detail'),
    path('notificacion-anuncio-estado/', NotificacionAnuncioDetalleAdminView.as_view()),  # movido a notifications, Fase 5
    path('notificacion-anuncio-envio/', NotificacionAnuncioDetalleAdminView.as_view(), name='envio_notificacionmasi'),  # movido a notifications, Fase 5
    path('roles-permisos/', RolesPermisosAdminView.as_view()),  # movido a accounts, Fase 5
    path('roles-permisos/<str:id>', RolesPermisosAdminView.as_view()),  # movido a accounts, Fase 5
    path('obtener-proveedor/<str:pk>', ProveedorPublicoWebView.as_view()),  # movido a accounts (web), cleanup post-Fase-5
    path('datos-proveedor/<str:user>', ProveedorPorCorreoProveedorView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('datos-admin/<str:user>', GetAdminByUserAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('solicitudes-proveedores/', SolicitudesProfesionAdminView.as_view()),  # movido a catalog, Fase 5
    path('solicitudes-proveedores/<str:user>', SolicitudPorUsuarioAdminView.as_view()),  # movido a catalog, Fase 5
    path('solicitud-profesion/<str:pk>', SolicitudProfesionDetalleAdminView.as_view()),  # movido a catalog, Fase 5
    path('obtener_solicitudes_profesiones/', ManejoSolicitudAdminView.as_view()),  # movido a catalog, Fase 5
    path('crear_solicitud_profesion/', ManejoSolicitudAdminView.as_view()),  # movido a catalog, Fase 5
    path('change-solicitud/<str:pk>', ManejoSolicitudAdminView.as_view()),  # movido a catalog, Fase 5
    path('solicitudesDate_search/', SolicitudesProfesionFechaAdminView.as_view()),  # movido a catalog, Fase 5
    path('solicitudesUser_search/<str:user>', SolicitudesProfesionBusquedaAdminView.as_view()),  # movido a catalog, Fase 5
    path('correo-solicitud/', CorreoSolicitudAdminView.as_view()),  # movido a notifications, cleanup post-Fase-5
    path('permisos', PermisosAdminView.as_view()),  # movido a accounts, Fase 5
    path('cargos/', CargosAdminView.as_view()),  # movido a content, Fase 5
    path('cargo_delete/<str:id>', CargosAdminView.as_view()),  # movido a content, Fase 5
    path('cargos/<str:pk>', CargoDetailsAdminView.as_view()),  # movido a content, Fase 5
    path('cargo_update/<str:id>', CargosAdminView.as_view()),  # movido a content, Fase 5
    path('valor_total_provider/', ValorTotalProveedoresAdminView.as_view()),  # movido a payments, Fase 5
    path('profesion_proveedor/<str:proveedor_id>', ProfesionProveedorAdminView.as_view()),  # movido a catalog, cleanup post-Fase-5
    path('puntos/<str:email>', PuntosSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('politica/', TerminosCondicionesWebView.as_view()),  # movido a content, cleanup post-Fase-5
    re_path("static/", AdminPage.as_view()),
    path('actualizar_caducidad/<str:pk>', ActualizarCaducidadAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('bancos/', Bancos.as_view()), # web
    path('bancos/delete/<int:id>', Bancos.as_view()),

    path('version_android_solicitante/', VersionAndroidSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('version_ios_solicitante/', VersionIosSolicitanteView.as_view()),  # movido a accounts, cleanup post-Fase-5
    path('version_android_proveedor/', VersionAndroidProveedorView.as_view()),  # movido a accounts, Fase 4
    path('version_ios_proveedor/', VersionIosProveedorView.as_view()),  # movido a accounts, Fase 4

    path('actualizar_caducidad_proveedores/', ActualizarCaducidadProveedoresAdminView.as_view()),  # movido a accounts, cleanup post-Fase-5 (público a propósito, ver checklist)
    
    # path('pagos/', Pagos.as_view()),
    # path('send_correo/', EnviarCorreoProveedor.as_view()),

]
#urlpatterns = format_suffix_patterns(urlpatterns)
