from django.urls import path

from promotions.api.admin.views import (
    CuponDetailsAdminView,
    CuponesAdminView,
    CuponUsosAdminView,
)

# OJO CON EL ORDEN: Django resuelve la primera ruta que coincide, y `<str:id>`
# también hace match con la palabra "estado". Las rutas literales tienen que ir
# ANTES de las paramétricas.
#
# Estaban al revés: `PUT cupones/estado/` nunca llegaba a su vista, caía en la
# de actualizar, no encontraba el cupón y devolvía HTTP 200 con un error en el
# body. Resultado: el interruptor de activo/inactivo del admin no hacía nada y
# parecía haber funcionado.
urlpatterns = [
    path("cupones/", CuponesAdminView.as_view()),
    path("cupones/estado/", CuponDetailsAdminView.as_view()),
    path("cupones/<str:pk>/usos/", CuponUsosAdminView.as_view()),
    path("cupones/<str:pk>/detalle/", CuponDetailsAdminView.as_view()),
    path("cupones/<str:id>/", CuponesAdminView.as_view()),
]
