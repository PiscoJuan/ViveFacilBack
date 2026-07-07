from django.urls import path

from promotions.api.admin.views import (
    CuponDetailsAdminView,
    CuponesAdminView,
    PromocionDetailsAdminView,
    PromocionesAdminView,
    PromocionesListAdminView,
)

urlpatterns = [
    path("promociones/", PromocionesListAdminView.as_view()),
    path("promociones/<str:id>/", PromocionesAdminView.as_view()),
    path("promociones/detalle/<str:pk>/", PromocionDetailsAdminView.as_view()),
    path("promociones/estado/", PromocionDetailsAdminView.as_view()),
    path("cupones/", CuponesAdminView.as_view()),
    path("cupones/<str:id>/", CuponesAdminView.as_view()),
    path("cupones/estado/", CuponDetailsAdminView.as_view()),
]
