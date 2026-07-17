from django.urls import path

from solicitudes.api.admin.views import SolicitudAdminDetalleView, SolicitudesAdminView

urlpatterns = [
    path("", SolicitudesAdminView.as_view()),
    path("<int:pk>/", SolicitudAdminDetalleView.as_view()),
]
