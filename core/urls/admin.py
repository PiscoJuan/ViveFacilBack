from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.api.admin.urls')),
    path('catalog/', include('catalog.api.admin.urls')),
    path('content/', include('content.api.admin.urls')),
    path('notifications/', include('notifications.api.admin.urls')),
    path('payments/', include('payments.api.admin.urls')),
    path('promotions/', include('promotions.api.admin.urls')),
    path('solicitudes/', include('solicitudes.api.admin.urls')),
]
