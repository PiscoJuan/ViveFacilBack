from django.urls import path

from solicitudes.api.admin.views import SolicitudesAdminView

urlpatterns = [
    path("", SolicitudesAdminView.as_view()),
]
