from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.api.proveedor.urls')),
    path('catalog/', include('catalog.api.proveedor.urls')),
    path('payments/', include('payments.api.proveedor.urls')),
    path('solicitudes/', include('solicitudes.api.proveedor.urls')),
    path('content/', include('content.api.proveedor.urls')),
    path('notifications/', include('notifications.api.proveedor.urls')),
]
