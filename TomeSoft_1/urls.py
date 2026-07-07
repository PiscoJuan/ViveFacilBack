from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include


urlpatterns = [
    path('admin/',       include('core.urls.admin')),
    path('proveedor/',   include('core.urls.proveedor')),
    path('solicitante/', include('core.urls.solicitante')),
    path('web/',         include('core.urls.web')),
    path('adminDefault/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root= settings.STATIC_ROOT)
