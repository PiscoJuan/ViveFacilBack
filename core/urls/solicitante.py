from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.api.solicitante.urls')),
    path('catalog/', include('catalog.api.solicitante.urls')),
    path('solicitudes/', include('solicitudes.api.solicitante.urls')),
    path('payments/', include('payments.api.solicitante.urls')),
    path('promotions/', include('promotions.api.solicitante.urls')),
    path('content/', include('content.api.solicitante.urls')),
    path('notifications/', include('notifications.api.solicitante.urls')),
]
