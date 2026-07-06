from itertools import chain
from django.core import serializers as serializador
from collections import namedtuple
from django.shortcuts import render
from django.shortcuts import redirect
from api.models import *
from api.serializers import *
from django.http import Http404, HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
from rest_framework.renderers import JSONRenderer
from django.contrib.auth.models import User, Group, Permission
from django.db.models import Count, Sum
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.permissions import IsAdministrador
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth import models
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
#from rest_auth.registration.views import SocialLoginView #en produccion
from dj_rest_auth.registration.views import SocialLoginView #en local
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as do_login
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.template.loader import get_template
from fcm_django.models import FCMDevice
from pyfcm import FCMNotification
from firebase_admin.messaging import Message, Notification
from django.db.models import Q
from datetime import date, timedelta, datetime
from base64 import b64encode
from django.utils.crypto import get_random_string
import uuid
import json
import requests
import http
import time
import hashlib
import datetime
import threading
from rest_framework.settings import api_settings
from api.pagination import MyPaginationMixin, MyCustomPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
import os
from django.core.files import File
import codecs
import pytz
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from TomeSoft_1.settings import ACCESS_URL
from firebase_admin import auth as fire_auth
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils.timezone import now, localtime
from django.utils import timezone
from django.db.models import Case, When, Value, CharField, DateTimeField
from django.db.models.functions import Cast

class TokenFirebase:
    expirado = False
    nuevo_token = None

def get_firebase_access_token():
    try:
        from firebase_admin import credentials
        import firebase_admin
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        import os
        from TomeSoft_1.settings import CRED_PATH, BASE_DIR
        # Ruta al archivo de credenciales
        # Generar el token de acceso utilizando google-auth
        credentials = service_account.Credentials.from_service_account_file(
            os.path.join(BASE_DIR, 'TomeSoft_1/vive-facil-66ae4-firebase-adminsdk-fo42r-94d590fc9a.json'),
            scopes=["https://www.googleapis.com/auth/firebase.messaging"]
        )

        # Solicitar un token de acceso
        credentials.refresh(Request())

        # Obtener el token de acceso
        FIREBASE_ACCESS_TOKEN = credentials.token
        return FIREBASE_ACCESS_TOKEN
    except Exception as e:
        print(f"Error al inicializar Firebase Admin SDK o al obtener el token de acceso: {e}")
        return None

@csrf_exempt
def send_notificationF(tokend, title, body, data):
    try:
        responses = []
        success_flag = False
        token_trabajo = settings.FIREBASE_ACCESS_TOKEN
        if not token_trabajo or TokenFirebase.expirado:
            token_trabajo = TokenFirebase.nuevo_token
        # Obtener token desde settings (no lo renueva si no hace falta)
        if not token_trabajo:
            print("No se pudo obtener el token de Firebase")
            return JsonResponse({"error": "No se pudo obtener el token de Firebase"}, status=500)

        print("Token Firebase listo.")
        unique_tokens = list(set(tokend))

        for token in unique_tokens:
            message = {
                "message": {
                    "token": token,
                    "notification": {"title": title, "body": body},
                    "data": data
                }
            }

            response = requests.post(
                settings.ACCESS_URL,
                json=message,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token_trabajo}'
                }
            )

            # Si el token expiró (401/403), lo renovamos y reintentamos una vez
            if response.status_code in (401, 403):
                print("Token Firebase expirado, renovando...")
                TokenFirebase.expirado = True
                token_obtenido = get_firebase_access_token()
                TokenFirebase.nuevo_token = token_obtenido
                token_trabajo = token_obtenido
                if token_obtenido:
                    response = requests.post(
                        settings.ACCESS_URL,
                        json=message,
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {token_obtenido}'
                        }
                    )

            print(f"Respuesta Firebase ({token}): {response.status_code}")

            if response.status_code == 200:
                success_flag = True
                responses.append({
                    "token": token,
                    "status_code": 200,
                    "response": response.json()
                })
            else:
                responses.append({
                    "token": token,
                    "status_code": response.status_code,
                    "response": response.text
                })

        if success_flag:
            return JsonResponse({
                "message": "Notificaciones enviadas con éxito.",
                "successful_responses": [r for r in responses if r["status_code"] == 200],
                "all_responses": responses
            })
        else:
            return JsonResponse({
                "message": "No se pudo enviar ninguna notificación.",
                "all_responses": responses
            })

    except Exception as e:
        print(f"Error general al enviar notificación: {e}")
        return JsonResponse({"error": "Error interno en el servidor", "details": str(e)}, status=500)

@csrf_exempt
def send_notificationI(token, title,body,data):
    try:
        # Verifica si el token está disponible
        if not settings.FIREBASE_ACCESS_TOKEN:
            print("No se pudo obtener el token de Firebase")
            return JsonResponse({"error": "No se pudo obtener el token de Firebase"}, status=500)

        # Recorrer cada token en la lista
        responses = []  # Almacena las respuestas de Firebase
        message = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": title,
                        "body": body
                    },
                    "data": data
                }
        }

            # Envía la petición POST a FCM
        response = requests.post(
                settings.ACCESS_URL,
                json=message,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {settings.FIREBASE_ACCESS_TOKEN}'
                }
        )

            # Guarda la respuesta
        responses.append({
                "token": token,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
        })

        # Devuelve todas las respuestas
        return JsonResponse({"message": "Notificaciones enviadas", "results": responses}, safe=False)
    except Exception as e:
        return JsonResponse({"error": "Error en el servidor", "details": str(e)}, status=500)

# CardsAuth movida a accounts.api.solicitante.views.TarjetaCvcSolicitanteView
# (Fase 3, docs/refactor/05-fase-3-solicitante.md). `tarjetaPaymentez/` y
# `cardAuth_delete/<token>` en urls.py importan la clase desde su nueva
# ubicación.


class InsigniasPersonales(APIView):
    """GET delegado a content.services.insignias_personales (cleanup
    post-Fase-5, Bloque 4) — endpoint multi-rol (Solicitante2022 y
    Provedor2022, grep confirmado), ruta legacy sin permiso reforzado,
    igual que antes. Nuevas rutas namespaced: `solicitante/content/insignias-personales/<id>`
    y `proveedor/content/insignias-personales/<id>`. El POST/PUT/DELETE
    de abajo nunca estuvieron alcanzables por esta URL (el patrón no
    captura `id` para POST, y aunque PUT/DELETE sí podrían matchear, no
    hay evidencia de ningún llamador real) — se dejan tal cual, fuera de
    alcance de este cleanup."""

    def get(self, request, id, format=None):
        from content import services as content_services

        serializer = InsigniaSerializer(content_services.insignias_personales(id), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        name = request.POST.get('nombre')
        # picture = request.POST.get('imagen')
        picture = request.FILES.get('imagen')
        service = request.POST.get('servicio')
        order = request.POST.get('pedidos')
        description = request.POST.get('descripcion')
        typ = request.POST.get('tipo')
        tipoUsuario = request.POST.get('tipoUsuario')
        insignia_creada = Insignia.objects.create(
            nombre=name, imagen=picture, servicio=service, pedidos=order, descripcion=description, tipo=typ, tipo_usuario=tipoUsuario)
        serializer = InsigniaSerializer(insignia_creada)
        data['insignia'] = serializer.data
        if insignia_creada:
            return Response(data)
        else:
            data['error'] = "Error al crear una insignia!."
            return Response(data)

    def put(self, request, id, format=None):
        insignia = Insignia.objects.get(id=id)
        serializer = InsigniaSerializer(
            insignia, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        insignia = Insignia.objects.get(id=id)
        insignia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MedallasPersonales(APIView):
    """GET delegado a content.services.medallas_personales (cleanup
    post-Fase-5, Bloque 4) — endpoint multi-rol (Solicitante2022 y
    Provedor2022, grep confirmado), ruta legacy con el mismo
    `IsAuthenticated` genérico de antes (no se endurece a un rol
    específico acá; sí lo hacen las rutas nuevas namespaced:
    `solicitante/content/medallas-personales/` y
    `proveedor/content/medallas-personales/`)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        from content import services as content_services

        serializer = MedallaSerializer(content_services.medallas_personales(request.user), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        name = request.POST.get('nombre')
        # picture = request.POST.get('imagen')
        picture = request.FILES.get('imagen')
        service = request.POST.get('servicio')
        order = request.POST.get('pedidos')
        description = request.POST.get('descripcion')
        typ = request.POST.get('tipo')
        tipoUsuario = request.POST.get('tipoUsuario')
        insignia_creada = Insignia.objects.create(
            nombre=name, imagen=picture, servicio=service, pedidos=order, descripcion=description, tipo=typ, tipo_usuario=tipoUsuario)
        serializer = InsigniaSerializer(insignia_creada)
        data['insignia'] = serializer.data
        if insignia_creada:
            return Response(data)
        else:
            data['error'] = "Error al crear una insignia!."
            return Response(data)

    def put(self, request, id, format=None):
        insignia = Insignia.objects.get(id=id)
        serializer = InsigniaSerializer(
            insignia, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        insignia = Insignia.objects.get(id=id)
        insignia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class Insignias(APIView):
    """El PUT/DELETE se movieron a content.api.admin.views.InsigniasAdminView
    (Fase 5) — nunca estuvieron wireados a ninguna URL real (código muerto,
    ver esa vista para el detalle). El GET/POST siguen acá: comparten la
    URL `insignias/` con el GET compartido de verdad con Provedor2022 y
    Solicitante2022 (grep confirmado)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]          # GET compartido con Provedor2022 y Solicitante2022
        return [IsAdministrador()]       # POST protegido (antes totalmente abierto)

    def get(self, request, format=None):
        insignias = Insignia.objects.all().filter()
        serializer = InsigniaSerializer(insignias, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from content import services as content_services

        return Response(content_services.crear_insignia(request.POST, request.FILES))


# Medallas se movió por completo a content.api.admin.views.MedallasAdminView
# (Fase 5) — admin-exclusivo, grep confirmado.

# Insignia_Details se movió por completo a
# content.api.admin.views.InsigniaDetailsAdminView (Fase 5) — ambas URLs
# (`insignias/<pk>`, `insignia_estado/`) eran admin-exclusivas.

# Medalla_Details: el GET nunca estuvo wireado a ninguna URL (`medallas/
# <pk>` no existe en api/urls.py) y además tenía un bug de copy-paste
# (consultaba Insignia en vez de Medalla) — código muerto, no se replica.
# El PUT (`medalla_estado/`, el único método real) se movió a
# content.api.admin.views.MedallaEstadoAdminView, Fase 5. Nota aparte:
# Medallas.delete (arriba) tenía el mismo tipo de bug de copy-paste
# (borraba una Insignia en vez de la Medalla pedida) — corregido al mover
# ese método, ver content.services.eliminar_medalla.

# InsigniasProveedor movida a content.api.proveedor.views.InsigniasProveedorView (Fase 4)


# InsigniaSolicitantes movida a content.api.solicitante.views.InsigniasSolicitanteView
# (cleanup post-Fase-5, Bloque 4) — sin evidencia de consumidor real en
# ningún frontend, migrada igual por consistencia.


class DeviceNotification(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, format=None):
        data = {}
        correo = request.data.get('correo')
        devices = FCMDevice.objects.filter(active=True,user=correo)
        serializer = FCMDeviceSerializer(devices, many=True)
        if len(devices) != 0:
            for device in devices:
                device.delete()
                num_devices += 1
            data['success'] = True
            data['dispositivos'] = serializer.data
            return Response(data)
        else:
            data['success'] = False
            data['message'] = 'No se han encontrados dispositivos con el correo: ' + \
                correo + ' registrados en la base de datos'
            return Response(data)

    # post/delete movidos a accounts.services (Fase 3, endpoint multi-rol
    # compartido con proveedor — ver docs/refactor/05-fase-3-solicitante.md).
    # Lógica movida sin duplicar; el GET de arriba NO se tocó (no hay
    # evidencia de que ningún frontend lo llame, y tiene un bug preexistente
    # de `num_devices` sin inicializar que se documenta y no se corrige por
    # tratarse de código sin uso confirmado).
    def post(self, request, format=None):
        from accounts import services
        data, http_status = services.registrar_dispositivo(request, request.data.get('token'))
        return Response(data, status=http_status)

    def delete(self, request, format=None):
        from accounts import services
        data, http_status = services.eliminar_dispositivos_por_correo(request.data.get('correo'))
        return Response(data, status=http_status)


class FormatEmail(APIView):
    def create_email(self, email, subject, template_path, context):
        template = get_template(template_path)
        content = template.render(context)
        email = EmailMultiAlternatives(
            subject=subject,
            body='',
            from_email=settings.EMAIL_HOST_USER,
            to=email,
            cc=[]  # Con Copia -- correo del Administrador.

        )
        email.attach_alternative(content, 'text/html')
        return email

    def send_email(self, email, subject, template_path, context):
        welcome_email = self.create_email(
            email,
            subject,
            template_path,
            context
        )
        welcome_email.send(fail_silently=False)

# Email movida a notifications.api.admin.views.EmailBienvenidaAdminView
# (cleanup post-Fase-5, Bloque 4) — confirmado exclusivo de Admin2022.


class EmailFactura(APIView):

    def post(self, request, format=None):
        data = {}
        emails = []
        email_user = request.data.get('email')
        formatEmail = FormatEmail()
        user = Datos.objects.get(user__username=email_user)
        if user is not None:
            user.security_access = uuid.uuid4()
            user.save()
            emails.append(email_user)
            # emails.append("axelauza31@gmail.com")
            fecha = request.data.get('fecha_emision')
            metodo = request.data.get('metodo')
            oferta = request.data.get('oferta')
            descuento = request.data.get('descuento')
            valor = request.data.get('valor')
            descripcion = request.data.get('descripcion')
            pago_desc = request.data.get('pago_descripcion')
            transaccion = request.data.get('transaccion')
            proveedor = request.data.get('proveedor')
            solicitud = request.data.get('solicitud')
            # emails = request.data.get('emails')
            try:
                asunto = 'Recibo Pago de Servicios Vive Fácil'
                thread = threading.Thread(target=formatEmail.send_email(emails, asunto, 'emails/factura.html', {"fecha_today": fecha, "fecha_emision": fecha, "solicitante_name": user.nombres + ' ' + user.apellidos, "solicitud_descripcion": solicitud,
                                                                                                                "transaccion_id": transaccion, "proveedor_name": proveedor, "pago_descripcion": pago_desc, "metodo_pago": metodo, "oferta": oferta, "descuento": descuento, "valor_total": valor}))
                thread.start()
                data['success'] = True
                data['clave'] = user.security_access
                return Response(data)
            except Exception as e:
                data['error'] = str(e)
                # data['success']=False
                return Response(data)
        else:
            data['success'] = False
            return Response(data)

# RecuperarPassword movida a
# accounts.api.solicitante.views.RecuperarPasswordSolicitanteView —
# confirmado real solo en Solicitante2022.


# EnviarAlerta movida a notifications.api.admin.views.EnviarAlertaAdminView
# (cleanup post-Fase-5, Bloque 4) — confirmado exclusivo de Admin2022.


# ValidarCodigo movida a
# accounts.api.solicitante.views.ValidarCodigoSolicitanteView — confirmado
# real solo en Solicitante2022.

# CambioPasswordCodigo movida a
# accounts.api.solicitante.views.CambioPasswordCodigoSolicitanteView — sin
# evidencia de llamador real ni siquiera en Solicitante2022.

# CambioContrasenia: lógica movida a accounts.services.cambiar_contrasenia_firebase
# (Fase 3, endpoint multi-rol compartido con proveedor).
class CambioContrasenia(APIView):
    def post(self, request, format=None):
        from accounts import services
        data, http_status = services.cambiar_contrasenia_firebase(
            request.data.get('token'), request.data.get('pass')
        )
        return Response(data, status=http_status)

# Categorias se movió por completo a catalog/api/admin/views.py
# (CategoriasAdminView) — no tenía consumidor fuera del panel admin (a
# diferencia de Servicios/Profesiones), Fase 5.


class Servicios(APIView):
    """El PUT/DELETE (`servicios/<id>`) se movió a
    catalog.api.admin.views.ServiciosAdminView (Fase 5) — esa URL era
    admin-exclusiva. El GET/POST siguen acá porque comparten la URL
    `servicios/` con el GET público (Fase 2, `web/catalog/servicios/`)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]          # GET público
        return [IsAdministrador()]       # POST protegido (antes solo IsAuthenticated: cualquier rol logueado podía crear servicios)

    def get(self, request, format=None):
        todas = request.GET.get('todas')
        servicios = Servicio.objects.all()
        if not todas:
            servicios = Servicio.objects.all().filter(estado = True)
        serializer = ServicioSerializer(servicios, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from catalog import services as catalog_services

        _, data = catalog_services.crear_servicio(
            request.POST.get('nombre'), request.POST.get('descripcion'),
            request.POST.get('categoria'), request.FILES.get('foto'),
        )
        return Response(data)


# Logout movida a accounts.api.admin.views.LogoutAdminView (cleanup
# post-Fase-5, Bloque 3) — ver docs/refactor/CHECKLIST-inventario-endpoints.md.


# RegistroFromRedes movida a
# accounts.api.solicitante.views.RegistroRedesSolicitanteView (cleanup
# post-Fase-5, Bloque 1) — sin evidencia de llamador real.

# Registro (viewset, router `registro/`) movida a
# accounts.api.web.views.RegistroWebView — endpoint multi-rol confirmado
# (Solicitante2022 + Admin2022), se registra público bajo `web/`.
# FacebookLogin/GoogleLogin movidas a accounts.api.solicitante.views
# (FacebookLoginSolicitanteView/GoogleLoginSolicitanteView) — confirmado
# uso exclusivo de Solicitante2022.


# Register_Proveedor movido a accounts.api.proveedor.views.RegistroProveedorView
# (Fase 4, Tanda A). Sin evidencia de llamador real en ningún frontend — ver
# docs/refactor/06-fase-4-proveedor.md.


# Update_Proveedor_Pendiente movida a
# accounts.api.admin.views.UpdateProveedorPendienteAdminView (cleanup
# post-Fase-5, Bloque 2 — ver docs/refactor/CHECKLIST-inventario-endpoints.md).


# Cupones_Aplicados movida a
# promotions.api.solicitante.views.CuponAplicadoCrearSolicitanteView
# (cleanup post-Fase-5, Bloque 4) — confirmado exclusivo de Solicitante2022
# (solo el POST tiene consumidor real; el PUT original tenía un bug real
# de AttributeError garantizado, corregido al mover el código, ver
# promotions.services.actualizar_cupon_aplicado).


# Get_Cupon_Aplicado movida a promotions.api.solicitante.views.CuponAplicadoSolicitanteView (Fase 3)


# Data_Proveedor_Proveedor movida a
# accounts.api.admin.views.DataProveedorProveedorAdminView (cleanup
# post-Fase-5, Bloque 2 — ver docs/refactor/CHECKLIST-inventario-endpoints.md).

# Los formularios "quiero ser proveedor" (público) y de alta manual de
# proveedor pendiente (admin) se movieron a accounts/api/web/views.py
# (ProveedorPendienteWebView, ProveedoresPendientesEmailWebView) —
# ver docs/refactor/04-fase-2-web.md.


# Proveedores_Pendientes_Details, Proveedores_Pendientes_Estado,
# Proveedores_Pendientes_Details2, Proveedores_Proveedores_Details,
# ProveedorDeleteView y Proveedores_Rechazados_Details movidas a
# accounts.api.admin.views.* (Fase 5, Bloque 2 — ver
# docs/refactor/07-fase-5-admin.md). Lógica compartida en accounts/services.py.


# Pendientes_Search_Name movida a
# accounts.api.admin.views.PendientesSearchAdminView (cleanup post-Fase-5,
# Bloque 2 — ver docs/refactor/CHECKLIST-inventario-endpoints.md).

# Pendientes_FilterDate movida a
# accounts.api.admin.views.PendientesFilterDateAdminView (cleanup
# post-Fase-5, Bloque 2).


class SolicitudAdjudicada(APIView):
    """Réplica movida a solicitudes.services.solicitud_adjudicada (cleanup
    post-Fase-5, Bloque 3) — endpoint multi-rol confirmado (Solicitante2022
    + Provedor2022). Se preserva sin permission_classes, igual que el
    original, hasta confirmar tráfico cero de versiones viejas de ambas apps."""

    def get(self, request, solicitud_ID, format=None):
        from solicitudes import services as solicitudes_services

        return Response(solicitudes_services.solicitud_adjudicada(solicitud_ID))


# AdjudicarSolicitud movida a solicitudes.api.solicitante.views.AdjudicarSolicitudSolicitanteView (Fase 3)


# SolicitudID movida a solicitudes.api.proveedor.views.SolicitudDetalleProveedorView (Fase 4)

# Las 9 variantes de listado de solicitudes (SolicitudesPending/Past/Paid/
# NoPaid, con y sin paginar, + SolicitudesEnProceso) movidas a
# solicitudes.api.solicitante.views.* (Fase 3,
# docs/refactor/05-fase-3-solicitante.md — no se colapsan en esta fase pese
# a ser casi-duplicadas, queda para una limpieza posterior).


# Solicituds: lógica movida a solicitudes.services (Fase 3, endpoint
# multi-rol compartido con proveedor).
class Solicituds(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        from solicitudes import services
        return Response(services.listar_todas_solicitudes())

    def put(self, request, solicitud_ID, format=None):
        from solicitudes import services
        data, http_status = services.actualizar_solicitud(solicitud_ID, request.data)
        return Response(data, status=http_status)


# AddSolicitud: lógica movida a solicitudes.services.crear_solicitud (Fase 3).
# Descubierto por grep durante la migración: pese a que el doc de fase lo
# tageaba como solo-solicitante, ViveFacil_Provedor2022 también llama
# `addsolicitud/` (python-anywhere.service.ts:293) — es multi-rol en la
# práctica, por eso esta ruta legacy NO se endurece a un solo rol.
class AddSolicitud(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        from solicitudes import services
        solicitud, data = services.crear_solicitud(request.data, request.FILES)
        if solicitud is not None:
            data['solicitud'] = SolicitudSerializer(solicitud).data
        return Response(data)



class Solicitudes(APIView):
    """Réplica movida a solicitudes.services.historial_solicitudes_por_email
    (cleanup post-Fase-5, Bloque 3) — endpoint multi-rol confirmado
    (Solicitante2022 + Provedor2022). Se preserva sin permission_classes,
    igual que el original, hasta confirmar tráfico cero de versiones viejas
    de ambas apps."""

    def get(self, request, user, format=None):
        from solicitudes import services as solicitudes_services

        return Response(solicitudes_services.historial_solicitudes_por_email(user))


class Profesiones(APIView):
    """El DELETE (`profesiones/<pk>`) se movió a
    catalog.api.admin.views.ProfesionesAdminView (Fase 5) — única URL
    admin-exclusiva propia de esta clase. GET/POST/PUT siguen acá porque
    comparten la URL `profesiones/` con el GET público (Fase 2,
    `web/catalog/profesiones/`)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]          # GET público
        return [IsAdministrador()]       # POST, PUT protegidos (antes solo IsAuthenticated)

    def get(self, request, format=None):
        profesion = Profesion.objects.all().filter(estado=1)
        serializer = ProfesionSerializer(profesion, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from catalog import services as catalog_services

        data = catalog_services.crear_profesion(
            request.data.get("nombre"), request.data.get("descripcion"),
            request.data.get("servicio"), request.FILES.get('foto'),
        )
        return Response(data)

    def put(self, request):
        from catalog import services as catalog_services

        data, valido = catalog_services.actualizar_profesion(
            request.data.get("id"), request.data.get("servicio"), request.data
        )
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)

# CrearProfesionesFaltantesView movida a
# catalog.api.admin.views.CrearProfesionesFaltantesAdminView (cleanup
# post-Fase-5, Bloque 4) — sin evidencia de consumidor real en ningún
# frontend, migrada igual por consistencia.


class ProfesionDetails(APIView):

    def get(self, request, pk, format=None):

        profesion = Profesion.objects.get(id=pk)
        serializer = ProfesionSerializer(profesion)
        return Response(serializer.data)


# ProfesionProveedor movida a catalog.api.admin.views.ProfesionProveedorAdminView
# (cleanup post-Fase-5, Bloque 4) — confirmado exclusivo de Admin2022.


# ProveedoresByProfesion movida a catalog.api.solicitante.views.ProveedoresPorServicioSolicitanteView (Fase 3)

# SincronizarProfesionProveedorView movida a
# catalog.api.admin.views.SincronizarProfesionProveedorAdminView (cleanup
# post-Fase-5, Bloque 4) — sin evidencia de consumidor real en ningún
# frontend, migrada igual por consistencia.

# ValorTotalProveedores movida a payments.api.admin.views.ValorTotalProveedoresAdminView
# (Fase 5, Bloque 3).

# ValorTotalSolicitantes: nunca estuvo wireada a ninguna URL (grep confirmado
# sobre api/urls.py) — código muerto, no se migra ni se le da ruta nueva.


# Proveedores movida a accounts.api.admin.views.ProveedoresAdminView
# (Fase 5, Bloque 2).


# Get_Proveedor movida a accounts.api.web.views.ProveedorPublicoWebView —
# sin evidencia de llamador real, se registra público por descarte.

# Get_ProveedorByUser movida a
# accounts.api.proveedor.views.ProveedorPorCorreoProveedorView — confirmado
# real, usado en el login de Provedor2022 antes de tener token.


# Get_AdminByUser movida a accounts.api.admin.views.GetAdminByUserAdminView
# (cleanup post-Fase-5, Bloque 2).

class Proveedores_Details(APIView):

    def get(self, request, pk, format=None):

        proveedor = Proveedor.objects.get(id=pk)
        serializer = ProveedorSerializer(proveedor)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        data = {}
        dataMensaje = {}

        proveedorActual = Proveedor.objects.get(id=pk)
        # info para correo
        data["profesion"] = request.data.get("profesion")
        data["email"] = proveedorActual.user_datos.user.email
        data["estado"] = False
        try:
            profesionObj = Profesion.objects.get(
                nombre=request.data.get("profesion"))
            profesion_creada = Profesion_Proveedor.objects.create(
                proveedor=proveedorActual, profesion=profesionObj, ano_experiencia=request.data.get("ano_experiencia"))
            solicitud = SolicitudProfesion.objects.get(
                id=request.data.get("idSolicitud"))
            documentoSolicitud = solicitud.documento
            documento_creado = Document.objects.create(descripcion="Documento", documento=File(
                documentoSolicitud, os.path.basename(documentoSolicitud.name)))
            proveedorActual.document.add(documento_creado)
            stringProfesiones = ""
            lista_profesiones_proveedor = Profesion_Proveedor.objects.all().filter(proveedor__id=pk)
            for profesion in lista_profesiones_proveedor:
                if stringProfesiones == "":
                    stringProfesiones = profesion.profesion.nombre
                else:
                    stringProfesiones = stringProfesiones + "," + profesion.profesion.nombre
            proveedorActual.profesion = stringProfesiones
            proveedorActual.save()
            # Notificacion a los usuarios
            # devices = FCMDevice.objects.filter(user__id= proveedorActual.user_datos.user.id)
            devices = FCMDevice.objects.filter( active=True,
                user__id=proveedorActual.user_datos.user.id)
            # Obtiene la lista de registration_ids (tokens)
            tokend = devices.values_list('registration_id', flat=True)

            dataMensaje["ruta"] = "/perfil"
            dataMensaje["descripcion"] = "¡Su solicitud de agregar profesión fue aceptada!"
            titles="Tienes una Nueva Profesión: "+profesion
            bodys="¡Dale un vistazo!"
            tokens=list(tokend)
            send_notificationF(tokens,titles,bodys,dataMensaje)

            data["error"] = "Sin Errores"
            return Response(data)
        except:
            data["error"] = "Con Errores"
            return Response(data)


# SolicitudProfesionProveedor y ManejoSolicitud movidos a
# catalog/api/admin/views.py (SolicitudesProfesionAdminView,
# ManejoSolicitudAdminView), docs/refactor/07-fase-5-admin.md, Bloque 4.


# CorreoSolicitud movida a notifications.api.admin.views.CorreoSolicitudAdminView
# (cleanup post-Fase-5, Bloque 4) — confirmado exclusivo de Admin2022.


# SolicitudByName, SolicitudDetails, Solicitudes_Search_Name y
# Solicitudes_Filter_Date movidos a catalog/api/admin/views.py
# (SolicitudPorUsuarioAdminView, SolicitudProfesionDetalleAdminView,
# SolicitudesProfesionBusquedaAdminView, SolicitudesProfesionFechaAdminView),
# docs/refactor/07-fase-5-admin.md, Bloque 4.


# Proveedores_Search_Name movida a
# accounts.api.admin.views.ProveedoresSearchAdminView (cleanup post-Fase-5,
# Bloque 2).

# Proveedores_Filter_Date movida a
# accounts.api.admin.views.ProveedoresFilterDateAdminView (cleanup
# post-Fase-5, Bloque 2).


# PlanProveedores_Filter_Date movida a
# payments.api.admin.views.PlanProveedoresFiltroFechaAdminView (cleanup
# post-Fase-5, Bloque 3) — sin evidencia de llamador real en ningún frontend.


# Documentos_proveedor movido a accounts.api.proveedor.views.DocumentoProveedorView
# (Fase 4, Tanda A). Sin evidencia de llamador real en ningún frontend.


# ProveedoresDocumentsView movida a
# accounts.api.admin.views.ProveedoresDocumentsAdminView (Fase 5, Bloque 2).


class Proveedores_Pendientes_exitente(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, username, name_profesion, format=None):
        data = {}
        try:
            proveedor_pendiente = Proveedor_Pendiente.objects.get(
                proveedor__user_datos__user__username=username, profesion=name_profesion)
            if proveedor_pendiente is not None:
                data['success'] = True
                return Response(data)
        except:
            data['success'] = False
            return Response(data)


# Proveedores_Pendientes y Proveedores_Rechazados movidas por completo a
# accounts.api.admin.views.* (Fase 5, Bloque 2).


# IMPORTANTE — Proveedores_Proveedores se deja definida a propósito, sin
# tocar: el bucle de abajo (escaneo de `fecha_caducidad`, envío de emails de
# "Cuenta caducada" y desactivación de cuentas) vive en el CUERPO de la
# clase, no dentro de ningún método — se ejecuta una sola vez, cada vez que
# Python importa este módulo (es decir, en cada arranque del servidor o
# `manage.py`), sin importar si la clase sigue o no registrada en alguna
# URL. Borrar la clase detendría ese efecto secundario (un cambio de
# comportamiento real, no solo un cambio de namespace). Sus métodos GET/PUT/
# DELETE de gestión de "proveedores_proveedores/" SÍ se movieron a
# accounts.api.admin.views.ProveedoresProveedoresAdminView (Fase 5, Bloque
# 2, ver accounts.services.listar_proveedores_proveedores_queryset) y ya no
# están wireados a ninguna URL acá — quedan huérfanos pero inofensivos.
# Hallazgo pendiente de decisión de producto, ver
# docs/refactor/CHECKLIST-inventario-endpoints.md.
class Proveedores_Proveedores(APIView, MyPaginationMixin):
    print("querysetBan")
    formatEmail = FormatEmail()
    today = timezone.now()
    for e in Proveedor.objects.all().order_by('-id').filter(fecha_caducidad__lt=today):
        if e.estado != False:
            thread = threading.Thread(target=formatEmail.send_email([e.user_datos.user.username], "Cuenta caducada", 'emails/enviarAlerta.html', {"username":e.user_datos.user.username, "contenido": "Tu cuenta ha caducado, si deseas extender tu contrato contactanos por nuestros canales oficiales."}))
            thread.start()
        e.estado = False
        e.save()
        datos=e.user_datos
        datos.estado=False
        datos.save()
    queryset = Proveedor.objects.all().order_by('-id')
    serializer_class = ProveedorSerializer
    pagination_class = MyCustomPagination


# CuentaProveedor movido a payments.api.proveedor.views.CuentaProveedorView
# (Fase 4, Tanda A). Sin evidencia de llamador real en ningún frontend.


# DatosUsers movida a accounts.api.admin.views.DatosAdminView (cleanup
# post-Fase-5, Bloque 2).

# Usuarios movida a accounts.api.admin.views.UsuariosAdminView (cleanup
# post-Fase-5, Bloque 2).


class Dato(APIView):
   # permission_classes = (IsAuthenticated,)
   # authentication_class = (TokenAuthentication)
    def get(self, request, user, format=None):
        data = {}
        proveedor = Datos.objects.all().filter(
            user__email=user) | Datos.objects.all().filter(user__username=user)
        serializer = DatosSerializer(proveedor, many=True)
        # print(JSONRenderer().render(serializer.data))
        data['dato'] = serializer.data
        return Response(data)

    # PUT movido a accounts.services.actualizar_datos_usuario (Fase 4,
    # endpoint multi-rol compartido con Proveedor y Solicitante — ver
    # accounts/api/proveedor/views.py::DatoProveedorView y
    # accounts/api/solicitante/views.py::DatoSolicitanteView). El GET de
    # arriba NO se tocó — sin evidencia de llamador real en ningún frontend.
    def put(self, request, user, formato=None):
        from accounts import services
        services.actualizar_datos_usuario(user, request.data, request.FILES)
        return Response(status=status.HTTP_200_OK)


class SolicitanteUser(APIView):
    """Endpoint multi-rol (Solicitante2022 + Admin2022, ver
    accounts.api.solicitante.views.SolicitanteUserSolicitanteView /
    accounts.api.admin.views.SolicitanteUserAdminView) — se deja la ruta
    legacy abierta (sin permission_classes, igual que antes) delegando a la
    misma función compartida, mismo criterio que `Dato.put` (Fase 4)."""

    def get(self, request, user, format=None):
        from accounts import services
        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(user), many=True)
        return Response(serializer.data)


# SolicitanteByUserDatos movida a
# accounts.api.proveedor.views.SolicitanteByUserDatosProveedorView —
# confirmado uso exclusivo de Provedor2022 (feature de chat), sin necesidad
# de doble-registro.


# Solicitantes movida a accounts.api.admin.views.SolicitantesAdminView
# (Fase 5, Bloque 2).


# SolicitantesFilter movida a accounts.api.admin.views.SolicitantesFilterAdminView
# (cleanup post-Fase-5, Bloque 2).

# FiltroNombres movida a accounts.api.admin.views.FiltroNombresAdminView
# (cleanup post-Fase-5, Bloque 2).


# Administradores y Admin_Details movidas a accounts.api.admin.views.*
# (Fase 5, Bloque 2).


class AdministradoresFilter(APIView, MyPaginationMixin):
    queryset = Administrador.objects.all()
    serializer_class = AdministradorSerializer
    pagination_class = MyCustomPagination

    def get(self, request):
        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(self.queryset.filter(
            user_datos__fecha_creacion__date__range=[fechaIn, fechaFi]))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class AdministradoresUser(APIView, MyPaginationMixin):

    queryset = Administrador.objects.all()
    serializer_class = AdministradorSerializer
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):

        page = self.paginate_queryset(self.queryset.filter(
            Q(user_datos__nombres__icontains=user) | Q(user_datos__apellidos__icontains=user)))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Proveedor_Profesiones(APIView):
    permission_classes = [IsAuthenticated]    
    def get(self, request, format=None):
        user = request.user
        proveedor_profesiones = Profesion_Proveedor.objects.filter(
            proveedor__user_datos__user=user) | Profesion_Proveedor.objects.filter(proveedor__user_datos__user=user)
        serializer = Profesion_ProveedorSerializer(
            proveedor_profesiones, many=True)
        c=0
        for prof in proveedor_profesiones:
            print('serializerTPA7')
            print(serializer.data[c]['profesion']['nombre'])
            servicioTemp = Servicio.objects.get(nombre=serializer.data[c]['profesion']['nombre'])
            # serializer.data[c]['profesion']['id'] = servicioTemp.id
            serializer.data[c]['profesion']['servicio'] = ServicioSerializer(servicioTemp).data
            c=c+1
        return Response(serializer.data)

    def post(self, request, format=None):
        user = request.user
        data = {}
        profesion = request.data.get('profesion')
        anios = request.data.get('ano_experiencia')
        try:
            profesionObj = Profesion.objects.get(nombre=profesion)
        except:
            data['success'] = False
            data['message'] = 'La profesion con el nombre pasado por parámetro no se ha encontrado en la base de datos.'
            return Response(data)

        try:
            proveedor = Proveedor.objects.get(user_datos__user=user)
        except:
            data['success'] = False
            data['message'] = 'El correo del proveedor pasado por parámetro no se ha encontrado en la base de datos.'
            return Response(data)

        proveedorProfesion = Profesion_Proveedor.objects.filter(
            profesion__id=profesionObj.id, proveedor__id=proveedor.id).first()
        if (proveedorProfesion):
            data['success'] = False
            data['message'] = 'Ya existe la tabla Profesion_Proveedor con el mismo proveedor y la misma profesión registrado en la base de datos.'
            return Response(data)
        else:
            profesion_creada = Profesion_Proveedor.objects.create(
                proveedor=proveedor, profesion=profesionObj, ano_experiencia=anios)
            serializer = Profesion_ProveedorSerializer(profesion_creada)

            # Actualiza el campo profesion de la tabla del Proveedor, agregando el string de la nueva profesion creada.
            stringProfesiones = ""
            lista_profesiones_proveedor = Profesion_Proveedor.objects.all().filter(
                proveedor__id=proveedor.id)
            for profesion_prov in lista_profesiones_proveedor:
                if stringProfesiones == "":
                    stringProfesiones = profesion_prov.profesion.nombre
                else:
                    stringProfesiones = stringProfesiones + "," + profesion_prov.profesion.nombre
            proveedor.profesion = stringProfesiones
            proveedor.save()

            # Notificacion al proveedor con el correo en especifico
            devices = FCMDevice.objects.filter(
                active=True, user=user)
            # Obtiene la lista de registration_ids (tokens)
            tokend = devices.values_list('registration_id', flat=True)
            titles="Tienes una Nueva Profesión: "+profesion,
            bodys="¡Dale un vistazo!",
            tokens=list(tokend)
            send_notificationF(tokens,titles,bodys,data)

            data['success'] = True
            data['message'] = 'Se ha creado la tabla Profesion_Proveedor y se ha registrado en la base de datos correctamente.'
            data['profesion_proveedor'] = serializer.data
            return Response(data)

    def put(self, request, pk):

        profesion_proveedor = Profesion_Proveedor.objects.get(id=pk)
        serializer = Profesion_ProveedorSerializer(
            profesion_proveedor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        data = {}
        try:
            profesion = Profesion_Proveedor.objects.get(id=pk)
        except:
            data['success'] = False
            data['message'] = 'No se encontró en la base de datos el objeto Profesion_Proveedor con el ID pasado por parámentro.'
            return Response(data)
        proveedor = profesion.proveedor
        profesion.delete()

        # Actualiza el campo profesion de la tabla del Proveedor, agregando el string de la nueva profesion creada.
        stringProfesiones = ""
        lista_profesiones_proveedor = Profesion_Proveedor.objects.all().filter(
            proveedor__id=proveedor.id)
        for profesion in lista_profesiones_proveedor:
            if stringProfesiones == "":
                stringProfesiones = profesion.profesion.nombre
            else:
                stringProfesiones = stringProfesiones + "," + profesion.profesion.nombre
        proveedor.profesion = stringProfesiones
        proveedor.save()
        data['success'] = True
        data['message'] = 'Se ha eliminado el objeto Profesion_Proveedor exitosamente.'
        return Response(data)


# Solicitud_Servicio_User movida a solicitudes.api.proveedor.views.SolicitudPorServicioProveedorView (Fase 4)

# Envio movida a solicitudes.api.proveedor.views.EnvioProveedorView (Fase 4)


# Notificacion_Chat movida a notifications.api.solicitante.views.NotificacionChatSolicitanteView
# (cleanup post-Fase-5, Bloque 4) — confirmado exclusivo de Solicitante2022
# (el frontend además hardcodeaba la URL completa de producción en vez de
# usar API_URL, normalizado de paso; ver notifications.services.notificar_chat_solicitante
# para el bug real preservado — NameError garantizado en la rama
# `isSolicitante=False`, que ningún llamador real dispara).

# Notificacion_Chat_Proveedor movida a notifications.api.proveedor.views.NotificacionChatProveedorView (Fase 4)

# Notificacion_General movida a notifications.api.admin.views.NotificacionGeneralAdminView
# (cleanup post-Fase-5, Bloque 4) — sin evidencia de consumidor real en
# ningún frontend, registrada bajo admin/ por descarte.

#! Paginar


class Proveedores_Interesados(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, id_proveedor_user_datos, format=None):
        envio_interesado = Envio_Interesados.objects.all().filter(
            proveedor__user_datos_id=id_proveedor_user_datos, interesado=True).order_by('-fecha_creacion')
        serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
        return Response(serializer.data)


# Proveedores_InteresadosFecha movida a
# solicitudes.api.proveedor.views.InteresadosPorFechaProveedorView (cleanup
# post-Fase-5, Bloque 3) — confirmado en uso activo por Provedor2022.

# Paginados


# Proveedores_Interesados_Pag, _Proceso_Pag y _Pasadas_Pag movidas a
# solicitudes.api.proveedor.views.Interesados{Pag,EnProcesoPag,PasadasPag}ProveedorView (Fase 4)


# Proveedores_Interesados_Efectivo_Pag y _Tarjeta_Pag movidas a
# solicitudes.api.proveedor.views.InteresadosPag{Efectivo,Tarjeta}ProveedorView
# (cleanup post-Fase-5, Bloque 3) — confirmado exclusivo de Provedor2022,
# el checklist original decía "probable admin/reportería".


# SolicitudesPagadas movida a
# solicitudes.api.proveedor.views.SolicitudesPagadasProveedorView (cleanup
# post-Fase-5, Bloque 3) — sin evidencia de llamador real en ningún frontend.


# Envio_Interesado movida a solicitudes.api.solicitante.views.EnvioInteresadosSolicitanteView (Fase 3)


# ChangePassword movida a
# accounts.api.proveedor.views.ChangePasswordProveedorView — sin evidencia
# de llamador real; el bug del GET (`super.get` sin invocar) se preserva
# tal cual, ver docstring de la vista nueva.


# Login: lógica de autenticación extraída a accounts.services.authenticate_login
# (AuthService, Fase 3 — docs/refactor/05-fase-3-solicitante.md). Endpoint
# multi-rol compartido con proveedor, la ruta legacy sigue sirviendo ambos
# roles sin cambio de permiso.
#
# Bug latente corregido al mover el código: si `authenticate()` devolvía
# None, el `post()` original no tenía `else` para ese caso y devolvía
# implícitamente `None` en vez de un `Response` — DRF lanza un
# AssertionError (500). En la práctica casi nunca se ejecutaba, porque
# `AuthenticationForm.is_valid()` (arriba) ya autentica y rechaza
# credenciales inválidas antes de llegar ahí; pero sí es la única
# validación de credenciales para `LoginSolicitanteView` (no usa
# AuthenticationForm), así que ahí el fix es necesario, no cosmético.
# `authenticate_login` agrega el `else` faltante.
class Login(APIView):
    def post(self, request, format=None):
        from accounts import services

        res_tipo = request.data.get('tipo')
        data = {}
        form = AuthenticationForm(data=request.data)
        if not form.is_valid():
            data['error'] = 'Error de formulario login'
            data['active'] = True
            data['form'] = request.data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        data, http_status = services.authenticate_login(request, username, password, res_tipo)
        data['form'] = request.data
        return Response(data, status=http_status)


class LoginAdmin(APIView):
    """Réplica exacta del branching manual, ahora delegado a
    `accounts.services.authenticate_login` (mismo AuthService compartido
    con Login/LoginSolicitanteView/LoginProveedorView, Fase 3/5). Se
    conserva `data['form'] = request.data` para no cambiar el shape de la
    respuesta legacy, igual que `Login.post()`."""

    def post(self, request, format=None):
        from accounts import services

        res_tipo = request.data.get('tipo')
        data = {}
        form = AuthenticationForm(data=request.data)
        if not form.is_valid():
            data['error'] = 'Error de formulario login'
            data['active'] = True
            data['form'] = request.data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        data, http_status = services.authenticate_login(request, username, password, res_tipo)
        data['form'] = request.data
        return Response(data, status=http_status)

# PAYMENTEZ-------------------------
class Paymentez:

    def getDELETEtokenPaymentez(self):
        try:
            server_application_code = 'INNOVA-EC-SERVER'
            server_app_key = 'Y5FnbpWYtULtj1Muvw3cl8LJ7FVQfM'
            unix_timestamp = str(int(time.time()))
            uniq_token_string = server_app_key + unix_timestamp
            uniq_token_string = uniq_token_string.encode('utf-8')
            uniq_token_hash = hashlib.sha256(uniq_token_string).hexdigest()
            to_encode = '%s;%s;%s' % (
                server_application_code, unix_timestamp, uniq_token_hash)
            auth_token = b64encode(to_encode.encode('utf-8'))
            return auth_token
        except:
            return None

    def getPOSTtokenPaymentez(self):
        try:
            server_application_code = 'INNOVA-EC-CLIENT'
            server_app_key = 'ZjgaQCbgAzNF7k8Fb1Qf4yYLHUsePk'
            unix_timestamp = str(int(time.time()))
            uniq_token_string = server_app_key + unix_timestamp
            uniq_token_string = uniq_token_string.encode('utf-8')
            uniq_token_hash = hashlib.sha256(uniq_token_string).hexdigest()
            to_encode = '%s;%s;%s' % (
                server_application_code, unix_timestamp, uniq_token_hash)
            auth_token = b64encode(to_encode.encode('utf-8'))
            return auth_token
        except:
            return None

    def remove_card(self, token, cedula):
        data = {}
        data['success'] = False
        auth_token = self.getDELETEtokenPaymentez()

        if auth_token == None:
            data['error'] = "auth_token no valido"
            return data

        header = {}
        header['Content-type'] = 'application/json'
        header['Auth-Token'] = auth_token.decode()

        dato = {'user': {'id': cedula}, 'card': {'token': token}}
        response = requests.post('https://ccapi-stg.paymentez.com/v2/card/delete/', data=json.dumps(dato),
                                 headers=header)

        if response.status_code >= 400:
            data['error'] = "No se pudo hacer el request en Paymentez"
            return data

        respuesta = response.json().get("message")
        data['success'] = True
        data['msg'] = respuesta['message']
        return data

    def add_card(self, dato):
        data = {}
        data['success'] = False
        auth_token = self.getPOSTtokenPaymentez()
        if auth_token == None:
            data['error'] = "auth_token no valido"
            return data

        header = {}
        header['Content-type'] = 'application/json'
        header['Auth-Token'] = auth_token.decode()

        response = requests.post(
            settings.PAYMENTEZ_HOST+'v2/card/add',  headers=header, data=json.dumps(dato))
        if response.status_code >= 400:
            data['error'] = response.json().get("error")
            return data

        card = response.json().get('error')
        data['card_info'] = card
        data['success'] = True
        return data


class TarjetaUser(APIView):
    """Réplica movida a payments.services.{list_tarjetas_por_usuario,
    eliminar_tarjeta} (cleanup post-Fase-5, Bloque 3) — GET multi-rol
    confirmado (Solicitante2022 + Provedor2022 lectura), DELETE exclusivo
    de Solicitante2022. Se preserva el mismo permiso (IsAuthenticated,
    cualquier rol) hasta confirmar tráfico cero de ambas apps."""

    permission_classes = [IsAuthenticated]

    def get(self, request, identifier, format=None):
        from payments import services as payments_services

        tarjetas = payments_services.list_tarjetas_por_usuario(identifier)
        return Response(TarjetaSerializer(tarjetas, many=True).data)

    def delete(self, request, identifier, format=None):
        from payments import services as payments_services

        return Response(payments_services.eliminar_tarjeta(identifier))


class Tarjetas(APIView):
    """Réplica movida a payments.services.{list_tarjetas_todas,
    crear_tarjeta} (cleanup post-Fase-5, Bloque 3). Se preserva el mismo
    permiso (IsAuthenticated) hasta confirmar tráfico cero."""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        from payments import services as payments_services

        return Response(TarjetaSerializer(payments_services.list_tarjetas_todas(), many=True).data)

    def post(self, request, format=None):
        from payments import services as payments_services

        return Response(payments_services.crear_tarjeta(request.data))


class Datos_Users(APIView):
    """Endpoint multi-rol (Solicitante2022 + Provedor2022, feature de chat —
    ver accounts.api.{solicitante,proveedor}.views.DatosUsuario*View). Ruta
    legacy abierta delegando a la función compartida, mismo criterio que
    `Dato.put`."""

    def get(self, request, id, format=None):
        from accounts import services
        serializer = DatosSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class Complete_Data_User(APIView):
    """Sin evidencia de llamador real en ningún frontend, endpoint genérico
    sobre `Datos` sin rol claro — se registra bajo ambos namespaces
    (solicitante/proveedor) por consistencia, ver
    accounts.api.{solicitante,proveedor}.views.CompleteDataUser*View. Ruta
    legacy abierta delegando a la función compartida."""

    def put(self, request, username, format=None):
        from accounts import services
        return Response(services.completar_datos_usuario(username, request.data))


# Notificaciones y Notificaciones_Details se movieron a
# notifications.api.admin.views.NotificacionesAdminView/
# NotificacionesDetalleAdminView (Fase 5, Bloque 3). La lógica de
# segmentación por profesión, antes duplicada acá y en
# SendNotificacion_Details.post, se unificó en
# notifications.services._notificar_proveedores_segmentado.

# Grupos movida a accounts.api.admin.views.GruposAdminView (Fase 5, Bloque 2).


class Promociones(APIView):
    """El PUT (`promocion_update/<id>`)/DELETE (`promocion_delete/<id>`) se
    movieron a promotions.api.admin.views.PromocionesAdminView (Fase 5) —
    únicas URLs admin-exclusivas propias de esta clase. GET/POST siguen acá
    porque comparten la URL `promociones/` con el GET compartido de verdad
    con Solicitante2022 (grep confirmado)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]          # GET compartido con Solicitante2022
        return [IsAdministrador()]       # POST protegido (antes totalmente abierto)

    def get(self, request, format=None):
        promociones = Promocion.objects.all().order_by("-pk")
        serializer = PromocionSerializer(promociones, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from promotions import services as promotions_services

        _, data = promotions_services.crear_promocion(request.data, request.POST.getlist('categorias'))
        return Response(data)


# Promocion_Details se movió por completo a
# promotions.api.admin.views.PromocionDetailsAdminView — ambas URLs
# (`promociones/<pk>`, `promocion_estado/`) eran admin-exclusivas, Fase 5.


# Cupones se movió por completo a promotions.api.admin.views.CuponesAdminView
# (Fase 5) — su GET (lista) es admin-exclusivo (a diferencia del de
# Promociones): Solicitante2022 solo usa `cupones/<id>` (Cupon_Details,
# sigue abajo sin tocar), grep confirmado.


class Cupon_Details(APIView):
    """El PUT (`cupon_estado/`) se movió a
    promotions.api.admin.views.CuponDetailsAdminView (Fase 5) — admin-
    exclusivo. El GET (`cupones/<pk>`) se queda acá: lo consume también
    Solicitante2022 (grep confirmado)."""

    def get(self, request, pk, format=None):
        cupon = Cupon.objects.get(id=pk)
        serializer = CuponSerializer(cupon)
        return Response(serializer.data)


class Cupon_Cant(APIView):
    def put(self, request, pk):
        cupo = Cupon.objects.get(id=pk)
        cupo.cantidad = request.data.get('cantidad')
        cupo.save()
        return Response(status=status.HTTP_200_OK)


class PromocionesCategoria(APIView):
    def get(self, request, promCode, format=None):
        promociones = PromocionCategoria.objects.all().filter(promocion__codigo=promCode)
        serializer = PromocionCategoriaSerializer(promociones, many=True)
        return Response(serializer.data)


class AllPromocionesCategoria(APIView):
    def get(self, request, format=None):
        promociones = PromocionCategoria.objects.all()
        serializer = PromocionCategoriaSerializer(promociones, many=True)
        return Response(serializer.data)


class CuponesCategoria(APIView):
    def get(self, request, cupCode, format=None):
        # Cambio CuponesCategoria por CuponCategoria
        cupones = CuponCategoria.objects.all().filter(cupon__codigo=cupCode)
        serializer = CuponCategoriaSerializer(cupones, many=True)
        return Response(serializer.data)


# AllCuponesCategoria movida a promotions.api.solicitante.views.CuponCategoriaSolicitanteView (Fase 3)


# PagosTarjeta (singular, `pago_tarjeta/`) movida a
# payments.api.solicitante.views.PagoTarjetaSolicitanteView (cleanup
# post-Fase-5, Bloque 3) — confirmado real de Solicitante2022, distinto de
# la familia admin `pago_tarjetas/`/`tarjeta_pago/` (PagosTarjetaUser).


# PagosEfectivo movida a payments.api.solicitante.views.PagoEfectivoSolicitanteView (Fase 3)


# PagosTarjetaUser, PagosEfectivoUser, PagosEfectivoUserP, EfectivosFilter,
# ValorTotalEfectivo, ValorTotalTarjeta, ValorTotalPayTarjeta,
# ValorTotalBancTarjeta, ValorTotalSisTarjeta, ValorTotal, TarjetasFilter,
# PagosTarjetaUserP, PagosSolicitudesEfectivo y PagosSolicitudesTarjeta se
# movieron a payments.api.admin.views.* (Fase 5, Bloque 3). Los alias de URL
# legacy `pago_tarjetas/` y `tarjeta_pago/` (antes ambos apuntaban a
# PagosTarjetaUser) siguen sirviendo el mismo código reapuntados a
# PagosTarjetaAdminView.

# PagosTarjeta (singular, `pago_tarjeta/`) NO se toca acá — es el endpoint
# real de pago con tarjeta de Solicitante2022 (confirmado en Fase 3/4), no
# forma parte de la gestión admin de esta fase.


class Suggestions(APIView):
    """POST delegado a content.services.crear_sugerencia (cleanup
    post-Fase-5, Bloque 4) — endpoint multi-rol confirmado (Solicitante2022
    y Provedor2022 crean sugerencias desde `ayuda.page.ts`), ruta legacy
    sin permiso reforzado, igual que antes. El GET (lista completa) no
    tiene consumidor real en ningún frontend — confirmado por grep, se
    deja tal cual. Nuevas rutas namespaced:
    `solicitante/content/sugerencias/` y `proveedor/content/sugerencias/`."""

    def get(self, request, format=None):
        sugerencia = Suggestion.objects.all().filter()
        serializer = SuggestionSerializer(sugerencia, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from content import services as content_services

        return Response(content_services.crear_sugerencia(request.POST, request.FILES))


# Suggestions_Details, ReadSuggestions y UnreadSuggestions se movieron a
# content.api.admin.views.* (Fase 5, Bloque 3). Bug real corregido al mover
# Suggestions_Details.put: ver content.services.actualizar_estado_sugerencia
# (el original exigía `pk` de la URL pero la ruta real que lo sirve
# (`suggestion_estado/`) nunca lo capturaba — 500 garantizado en cada
# llamada real desde Admin2022, que manda el id por query param).

# Suggestions (get/post, `suggestions/`) NO se toca acá — el GET no tiene
# consumidor confirmado y el POST (crear sugerencia) lo usan Provedor2022 y
# Solicitante2022, no es admin-exclusivo — fuera de alcance de esta fase.


class Politics(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]          # GET público
        return [IsAuthenticated()]      
    def get(self, request, format=None):
        politics = Politicas.objects.all().filter()
        serializer = PoliticasSerializer(politics, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        ident = request.data.get('identifier')
        term = request.data.get('terminos')
        pol = Politicas.objects.update_or_create(
            identifier=ident, defaults={'terminos': term})
        serializer = PoliticasSerializer(pol)
        data['politics'] = serializer.data
        if pol:
            return Response(data)
        else:
            data['error'] = "Error al crear!."
            return Response(data)

    def put(self, request, identifier, format=None):
        try:
            pol = Politicas.objects.get(identifier=identifier)
            term = request.data.get('terminos')
            pol.terminos = term
            pol.save()
            serializer = PoliticasSerializer(pol)
            data = {'politics': serializer.data}
            return Response(data)
        except Politicas.DoesNotExist:
            return Response({"error": "Política no encontrada."}, status=status.HTTP_404_NOT_FOUND)


# Planes, Publicidades y FiltroPublicidadesNombres se movieron por completo
# a payments.api.admin.views.PlanesAdminView y
# content.api.admin.views.PublicidadesAdminView/PublicidadesBuscarAdminView
# (Fase 5) — admin-exclusivos, grep confirmado.


# AdminUser/AdminUserPass movidas a accounts.api.admin.views
# (AdminUserView/AdminUserPassView) — dead code confirmado (definidas en
# python-anywhere.service.ts de Admin2022, cero llamadores reales: el
# login real de Admin2022 usa Firebase directo, ver Fase 5, Bloque 4).


class Ciudades(APIView):
    """GET compartido de verdad por Provedor2022 y Solicitante2022 (grep
    confirmado) — no se toca. El POST es admin-exclusivo y ahora delega a
    catalog.services.crear_ciudad (Fase 5), igual que
    catalog.api.admin.views.CiudadesAdminView registrada bajo
    `admin/catalog/ciudades/`.

    Nota: Admin2022 llama además un PUT a esta misma URL
    (`ciudades/`) que nunca existió en el backend (`Ciudades` nunca
    definió ese método) — 405 real, no se inventa acá, ver
    docs/refactor/CHECKLIST-inventario-endpoints.md."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdministrador()]

    def get(self, request, formt=None):
        ciudades = Ciudad.objects.all().filter()
        serializer = CiudadSerializer(ciudades, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from catalog import services as catalog_services

        data, valido = catalog_services.crear_ciudad(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)


# PlanProveedorView y PlanesEstado se movieron por completo a
# payments.api.admin.views.PlanProveedorAdminView/PlanesEstadoAdminView
# (Fase 5) — admin-exclusivos, grep confirmado.


# class PlanillasView(ModelViewSet):

#     queryset = Planilla_Servicios.objects.all()
#     serializer_class = PlanillasServiciosSerializer
#     parser_classes = (MultiPartParser, FormParser)


# PendientesDocumentsView movida a
# accounts.api.admin.views.PendientesDocumentsAdminView (Fase 5, Bloque 2).


# ProveedoresDate_Search_Name movida a
# payments.api.admin.views.ProveedoresFiltroFechaYNombreAdminView (cleanup
# post-Fase-5, Bloque 3) — sin evidencia de llamador real en ningún frontend.


# ProveedorRegistro movida a
# accounts.api.proveedor.views.ProveedorRegistroManualView — sin evidencia
# de llamador real en ningún frontend.


# ProveedorEdicion movida a accounts.api.admin.views.ProveedorEdicionAdminView
# (Fase 5, Bloque 2).


class SendNotificacion(APIView):
    """GET compartido de verdad con Provedor2022 y Solicitante2022 (grep
    confirmado); el método análogo del lado proveedor (`postNotificacionMasiva`
    en python-anywhere.service.ts) existe en el frontend pero no lo llama
    ningún componente — código muerto, no hay un segundo emisor real. Por
    eso POST/PUT/DELETE se endurecen a admin-only sin romper nada. La
    implementación se delega a `notifications.services` (Fase 5, Bloque 3);
    esta clase se queda en `api/views.py` porque el GET no puede
    registrarse bajo `admin/` sin duplicar la URL que ya usan los otros dos
    roles."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        from notifications import services as notifications_services

        serializer = NotificacionMasivaSerializer(notifications_services.list_notificaciones_masivas(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        from notifications import services as notifications_services

        notificacion, data = notifications_services.crear_notificacion_masiva(request.data, request.FILES)
        if notificacion is not None:
            data['notificacion_masiva'] = NotificacionMasivaSerializer(notificacion).data
        return Response(data)

    def put(self, request, id, format=None):
        from notifications import services as notifications_services

        try:
            notificacion = notifications_services.actualizar_notificacion_masiva(id, request.data)
            serializer = NotificacionMasivaSerializer(notificacion, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotificacionMasiva.DoesNotExist:
            return Response({"error": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        from notifications import services as notifications_services

        success, message = notifications_services.eliminar_notificacion_masiva(id)
        return Response({"success": success, "message": message})


# SendNotificacion_Details se movió por completo a
# notifications.api.admin.views.NotificacionAnuncioDetalleAdminView (Fase 5,
# Bloque 3) — a diferencia de SendNotificacion, esta clase no tiene ningún
# verbo compartido con otros roles (`notificacion-anuncio-estado/` y
# `notificacion-anuncio-envio/` son admin-exclusivas).



# RolesPermisos y Permisos movidas a accounts.api.admin.views.* (Fase 5,
# Bloque 2). Ver accounts.services.actualizar_permisos_grupo para un
# hallazgo real de lógica invertida en el PUT de RolesPermisos, preservado
# tal cual (no es un crash, es lógica de negocio — fuera de alcance).


# Cargos y Cargo_Details se movieron por completo a
# content.api.admin.views.CargosAdminView/CargoDetailsAdminView (Fase 5) —
# admin-exclusivos, grep confirmado.


# Puntos movida a accounts.api.solicitante.views.PuntosSolicitanteView —
# confirmado real, exclusivo de Solicitante2022.

# Politica movida a content.api.web.views.TerminosCondicionesWebView
# (cleanup post-Fase-5, Bloque 4) -- texto estatico hardcodeado, sin
# consumidor real en ningun frontend (endpoint distinto de politics/,
# pese al nombre parecido), migrada igual por consistencia.

# ConfirmarDescuento se movió a promotions/api/web/views.py
# (ConfirmarDescuentoWebView) — ver docs/refactor/04-fase-2-web.md.


# RevisarDescuentoUnico/UsarDescuentoUnico movidas a
# promotions.api.solicitante.views.* (Fase 3). El comentario viejo de
# `revisar_descuento_unico/` en urls.py decía "# proveedor", pero grep
# confirmó que solo ViveFacil_Solicitante2022 las llama — no son multi-rol
# pese a la etiqueta.


class AdminPage(APIView):
    def get (self, request):
        return redirect(to="/static/index.html")

# ActualizarCaducidad movida a
# accounts.api.admin.views.ActualizarCaducidadAdminView — confirmado real,
# exclusivo de Admin2022.

class Bancos(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]          # GET público
        return [IsAuthenticated()]       # POST, PUT, DELETE protegidos    
    def get(self, request):
        try:
            bancos = Banco.objects.all()
            print(bancos)
            serializer = BancoSerializer(bancos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            banco = Banco.objects.get(pk=id)
            banco.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Banco.DoesNotExist:
            return Response({'error': 'Banco no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        nombre = request.data.get('nombre')
        estado = request.data.get('estado')

        if not nombre or not estado:
            return Response({'error': 'Nombre y estado son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        bancocreado = Banco.objects.create(nombre=nombre, estado=estado)

        return Response({'id': bancocreado.id, 'nombre': bancocreado.nombre, 'estado': bancocreado.estado}, status=status.HTTP_201_CREATED)
# VerionAndroidSolicitante/VerionIosSolicitante movidas a
# accounts.api.solicitante.views (VersionAndroidSolicitanteView/
# VersionIosSolicitanteView) — confirmado real (app.component.ts).

# VerionAndroidProveedor / VerionIosProveedor movidos a
# accounts.api.proveedor.views (Fase 4, Tanda A).

# ActualizarCaducidadProveedoresRequest movida a
# accounts.api.admin.views.ActualizarCaducidadProveedoresAdminView — sin
# evidencia de llamador real; se preserva pública (IsPublic) por el riesgo
# de un cron externo no verificable desde el repo, ver docstring de la
# vista nueva y el checklist.
