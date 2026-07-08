import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.static import serve


def serve_spa(request, path):
    if '.' in path.rsplit('/', 1)[-1]:
        return serve(request, path, document_root=settings.STATIC_ROOT)
    with open(os.path.join(settings.STATIC_ROOT, 'index.html'), 'rb') as f:
        return HttpResponse(f.read(), content_type='text/html')


urlpatterns = [
    path('administrador/', include('core.urls.admin')),
    path('proveedor/',   include('core.urls.proveedor')),
    path('solicitante/', include('core.urls.solicitante')),
    path('web/',         include('core.urls.web')),
    path('admin/', admin.site.urls),
    re_path(r'^static/(?P<path>.*)$', serve_spa),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
