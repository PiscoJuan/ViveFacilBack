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
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth import models
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
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
from TomeSoft_1.settings import ACCESS_URL, FIREBASE_ACCESS_TOKEN

@csrf_exempt
def send_notificationF(tokend, title, body, data):
    try:
        # Verifica si el token está disponible
        if not FIREBASE_ACCESS_TOKEN:
            print("Error: No se pudo obtener el token de Firebase.")
            return JsonResponse({"error": "No se pudo obtener el token de Firebase"}, status=500)

        print("Firebase Access Token obtenido correctamente.")

        # Eliminar duplicados de la lista de tokens
        unique_tokens = list(set(tokend))  # Convertir a conjunto y luego a lista para eliminar duplicados
        print(f"Tokens únicos para enviar notificaciones: {unique_tokens}")

        # Inicializa la lista para almacenar respuestas de Firebase
        responses = []
        success_flag = False  # Flag to track if at least one notification was successful

        # Recorrer cada token en la lista
        for token in unique_tokens:
            print(f"Enviando notificación al token: {token}")

            # Cuerpo de la notificación
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
            print(f"Mensaje a enviar: {message}")

            # Envía la petición POST a FCM
            try:
                response = requests.post(
                    ACCESS_URL,
                    json=message,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {FIREBASE_ACCESS_TOKEN}'
                    }
                )
                print(f"Respuesta de Firebase para token {token}: {response.status_code} - {response.text}")

                # Guarda la respuesta
                if response.status_code == 200:
                    success_flag = True  # Mark as success if at least one notification succeeds
                    responses.append({
                        "token": token,
                        "status_code": response.status_code,
                        "response": response.json()
                    })
                else:
                    responses.append({
                        "token": token,
                        "status_code": response.status_code,
                        "response": response.text
                    })
            except requests.exceptions.RequestException as req_error:
                print(f"Error al enviar la notificación al token {token}: {req_error}")
                responses.append({
                    "token": token,
                    "status_code": 500,
                    "response": f"Error de conexión: {req_error}"
                })

        # Verifica si al menos una notificación fue exitosa
        if success_flag:
            print("Al menos una notificación fue enviada exitosamente.")
            successful_responses = [res for res in responses if res["status_code"] == 200]
            print(f"Notificaciones exitosas: {successful_responses}")
            return JsonResponse({
                "message": "Notificaciones enviadas con éxito.",
                "successful_responses": successful_responses,
                "all_responses": responses
            }, safe=False)
        else:
            print("No se pudo enviar ninguna notificación.")
            return JsonResponse({
                "message": "No se pudo enviar ninguna notificación.",
                "all_responses": responses
            }, safe=False)

    except Exception as e:
        print(f"Error en el servidor: {str(e)}")
        return JsonResponse({"error": "Error en el servidor", "details": str(e)}, status=500)



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

class CardsAuth(APIView):

    # aqui es donde se busca una credencial por token mediane mysql
    def get(self, request, format=None):
        resp = {}
        if request.method == 'GET':
            valor = request.GET.get("token")
            if valor != None:
                cards = Cardauth.objects.get(token=valor)
                return JsonResponse(cards.auth, safe=False)
            else:
                resp['sucess'] = False
                resp['message'] = 'No existe token pasado por parametro'
                return Response(resp)
        else:
            resp['sucess'] = False
            resp['message'] = 'No es metodo get'
            return Response(resp)
            # return HttpResponse(status=400)

    # aqui es donde se añade una credencial mediante mysql

    def post(self, request, format=None):
        if request.method == 'POST':
            response = json.loads(request.body)
            ntoken = response["token"]
            nauth = response["cvc"]
            try:
                existe = Cardauth.objects.filter(token=ntoken)
                total = existe.count()
                if total == 0:
                    ncard = Cardauth(token=ntoken, auth=nauth)
                    ncard.save()
                    response_data = {
                        'valid': 'OK'
                    }
                    return JsonResponse(response_data, safe=False)
            except Cardauth.DoesNotExist:
                ncard = Cardauth(token=ntoken, auth=nauth)
                ncard.save()
                response_data = {
                    'valid': 'OK'
                }
                return JsonResponse(response_data, safe=False)
        response_data = {
            'valid': 'NO'
        }
        return JsonResponse(response_data, safe=False)

    # aqui es donde se elimina una credencial por token

    def delete(self, request, token, format=None):
        resp = {}
        if token:
            try:
                cards = Cardauth.objects.get(token=token)
                cards.delete()
                resp['success'] = True
                resp['message'] = 'Credencial eliminada exitosamente'
                return JsonResponse(resp)
            except Cardauth.DoesNotExist:
                resp['success'] = False
                resp['message'] = 'No se encontró la credencial con el token proporcionado'
                return JsonResponse(resp)
        else:
            resp['success'] = False
            resp['message'] = 'No se proporcionó el token para eliminar la credencial'
            return JsonResponse(resp)


class InsigniasPersonales(APIView):

    def get(self, request, id, format=None):
        prov = Proveedor.objects.get(user_datos_id=id)
        profesion = prov.profesion
        cant_Servicios = prov.servicios

        print("Profesión del proveedor:", profesion)

        insignias_profesion = Insignia.objects.filter(servicio=profesion)
        print("Insignias relacionadas con la profesión:", insignias_profesion)

        if not insignias_profesion.exists():
            print("No se ha encontrado una insignia para esta profesión, creando nueva.")

            insigniaNueva = Insignia.objects.create(
                nombre="Insignia de Bienvenida",
                imagen="insignias/01.png",
                servicio=profesion,
                pedidos=0,
                descripcion="Bienvenidos a Vive Facil",
                tipo="Oficio",
                tipo_usuario="Proveedor",
            )
            insigniaNueva.save()
            print("Insignia creada con éxito para el proveedor:", insigniaNueva)

            list_of_ids = [insigniaNueva.id]
        else:
            list_of_ids = []

        for i in insignias_profesion:
            print("Verificando insignia:", i)
            if cant_Servicios >= i.pedidos and i.estado and profesion in i.servicio:
                list_of_ids.append(i.id)
                print("Insignia asignada:", i)

        medallasMostrar = Insignia.objects.filter(id__in=list_of_ids)
        serializer = InsigniaSerializer(medallasMostrar, many=True)
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

    def get(self, request, id,  format=None):
        utc=pytz.UTC
        print("AAAAAAAAAAAAAAAAAAAAAA")
        print(id)
        print("EEEEEEEEEEE")
        medallasTot = Medalla.objects.all().filter()
        print(medallasTot)
        dato = Datos.objects.get(id=id)
        print(dato)
        fechaDato=dato.fecha_creacion
        correoDato=dato.user.email
        list_of_ids = []
        for a in medallasTot:
            nuevotiempo= datetime.datetime.today() - timedelta(days=a.tiempo)
            if fechaDato<utc.localize(nuevotiempo) and dato.tramites>=a.cantidad and a.estado and dato.dinero_invertido>=a.valor:
                list_of_ids.append(a.id)
                medallaTiene=clientexmedalla.objects.filter(medalla=a, user=dato.user)
                if not medallaTiene:
                    medallaNueva= clientexmedalla.objects.create(medalla=a, user=dato.user)
                    dato.puntos=dato.puntos + a.puntos
                    dato.save()
                    medallaNueva.save()

        print("jeje")
        medallasMostrar=Medalla.objects.filter(id__in=list_of_ids)
        serializer = MedallaSerializer(medallasMostrar, many=True)
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

    def get(self, request, format=None):
        insignias = Insignia.objects.all().filter()
        serializer = InsigniaSerializer(insignias, many=True)
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

class Medallas(APIView):
    def get(self, request, format=None):
        medallas = Medalla.objects.filter(estado=True)
        medallas
        serializer = MedallaSerializer(medallas, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        nombre = request.POST.get('nombre')
        imagen = request.FILES.get('imagen')
        descripcion = request.POST.get('descripcion')
        tiempo = int(request.POST.get('tiempo'))
        valor = int(request.POST.get('valor'))
        cantidad = int(request.POST.get('cantidad'))
        medalla_creada = Medalla.objects.create(
            nombre=nombre, imagen=imagen, descripcion=descripcion, tiempo=tiempo, valor=valor, cantidad=cantidad)
        serializer = MedallaSerializer(medalla_creada)
        data['medalla'] = serializer.data
        if medalla_creada:
            return Response(data)
        else:
            data['error'] = "Error al crear una medalla!."
            return Response(data)

    def put(self, request, id, format=None):
        print("AAAAAAAAAAAAAAAA")
        medalla = Medalla.objects.get(id=id)
        serializer = MedallaSerializer(
            medalla, data=request.data, partial=True)
        if serializer.is_valid():
            print(serializer)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        insignia = Insignia.objects.get(id=id)
        insignia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class Insignia_Details(APIView):

    def get(self, request, pk, format=None):

        insignia = Insignia.objects.get(id=pk)
        serializer = InsigniaSerializer(insignia)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        insig = Insignia.objects.get(id=ident)
        insig.estado = request.data.get('estado')
        insig.save()
        return Response(status=status.HTTP_200_OK)

class Medalla_Details(APIView):

    def get(self, request, pk, format=None):

        insignia = Insignia.objects.get(id=pk)
        serializer = InsigniaSerializer(insignia)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        medalla = Medalla.objects.get(id=ident)
        print( "medalla.estado")
        print( medalla.estado)
        if medalla.estado == True:
            medalla.estado = False
        else:
            medalla.estado = True
        print( medalla.estado)
        medalla.save()
        return Response(status=status.HTTP_200_OK)


class InsigniasProveedor(APIView):

    def get(self, request, formt=None):
        insignias = Insignia.objects.all().filter(tipo_usuario="Proveedor")
        serializer = InsigniaSerializer(insignias, many=True)
        return Response(serializer.data)


class InsigniaSolicitantes(APIView):

    def get(self, request, formt=None):
        insignias = Insignia.objects.all().filter(tipo_usuario="Solicitante")
        serializer = InsigniaSerializer(insignias, many=True)
        return Response(serializer.data)


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

    def post(self, request, format=None):
        data = {}
        token = request.data.get('token')
        # device = FCMDevice.objects.filter(registration_id=token, active=True)
        device = FCMDevice.objects.filter(active=True,registration_id=token)
        if len(device) > 0:
            data['message'] = 'Token existente.'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        device = FCMDevice()
        device.registration_id = token
        device.active = True
        if request.user.is_authenticated:
            device.user = request.user
            device.save()
            data['message'] = 'Token guardado.'
            return Response(data)
        else:
            data['message'] = 'Usuario no identificado.'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        data = {}
        num_devices = 0
        correo = request.data.get('correo')
        devices = FCMDevice.objects.filter(active=True,user=correo)
        if len(devices) != 0:
            for device in devices:
                device.delete()
                num_devices += 1
            data['success'] = True
            data['message'] = 'Se han eliminado #' + num_devices + \
                ' de los dispositivos registrados con el correo' + correo
            return Response(data)
        else:
            data['success'] = False
            data['message'] = 'No se han encontrados dispositivos con el correo: ' + \
                correo + ' registrados en la base de datos'
            return Response(data)


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

class Email(APIView):

    def post(self, request, format=None):
        data = {}
        emails = []
        email_user = request.data.get('email')
        formatEmail = FormatEmail()
        user = Datos.objects.get(user__email=email_user)
        if user is not None:
            user.security_access = uuid.uuid4()
            user.save()
            emails.append(email_user)
            pass_user = request.data.get('password')
            asunto = 'Bienvenido a Vive Fácil'
            try:
                if (request.data.get('tipo') == "Administrador"):
                    thread = threading.Thread(target=formatEmail.send_email(emails, asunto, 'emails/welcomeAdmin.html', {
                                              "username": user.nombres + ' ' + user.apellidos, "user": email_user, "password": pass_user}))
                    thread.start()
                    data['success'] = True
                    data['clave'] = user.security_access
                    return Response(data)
                else:
                    thread = threading.Thread(target=formatEmail.send_email(emails, asunto, 'emails/welcomeProveedor.html', {
                                              "username": user.nombres + ' ' + user.apellidos, "user": email_user, "password": pass_user}))
                    thread.start()
                    data['success'] = True
                    data['clave'] = user.security_access
                    return Response(data)

            except:
                data['success'] = False
                return Response(data)
        else:
            data['success'] = False
            return Response(data)
        return Response(status=status.HTTP_200_OK)


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

class RecuperarPassword(APIView):
    def get(selt, request, user_email, format=None):
        data = {'success': False}
        # dato= Dato.objects.all().filter(id=id)
        usuario = User.objects.filter(email=user_email)
        if usuario.count() > 0:
            # se envia correo con codigo y se retorna true para dar pase a la pantalla donde se ingresa codigo
            user_dato = Datos.objects.get(user=usuario.first())
            if (user_dato is not None):
                data['success'] = True
        return Response(data)


class EnviarAlerta(APIView):
    def get(selt, request, user_email, asunto, texto, format=None):
        data = {'success': False}
        # dato= Dato.objects.all().filter(id=id)
        usuario = User.objects.filter(email=user_email)
        if usuario.count() > 0:
            # se envia correo con codigo y se retorna true para dar pase a la pantalla donde se ingresa codigo
            user_dato = Datos.objects.get(user=usuario.first())
            if (user_dato is not None):
                formatEmail = FormatEmail()
                thread = threading.Thread(target=formatEmail.send_email(
                    [user_email], asunto, 'emails/enviarAlerta.html', {"username": user_dato.nombres, "contenido": texto}))
                thread.start()
                data['success'] = True
        return Response(data)


class ValidarCodigo(APIView):
    def get(selt, request, email, codigo, format=None):
        data = {'success': False}
        usuario = User.objects.filter(email=email)
        if usuario.count() > 0:
            user_dato = Datos.objects.get(user=usuario.first())
            if (user_dato is not None):
                codigos = Codigos.objects.filter(
                    user_datos=user_dato, codigo=codigo, estado=True)
                if (codigos.count() > 0):
                    data['success'] = True
        return Response(data)


class CambioPasswordCodigo(APIView):
    def get(selt, request, email, password, codigo, format=None):
        data = {'success': False}
        usuario = User.objects.filter(email=email)
        if usuario.count() > 0:
            user_dato = Datos.objects.get(user=usuario.first())
            if (user_dato is not None):
                codigos = Codigos.objects.filter(
                    user_datos=user_dato, codigo=codigo, estado=True)
                if (codigos.count() > 0):
                    codigoFirst = codigos.first()
                    codigoFirst.estado = False
                    codigoFirst.save()

                    user = usuario.first()
                    user.set_password(password)
                    user.save()
                    data['success'] = True
        return Response(data)


class CambioContrasenia(APIView):
    def get(selt, request, email, password, format=None):
        data = {'success': False}
        try:
            usuario = User.objects.get(email=email)
        except Exception as e:
            data['success'] = False
            data['message'] = "El usuario con ese correo no fue encontrado en la base de datos: " + \
                str(e)

        try:
            user_dato = Datos.objects.get(user=usuario)
        except Exception as e:
            data['success'] = False
            data['message'] = "La tabla User Datos no fue enocontrada en la base de datos " + \
                str(e)

        if (user_dato is not None):
            usuario.set_password(password)
            usuario.save()
            data['success'] = True
            data['message'] = "Contrsaseña cambiada con exito"

        return Response(data)


class Categorias(APIView):

    def get(self, request, format=None):
        categorias = Categoria.objects.all().filter()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)

    def put(self, request, id, format=None):
        dataMensaje = {}
        categoria = Categoria.objects.get(id=id)
        serializer = CategoriaSerializer(
            categoria, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            estado = request.data.get("estado")
            if estado != None:
                # Notificacion a los usuarios
                titles = None
                bodys = None
                if estado == False:
                    titles = 'Categoría Desabilitada: '+categoria.nombre
                    bodys = '¡Sorry, volveremos pronto!'
                    dataMensaje["descripcion"] = "Lamentamos informarles que la Categoría " + \
                        categoria.nombre + " se encuentra fuera de servicio"
                    dataMensaje["ruta"] = "/main-tabs/home"
                else:
                    titles = 'Categoría Habilitada: '+categoria.nombre
                    bodys = '¡Hemos Vuelto!'
                    dataMensaje["descripcion"] = "Es de nuestro agrado informarles que la Categoría " + \
                        categoria.nombre + " ha regresado nuevamente a su servicio"
                    dataMensaje["ruta"] = "/main-tabs/home"

                # devices = FCMDevice.objects.filter(user__id = 542)
                devices = FCMDevice.objects.filter(
                    active=True, user__groups__name="Solicitante")
                tokend = devices.values_list('registration_id', flat=True)
                tokens=list(tokend)


                if tokend:
                    send_notificationF(tokens,titles,bodys,dataMensaje)
                else:
                    dataMensaje['message'] = 'No hay dispositivos registrados para enviar la notificación.'
                    dataMensaje['success'] = False
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        dataMensaje = {}
        categoria = Categoria.objects.get(id=id)
        servicios = Servicio.objects.filter(categoria=categoria)
        servicios.delete()
        categoria.delete()
        # Notificacion a los usuarios
        devices = FCMDevice.objects.filter(
            active=True, user__groups__name='Solicitante')
        tokend = devices.values_list('registration_id', flat=True)


        dataMensaje["descripcion"] = "Lamentamos informarles que la Categoría " + \
            categoria.nombre + " ha sido eliminada de la aplicación"
        dataMensaje["ruta"] = "/main-tabs/home"
        # Notificacion a los usuarios
        titles = "Categoría Eliminada: "+categoria.nombre
        bodys = "¡Sorry, no podrás acceder a la categoría!"
        tokens=list(tokend),  # Convertir a lista
        send_notificationF(tokens,titles,bodys,dataMensaje)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        data = {}

        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        foto_categoria = request.FILES.get('foto')

        categoria_creada = Categoria.objects.create(
            nombre=nombre, descripcion=descripcion, foto=foto_categoria, foto2=foto_categoria)
        serializer = CategoriaSerializer(categoria_creada)
        # Notificacion a los usuarios
        devices = FCMDevice.objects.filter(
            active=True, user__groups__name='Solicitante')
        # Obtiene la lista de registration_ids (tokens)
        tokend = devices.values_list('registration_id', flat=True)

        titles="Nueva Categoría: "+nombre
        bodys="¡Dale un vistazo!"
        data["ruta"] = "/main-tabs/home"
        data["descripcion"] = "Vive Fácil cuenta con una nueva Categoría llamada " + categoria_creada.nombre
        tokens=list(tokend),
        if tokend:
            send_notificationF(tokens,titles,bodys,data)

        data['categoria'] = serializer.data
        if categoria_creada:
            return Response(data)
        else:
            data['error'] = "Error al crear!."
            return Response(data)


class Servicios(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, format=None):
        servicios = Servicio.objects.all().filter(estado = True)
        serializer = ServicioSerializer(servicios, many=True)
        return Response(serializer.data)

    def put(self, request, id, format=None):
        servicios = Servicio.objects.get(id=id)
        profesion = Profesion.objects.get_or_create(nombre=servicios.nombre)
        profesion = Profesion.objects.get(nombre=servicios.nombre)
        serializer = ServicioSerializer(
            servicios, data=request.data, partial=True)
        print("hasta aca llega0")
        if serializer.is_valid():
            serializer.save()
            print("hasta aca llega")
            servicios2 = Servicio.objects.get(id=id)
            print("hasta aca llega2")
            profesion.nombre=servicios2.nombre
            print("hasta aca llega3")
            profesion.foto=servicios2.foto
            print("hasta aca llega4")
            profesion.descripcion=servicios2.descripcion
            print("hasta aca llega5")
            profesion.save()
            print("hasta aca llega6")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        data = {}
        servicios = Servicio.objects.get(id=id)
        nombreServico = servicios.nombre
        servicios.estado = 0
        servicios.save()
        #servicios.delete()
        # Notificacion a los usuarios
        devices = FCMDevice.objects.filter(
            active=True, user__groups__name='Solicitante')
        tokend = devices.values_list('registration_id', flat=True)
        tokens=list(tokend)
        titles="Servicio Eliminado: " + nombreServico
        bodys="¡Sorry, no podrás acceder al Servicio!"
        data["ruta"] = "/main-tabs/home"
        data["descripcion"] = "El servicio " + nombreServico + " se ha eliminado de nuestro aplicativo"
        # Verifica que haya tokens para enviar
        if tokend:
            send_notificationF(tokens,titles,bodys,data)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        data = {}
        nombre = request.POST.get('nombre')
        servicio = Servicio.objects.filter(nombre=nombre)
        if (len(servicio) > 0):
            data['error'] = "Ya existe el servicio con el mismo nombre"
            return Response(data)

        descripcion = request.POST.get('descripcion')
        categoria = Categoria.objects.get(nombre=request.POST.get('categoria'))
        foto = request.FILES.get('foto')
        servicio_creado = Servicio.objects.create(
            nombre=nombre, descripcion=descripcion, categoria=categoria, foto=foto)
        serializer = ServicioSerializer(servicio_creado)
        data['servicio'] = serializer.data
        profesionCreada = Profesion.objects.create(
            nombre=nombre, descripcion=descripcion, foto=foto)
        profesionCreada.save()
        if servicio_creado:
            # Notificacion a los usuarios

            devices = FCMDevice.objects.filter(
                 active=True, user__groups__name="Solicitante")
            tokend = devices.values_list('registration_id', flat=True)
            tokens=list(tokend)
            titles="Nuevo Servicio: "+nombre,
            bodys="¡Dale un vistazo!",
            dataNot={
                  "ruta": "/main-tabs/home",
                  "descripcion": "El servicio " + nombre + " se ha agregado a nuestro aplicativo",
            },

            send_notificationF(tokens,titles,bodys,dataNot)

            return Response(data)

        else:
            data['error'] = "Error al crear!."
            return Response(data)


class Logout(APIView):
    # authentication_class = (TokenAuthentication)
    def get(self, request, *args, **kwargs):
        token = Token.objects.get(key=self.kwargs["token"])
        token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)


class RegistroFromRedes(APIView):
    def post(self, request, user, formato=None):
        usuario = User.objects.get(email=user)
        email = FormatEmail()
        if usuario:
            nombre_user = request.data.get('nombres')
            apellido_user = request.data.get('apellidos')
            telefono_user = request.data.get('telefono')
            ciudad_user = request.data.get('ciudad')
            cedula_user = request.data.get('cedula')
            foto_user = request.FILES.get('foto')
            usuario.username = user
            usuario.set_password(request.data.get('password'))
            usuario.save()
            try:
                dato, creado = Datos.objects.get_or_create(user=usuario, tipo=models.Group.objects.get(
                    name='Solicitante'), nombres=nombre_user, apellidos=apellido_user, telefono=telefono_user, foto=foto_user, ciudad=ciudad_user, cedula=cedula_user)
                if creado:
                    # thread = threading.Thread(target =email.send_email(user,'Bienvenido a TOME','emails/welcome.html',{"username":nombre_user}))
                    # thread.start()
                    Solicitante.objects.create(
                        user_datos=dato, bool_registro_completo=True)
                    return Response(status=status.HTTP_200_OK)
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class Registro(viewsets.ModelViewSet):
    serializer_class = DatosSerializer
    queryset = Datos.objects.all()

    def create(self, request, *args, **kwargs):
        print("Hora de crear un nuevo usuario")
        user_email = request.POST.get('email')
        user_password = request.POST.get('password')
        users = User.objects.filter(username=user_email).count()
        data = {}
        email = FormatEmail()
        if (users == 0):
            usuario = User.objects.create_user(email=request.POST.get('email'), username=request.POST.get('email'), password=user_password)
            tipo_user = request.POST.get('tipo')
            nombre_user = request.POST.get('nombres')
            apellido_user = request.POST.get('apellidos')
            telefono_user = request.POST.get('telefono')
            genero_user = request.POST.get('genero')
            ciudad_user = request.POST.get('ciudad')
            cedula_user = request.POST.get('cedula')
            foto_user = request.FILES.get('foto')
            print(foto_user)
            print("nombre_user: " + nombre_user)
            try:
                dato, creado = Datos.objects.get_or_create(user=usuario, tipo=models.Group.objects.get(
                    name=tipo_user), nombres=nombre_user, apellidos=apellido_user, telefono=telefono_user, genero=genero_user, ciudad=ciudad_user, cedula=cedula_user, foto=foto_user)
                # data['error1']=dato.user.email
                if creado:
                    # thread = threading.Thread(target =email.send_email(user_email,'Bienvenido a TOME','emails/welcome.html',{"username":nombre_user}))
                    # thread.start()
                    # data['error2']=dato.user.email
                    if tipo_user == 'Solicitante':
                        Solicitante.objects.create(
                            user_datos=dato, bool_registro_completo=True)
                        grupoSolicitante = Group.objects.get(
                            name='Solicitante')
                        grupoSolicitante.user_set.add(usuario)
                        asunto = 'Bienvenido a Vive Fácil'
                        formatEmail = FormatEmail()
                        thread = threading.Thread(target=formatEmail.send_email([user_email], asunto, 'emails/welcome.html', {"username":nombre_user}))
                        thread.start()
                    elif tipo_user == 'Proveedor':
                        # Proveedor.objects.create(user_datos= dato, bool_registro_completo= True)
                        try:
                            proveedor_user, created = Proveedor.objects.get_or_create(user_datos=dato, ano_profesion=0, profesion = request.POST.get('profesion'))
                            # pendiente, created_p = Proveedor_Pendiente.get_or_create(proveedor=proveedor_user, email = request.data.get('email'))
                            print("Proveedor email: " + proveedor_user.user_datos.user.email)
                            print("Proveedor trabalho: " + proveedor_user.profesion)

                        except:
                            print("No se pudo crear el perfil de proveedor 1")
                            data['error'] = "No se pudo crear el perfil de proveedor 1"
                            data['success'] = False
                            return Response(data)
                        else:
                            try:
                                #trabajo
                                print("trabalho?")
                                profesiones_lista = request.POST.get('profesion').split(',')
                                for profesion in profesiones_lista:
                                    profesion_obnj = Profesion.objects.get(nombre=profesion)
                                    profesion_proveedor = Profesion_Proveedor.objects.create(proveedor=proveedor_user, profesion=profesion_obnj,ano_experiencia=request.POST.get('ano_experiencia'))
                                print("trabalho!!!!!!")
                                # crear cuenta
                                banco_user = Banco.objects.get_or_create(nombre=request.POST.get('banco'))
                                tipo_cuenta_user = Tipo_Cuenta.objects.get_or_create(nombre=request.POST.get('tipo_cuenta'))
                                numero_account = request.POST.get('numero_cuenta')
                                cuenta = Cuenta.objects.get_or_create(banco=banco_user[0], tipo_cuenta=tipo_cuenta_user[0], proveedor=proveedor_user, numero_cuenta=numero_account)
                                proveedor_user.banco = request.POST.get('banco')
                                proveedor_user.numero_cuenta = numero_account
                                proveedor_user.tipo_cuenta = request.POST.get('tipo_cuenta')
                                print(request.POST.get('descripcion'))
                                print(request.POST.get('ano_experiencia'))
                                print(request.POST.get('licencia'))
                                print(request.POST.get('direccion'))
                                # Descripcion llega como none, cuando este arreglado descomentar la linea de abajo
                                proveedor_user.descripcion = request.POST.get('descripcion')
                                proveedor_user.ano_profesion = request.POST.get('ano_experiencia')
                                proveedor_user.licencia = request.POST.get('licencia')
                                proveedor_user.direccion = request.POST.get('direccion')

                                #No llegan los documentos ni la foto

                                documents = request.POST.getlist('filesDocuments')
                                print("He aqui los documentos")
                                if 'filesDocuments' in request.POST:
                                    doc = Document.objects.create(documento=request.POST.get('filesDocuments')[7:])
                                    print("Document", doc)
                                    print("Entra aqui")
                                    filesDocuments = request.POST.get('filesDocuments')
                                    print("Document", filesDocuments)
                                    print("Aqui tambien")
                                    arrayfilesDocuments=[doc]
                                    print("memento sql")
                                    proveedor_user.document.set(arrayfilesDocuments)
                                    print("Document", arrayfilesDocuments)
                                if 'foto' in request.POST:
                                    foto_user = request.POST.get('foto')[7:]
                                    proveedor_user.user_datos.foto = foto_user
                                    print(foto_user, "foto")
                                    print(proveedor_user.user_datos.foto, "proveedor_user.user_datos.foto")
                                if 'copiaCedula' in request.POST:
                                    copiaCedula = request.POST.get('copiaCedula')
                                    proveedor_user.copiaCedula = copiaCedula[7:]
                                    print(copiaCedula, "COPIA CEDULA")
                                if 'copiaLicencia' in request.POST:
                                    copiaLicencia = request.POST.get('copiaLicencia')
                                    proveedor_user.copiaLicencia = copiaLicencia[7:]
                                    print(copiaLicencia, "COPIA LICencia")
                                proveedor_user.save()
                                proveedor_user.user_datos.save()
                                data['success'] = True
                                asunto = "Solicitud Aceptada"
                                formatEmail = FormatEmail()
                                thread = threading.Thread(target=formatEmail.send_email([user_email], asunto, 'emails/formularioAceptado.html', {
                                                                      "username": nombre_user + ' ' + apellido_user, "user": user_email, "password": user_password}))
                                return Response(data)
                            except:
                                data['error'] = "No se pudo guardar la cuenta del usuario"
                                data['success'] = False
                                return Response(data)
                    data['email'] = dato.user.email
                    data['username'] = dato.user.username
                    token = Token.objects.get(user=dato.user).key
                    data['token'] = token
                    return Response(data)
                else:
                    data['error'] = "Esta persona ya existe1!."
                    return Response(data)
            except:
                data['error'] = "Esta persona ya existe2!."
                return Response(data)
        else:
            data['error'] = "Usuario ya existente!."
            return Response(data)


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class Register_Proveedor(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def post(self, request, format=None):
        data = {}

        serializer_class = DatosSerializer
        queryset = Datos.objects.all()
        user_email = request.POST.get('email')
        password_user = User.objects.make_random_password()
        usuario = User.objects.filter(username=user_email).count()
        data = {}
        email = FormatEmail()
        if not (usuario):
            usuario = User.objects.create_user(
                email=user_email, username=user_email, password=password_user)
            tipo_user = request.POST.get('tipo')
            nombre_user = request.POST.get('nombres')
            apellido_user = request.POST.get('apellidos')
            telefono_user = request.POST.get('telefono')
            genero_user = request.POST.get('genero')
            foto_user = request.FILES.get('foto')
            data["nombre"] = nombre_user
            data["apellido"] = apellido_user
            data["telefono"] = telefono_user
            data["genero"] = genero_user
            data["foto"] = foto_user
            data["email"] = user_email
            data["pass"] = password_user

            # try:
            dato, creado = Datos.objects.get_or_create(user=usuario, tipo=models.Group.objects.get(
                name='Proveedor'), nombres=nombre_user, apellidos=apellido_user, telefono=telefono_user, genero=genero_user, foto=foto_user)
            # data['error1']=dato.user.email
            if creado:
                thread = threading.Thread(target =email.send_email(user_email,'Bienvenido a Vive Fácil','emails/welcome.html',{"username":nombre_user}))
                thread.start()
                # data['error2']=dato.user.email
                if tipo_user == 'Proveedor':
                    Proveedor.objects.create(
                        user_datos=dato, bool_registro_completo=True)
                data['email'] = dato.user.email
                data['username'] = dato.user.username
                token = Token.objects.get(user=dato.user).key
                data['token'] = token
                return Response(data)
            else:
                data['error'] = "Esta persona ya existe1!."
                return Response(data)
            # except:
            #     data['error'] = "Esta persona ya existe2!."
            #     return Response(data)
        else:
            data['error'] = "Usuario ya existente!."
            return Response(data)


class Update_Proveedor_Pendiente(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def post(self, request, format=None):
        data = {}

        if request.data.get('tipo_user') != 'Proveedor_Pendiente':
            data['error'] = "El usuario no corresponde a Proveedor"
            data['success'] = False
            return Response(data)

        # id de user_datos en proveedor
        data_user = request.data.get('user_datos')
        proveedor_id = request.data.get('proveedor_id')  # id del proveedor
        pendiente_id = request.data.get(
            'pendiente_id')  # id del prveedor pendiente
        banco_name = request.data.get('banco')
        tipo_cuenta_user = request.data.get('tipo_cuenta')
        numero_cuenta_user = request.data.get('numero_cuenta')
        profesion_user = request.data.get('profesion')
        experiencia = request.data.get('ano_experiencia')
        nombre_user = request.data.get('nombres')
        apellido_user = request.data.get('apellidos')
        telefono_user = request.data.get('telefono')
        cedula_user = request.data.get('cedula')
        email_user = request.data.get('email')

        # obtener los objetos para actualizarlos
        try:
            data['code'] = 1
            dato = Datos.objects.get(id=data_user)
            data['code'] = 2
            proveedor = Proveedor.objects.get(id=proveedor_id)
            data['code'] = 3
            proveedor_pendiente = Proveedor_Pendiente.objects.get(
                id=pendiente_id)

        except:
            data['error'] = "No se pudo obtener la informacion del perfil"
            data['success'] = False
            return Response(data)
        else:

            data['code'] = 4
            # actualizar la informacion
            dato.nombres = nombre_user
            dato.apellidos = apellido_user
            dato.telefono = telefono_user
            dato.cedula = cedula_user
            dato.save()

            # actualizar info proveedor pendiente
            data['code'] = 5

            proveedor_pendiente.banco = banco_name
            proveedor_pendiente.numero_cuenta = numero_cuenta_user
            proveedor_pendiente.tipo_cuenta = tipo_cuenta_user
            proveedor_pendiente.email = email_user
            proveedor_pendiente.profesion = profesion_user
            proveedor_pendiente.ano_experiencia = experiencia

            proveedor_pendiente.save()

            data['success'] = True
            return Response(data)


class Cupones_Aplicados(APIView):

    def post(self, request, format=None):
        data = {}
        cupon_dat = request.data.get('cupon')
        user_dat = request.data.get('user')
        estado_dat = request.data.get('estado')
        cup_id = request.data.get('cupon_id')
        try:
            cupon_apl = Cupon_Aplicado.objects.filter(
                user=user_dat, cupon__id=cup_id)
            if not (cupon_apl):
                cupon_1 = Cupon.objects.get(id=cup_id)
                data['cr'] = True
                usuario = Datos.objects.get(user__email=user_dat)
                usuario.puntos = usuario.puntos - cupon_1.puntos
                cupon_1.cantidad = cupon_1.cantidad - 1
                if usuario.puntos < 0:
                    data['valid'] = "puntos"
                    data['creado'] = False
                elif cupon_1.cantidad+1 <=0:
                    data['valid'] = "cantidad"
                    data['creado'] = False
                else:
                    usuario.save()
                    cupon_1.save()
                    cup_create, creado = Cupon_Aplicado.objects.get_or_create(cupon=Cupon.objects.get(id=cup_id), user=user_dat, estado=estado_dat)
                    data['creado'] = True
            else:
                data['creado'] = False

            data['success'] = True
        except:
            data['error'] = "No se pudo adjudicar el cupon"
            data['success'] = False
            data['user'] = user_dat
            data['cupon'] = cupon_dat

            return Response(data)
        else:
            return Response(data)

    def put(self, request, formato=None):
        user_dat = request.data.get('user')
        cup_id = request.data.get('cupon_id')
        cupon_aplic = Cupon_Aplicado.objects.filter(
            user=user_dat, cupon=Cupon.objects.get(id=cup_id))
        if cupon_aplic:
            estado_dat = request.data.get('estado')
            cupon_aplic.estado = estado_dat
            cupon_aplic.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class Get_Cupon_Aplicado(APIView):
    def get(self, request, user, format=None):
        cupon_aplicado = Cupon_Aplicado.objects.all().filter(user=user)
        serializer = Cupon_AplicadoSerializer(cupon_aplicado, many=True)
        return Response(serializer.data)


class Data_Proveedor_Pendiente(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def post(self, request, format=None):
        data = {}
        print("ESTE")
        if request.data.get('tipo') != 'Proveedor_Pendiente':
            data['error'] = "El tipo de usuario no es un Proveedor Pendiente"
            return Response(data)

        usuario = User.objects.filter(
            username=request.data.get('email')).count()
        if not (usuario):
            tipo_user = request.data.get('tipo')
            nombre_user = request.data.get('nombres')
            apellido_user = request.data.get('apellidos')
            telefono_user = request.data.get('telefono')
            genero_user = request.data.get('genero')
            foto_user = request.data.get('foto')
            ciudad_user = request.data.get('ciudad')
            cedula_user = request.data.get('cedula')

            try:
                dato, creado = Datos.objects.get_or_create(tipo=models.Group.objects.get(
                    name=tipo_user), nombres=nombre_user, apellidos=apellido_user, telefono=telefono_user, genero=genero_user, foto=foto_user, ciudad=ciudad_user, cedula=cedula_user)
            except:
                data['error'] = "No se pudo guardar los datos"
                data['success'] = False
                return Response(data)
            else:
                # Crear la cuenta y el proveedor
                descripcion_user = request.data.get('descripcion')
                docs = request.data.get('documentos')  # Array

                try:
                    proveedor_user, created = Proveedor.objects.get_or_create(
                        user_datos=dato, descripcion=descripcion_user)
                    pendiente, created_p = Proveedor_Pendiente.get_or_create(
                        proveedor=proveedor_user, email=request.data.get('email'))

                except:
                    data['error'] = "No se pudo crear el perfil de proveedor 2"
                    data['success'] = False
                    return Response(data)

                else:
                    try:
                        # crear cuenta
                        banco_user = Banco.objects.get_or_create(
                            nombre=request.data.get('banco'))
                        tipo_cuenta_user = Tipo_Cuenta.objects.get_or_create(
                            nombre=request.data.get('tipo_cuenta'))
                        numero_account = request.data.get('numero_cuenta')

                        cuenta = Cuenta.objects.get_or_create(
                            banco=banco_user, tipo_cuenta=tipo_cuenta_user, proveedor=proveedor_user, numero_cuenta=numero_account)

                        serializer_cuenta = CuentaSerializer(cuenta)
                        serializer_pendiente = Proveedor_PendienteSerializer(
                            pendiente)

                        data['cuenta'] = serializer_cuenta.data
                        data['pendiente'] = serializer_pendiente.data
                        data['success'] = False
                        return Response(data)

                    except:
                        data['error'] = "No se pudo guardar la cuenta del usuario"
                        data['success'] = False
                        return Response(data)
        else:
            data['error'] = "El usuario ya existe"
            data['success'] = False
            return Response(data)

    def delete(self, request, format=None):
        print("In process")


class Data_Proveedor_Proveedor(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def post(self, request, format=None):
        data = {}
        '''if request.data.get('tipo')!='Proveedor_Pendiente':
            data['error']="El tipo de usuario no es un Proveedor Pendiente"
            return Response(data)'''
        usuario = User.objects.filter(
            username=request.data.get('email')).count()
        if not (usuario):
            tipo_user = request.data.get('tipo')
            nombre_user = request.data.get('nombres')
            apellido_user = request.data.get('apellidos')
            telefono_user = request.data.get('telefono')
            genero_user = request.data.get('genero')
            foto_user = request.data.get('foto')
            ciudad_user = request.data.get('ciudad')
            cedula_user = request.data.get('cedula')
            # usuarioNovo =
            try:
                dato, creado = Datos.objects.get_or_create(tipo=models.Group.objects.get(name="Proveedor"), nombres=nombre_user, apellidos=apellido_user,
                                                           telefono=telefono_user, genero=genero_user, foto=foto_user, ciudad=ciudad_user, cedula=cedula_user)  # , user = usuarioNovo'''
            except:
                data['error'] = "No se pudo guardar los datos"
                data['success'] = False
                return Response(data)
            else:
                # Crear la cuenta y el proveedor
                descripcion_user = request.data.get('descripcion')
                # docs = request.data.get('documentos') #Array, aun no incluido
                try:
                    proveedor_user, created = Proveedor.objects.get_or_create(
                        user_datos=dato, descripcion=descripcion_user, ano_profesion=0)
                    # pendiente, created_p = Proveedor_Pendiente.get_or_create(proveedor=proveedor_user, email = request.data.get('email'))
                except:
                    data['error'] = "No se pudo crear el perfil de proveedor 3"
                    data['success'] = False
                    return Response(data)
                else:
                    try:
                        # crear cuenta
                        banco_user = Banco.objects.get_or_create(
                            nombre=request.data.get('banco'))
                        tipo_cuenta_user = Tipo_Cuenta.objects.get_or_create(
                            nombre=request.data.get('tipo_cuenta'))
                        numero_account = request.data.get('numero_cuenta')
                        cuenta = Cuenta.objects.get_or_create(
                            banco=banco_user[0], tipo_cuenta=tipo_cuenta_user[0], proveedor=proveedor_user, numero_cuenta=numero_account)
                        proveedor_user.banco = banco_user[0]
                        proveedor_user.numero_cuenta = "0999990999999"
                        proveedor_user.profesion = "si"
                        # serializer_cuenta = CuentaSerializer(cuenta)
                        # serializer_pendiente = Proveedor_PendienteSerializer(pendiente)

                        # data['cuenta']= serializer_cuenta.data
                        # data['pendiente']= serializer_pendiente.data
                        data['success'] = True
                        return Response(data)
                    except:
                        data['error'] = "No se pudo guardar la cuenta del usuario"
                        data['success'] = False
                        return Response(data)
        else:
            data['error'] = "El usuario ya existe"
            data['success'] = False
            return Response(data)

    def delete(self, request, format=None):
        print("In process")

# Registrar al proveedor desde la pagina web


class Proveedor_Pendiente_Admin(APIView, MyPaginationMixin):

    queryset = Proveedor_Pendiente.objects.all().order_by('-id')
    serializer_class = Proveedor_PendienteSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
    # def get(self, request, format=None):
    #     proveedor_pendiente = Proveedor_Pendiente.objects.all().filter()
    #     serializer = Proveedor_PendienteSerializer(proveedor_pendiente, many=True)

        # print(JSONRenderer().render(serializer.data))
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        nombres_prov = request.data.get('nombres')
        apellidos_prov = request.data.get('apellidos')
        genero_prov = request.data.get('genero')
        telefono_prov = request.data.get('telefono')
        cedula_prov = request.data.get('cedula')
        cedula_copia = request.FILES.get('copiaCedula')
        ciudad_prov = request.data.get('ciudad')
        direccion_prov = request.data.get('direccion')
        email_prov = request.data.get('email')
        descripcion = request.data.get('descripcion')
        licencia = request.data.get('licencia')
        licencia_copia = request.FILES.get('copiaLicencia')
        profesion_prov = request.data.get('profesion')
        ano_experiencia_prov = request.data.get('ano_experiencia')
        banco_prov = request.data.get('banco')
        numero_cuenta_prov = request.data.get('numero_cuenta')
        tipo_cuenta_prov = request.data.get('tipo_cuenta')
        foto_prov = request.data.get('foto')
        documentos = request.FILES.getlist('filesDocuments')
        data['data'] = {nombres_prov}

        proveedor_pend = Proveedor_Pendiente.objects.create(nombres=nombres_prov, apellidos=apellidos_prov, genero=genero_prov, telefono=telefono_prov, cedula=cedula_prov, copiaCedula=cedula_copia, ciudad=ciudad_prov, direccion=direccion_prov,
                                                            email=email_prov, licencia=licencia, copiaLicencia=licencia_copia, profesion=profesion_prov, ano_experiencia=ano_experiencia_prov, banco=banco_prov, numero_cuenta=numero_cuenta_prov,
                                                            tipo_cuenta=tipo_cuenta_prov, descripcion=descripcion, foto=foto_prov)
        prov_pendiente = Proveedor_Pendiente.objects.get(id=proveedor_pend.id)
        for doc in documentos:

            documento_creado = PendienteDocuments.objects.create(document=doc)
            prov_pendiente.documentsPendientes.add(documento_creado)

        serializer = Proveedor_PendienteSerializer(proveedor_pend)

        data['success'] = True
        data['serializer'] = serializer.data
        asunto = "Solicitud Enviada"
        formatEmail = FormatEmail()
        thread = threading.Thread(target=formatEmail.send_email([email_prov], asunto, 'emails/formularioEnviado.html', {
                                              "username": nombres_prov + ' ' + apellidos_prov, "user": email_prov}))

        return Response(data)
        # try:
        #     proveedor_pend = Proveedor_Pendiente.objects.create(nombres= nombres_prov, apellidos= apellidos_prov, genero= genero_prov,telefono= telefono_prov,cedula=cedula_prov, copiaCedula = cedula_copia, ciudad= ciudad_prov, direccion= direccion_prov , estado = estado_prov, email= email_prov, licencia= licencia, copiaLicencia= licencia_copia,profesion=profesion_prov,ano_experiencia=ano_experiencia_prov, banco= banco_prov, numero_cuenta= numero_cuenta_prov, tipo_cuenta= tipo_cuenta_prov,planilla_servicios=planilla_servicios_prov)
        #     serializer=Proveedor_PendienteSerializer(proveedor_pend)
        #     data['success']=True
        #     data['serializer']=serializer.data
        # except:
        #         # data['error']="No se pudo crear el perfil de proveedor"
        #         # data['success']= False
        #         # return Response(data)return
        #         return Response(status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     return Response(data)

class Proveedores_Pendientes_Email(APIView):

    def get(self, request, mail, format=None):
        try:
            administrador = Proveedor_Pendiente.objects.get(email=mail)
            serializer = Proveedor_PendienteSerializer(administrador)
            return Response(serializer.data)
        except:
            return Response("nuevo")

class Proveedores_Pendientes_Details(APIView):

    def get(self, request, pk, format=None):

        administrador = Proveedor_Pendiente.objects.get(id=pk)
        serializer = Proveedor_PendienteSerializer(administrador)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        copiaCedula = request.data.get('copiaCedula')
        copiaLicencia = request.data.get('copiaLicencia')
        filesDocuments = request.data.get('filesDocuments')
        foto = request.data.get('foto')
        documents = request.FILES.getlist('filesDocuments')

        print("Pendiente original")
        print(pendiente)
        print("Datos ingresados")
        print(request.data)
        if not copiaCedula == None:
            pendiente.copiaCedula.delete()

        if not copiaLicencia == None:
            pendiente.copiaLicencia.delete()

        if not foto == None:
            pendiente.foto.delete()

        for doc in documents:
            documento_creado = PendienteDocuments.objects.create(document=doc)
            pendiente.documentsPendientes.add(documento_creado)
        pendiente.fecha_registro=timezone.now()
        serializer = Proveedor_PendienteSerializer(pendiente, data=request.data, partial=True)
        if 'foto' in request.FILES:
            foto_user = request.FILES.get('foto')
            serializer.foto = foto_user
        if 'copiaCedula' in request.FILES:
            copiaCedula = request.FILES.get('copiaCedula')
            serializer.copiaCedula = copiaCedula
        if 'copiaLicencia' in request.FILES:
            copiaLicencia = request.FILES.get('copiaLicencia')
            serializer.copiaLicencia = copiaLicencia
        if 'filesDocuments' in request.FILES:
            filesDocuments = request.FILES.get('filesDocuments')
            arrayfilesDocuments=[filesDocuments]
            serializer.documentsPendientes = arrayfilesDocuments
        print(copiaCedula)
        print(copiaLicencia)
        print(filesDocuments)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):

        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        # documentos = pendiente.documentsPendientes.all()
        # if not pendiente.copiaCedula == None:
        #     pendiente.copiaCedula.delete()
        # if not pendiente.copiaLicencia == None:
        #     pendiente.copiaLicencia.delete()
        # for doc in documentos:
        #     document = PendienteDocuments.objects.get(id=doc.id)
        #     document.delete()
        pendiente.estado = 1

        pendiente.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class Proveedores_Pendientes_Estado(APIView):

    def put(self, request):
        ident = request.GET.get('id')
        prov = Proveedor_Pendiente.objects.get(id=ident)
        prov.estado = 1
        prov.save()
        return Response(status=status.HTTP_200_OK)

class Proveedores_Pendientes_Details2(APIView):

    def put(self, request, pk, format=None):

        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        razon = request.data.get('razon')
        pendiente.estado = 1
        pendiente.rechazo = razon
        pendiente.save()
        asunto = "Solicitud Rechazada"
        formatEmail = FormatEmail()
        thread = threading.Thread(target=formatEmail.send_email([pendiente.email], asunto, 'emails/formularioRechazado.html', {
                                              "username": pendiente.nombres + ' ' + pendiente.apellidos, "user": pendiente.email, "razon": razon}))
        return Response(status=status.HTTP_204_NO_CONTENT)

class Proveedores_Rechazado_Estado(APIView):

    def put(self, request):
        ident = request.GET.get('id')
        prov = Proveedor_Pendiente.objects.get(id=ident)
        prov.estado = 1
        prov.save()
        return Response(status=status.HTTP_200_OK)

class Proveedores_Proveedores_Details(APIView):

    def get(self, request, pk, format=None):

        administrador = Proveedor_Pendiente.objects.get(id=pk)
        serializer = Proveedor_PendienteSerializer(administrador)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        print("dime si entra")
        pendiente = Proveedor.objects.get(id=pk)
        copiaCedula = request.data.get('copiaCedula')
        copiaLicencia = request.data.get('copiaLicencia')
        filesDocuments = request.data.get('filesDocuments')
        foto = request.data.get('foto')
        documents = request.FILES.getlist('filesDocuments')

        print("Pendiente original")
        print(pendiente)
        print("Datos ingresados")
        print(request.data)
        if not copiaCedula == None:
            pendiente.copiaCedula.delete()

        if not copiaLicencia == None:
            pendiente.copiaLicencia.delete()

        # if not foto == None:
        #     pendiente.foto.delete()

        for doc in documents:
            print("Document", doc)
            documento_creado = Document.objects.create(documento=doc)
            pendiente.document.add(documento_creado)
        if 'user_datos' in request.data:
            user_datos_str = request.data['user_datos']
            user_datos = json.loads(user_datos_str) if isinstance(user_datos_str, str) else user_datos_str

            # Actualizar los campos de 'user_datos'
            pendiente.user_datos.nombres = user_datos.get('nombres')
            pendiente.user_datos.apellidos = user_datos.get('apellidos')
            pendiente.user_datos.cedula = user_datos.get('cedula')
            pendiente.user_datos.ciudad = user_datos.get('ciudad')
            pendiente.user_datos.telefono = user_datos.get('telefono')
            pendiente.user_datos.genero = user_datos.get('genero')
            pendiente.user_datos.foto = foto or pendiente.user_datos.foto
            pendiente.user_datos.fecha_creacion = timezone.now()
            pendiente.user_datos.save()
        serializer = ProveedorSerializer(pendiente, data=request.data, partial=True)
        if 'foto' in request.FILES:
            foto_user = request.FILES.get('foto')
            serializer.foto = foto_user
            print(foto_user, "foto")
        if 'copiaCedula' in request.FILES:
            copiaCedula = request.FILES.get('copiaCedula')
            serializer.copiaCedula = copiaCedula
            print(copiaCedula, "COPIA CEDULA")
        if 'copiaLicencia' in request.FILES:
            copiaLicencia = request.FILES.get('copiaLicencia')
            serializer.copiaLicencia = copiaLicencia
            print(copiaLicencia, "COPIA LICencia")
        if 'filesDocuments' in request.FILES:
            filesDocuments = request.FILES.get('filesDocuments')
            arrayfilesDocuments=[filesDocuments]
            serializer.document = arrayfilesDocuments
            print(filesDocuments, "FILE DOCS")

        profesiones_lista = request.POST.get('profesion').split(',')
        print("trabalho?", profesiones_lista)
        if(profesiones_lista):
            Profesion_Proveedor.objects.all().filter(proveedor = pendiente).delete()
            for profesion in profesiones_lista:
                profesion_obnj_lista = Profesion.objects.filter(nombre=profesion)
                if(profesion_obnj_lista):
                    profesion_obnj = Profesion.objects.get(nombre=profesion)
                    #Comentado porque ano_experiencia no se guarda por lo que qeda como null y sale error, al arreglar descomentar la linea y comentar la que esta abajo de esta
                    #profesion_proveedor = Profesion_Proveedor.objects.get_or_create(proveedor=pendiente, profesion=profesion_obnj,ano_experiencia=request.POST.get('ano_experiencia'))
                    profesion_proveedor = Profesion_Proveedor.objects.get_or_create(proveedor=pendiente, profesion=profesion_obnj)

            print("trabalho!!!!!!")
            serializer.profesion = request.POST.get('profesion').split(',')
        pendiente.user_datos.save()
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):

        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        # documentos = pendiente.documentsPendientes.all()
        # if not pendiente.copiaCedula == None:
        #     pendiente.copiaCedula.delete()
        # if not pendiente.copiaLicencia == None:
        #     pendiente.copiaLicencia.delete()
        # for doc in documentos:
        #     document = PendienteDocuments.objects.get(id=doc.id)
        #     document.delete()
        pendiente.estado = 1

        pendiente.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProveedorDeleteView(APIView):
    def delete(self, request, proveedor_id):
        # Obtener el proveedor
        proveedor = get_object_or_404(Proveedor, id=proveedor_id)

        # Usar una transacción para asegurar que las eliminaciones se realicen de manera atómica
        with transaction.atomic():
            # Eliminar los Envio_Interesados asociados
            Envio_Interesados.objects.filter(solicitud__proveedor=proveedor).delete()

            # Eliminar las solicitudes asociadas al proveedor
            solicitudes_eliminadas = Solicitud.objects.filter(proveedor=proveedor).delete()

            # Eliminar el proveedor
            proveedor.delete()

        # Respuesta exitosa
        return Response({
            "message": "Proveedor, solicitudes y envíos eliminados exitosamente.",
            "solicitudes_eliminadas": solicitudes_eliminadas[0],
        }, status=status.HTTP_204_NO_CONTENT)


class Proveedores_Rechazados_Details(APIView):

    def get(self, request, pk, format=None):

        administrador = Proveedor_Pendiente.objects.get(id=pk)
        serializer = Proveedor_PendienteSerializer2(administrador)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        copiaCedula = request.data.get('copiaCedula')
        copiaLicencia = request.data.get('copiaLicencia')
        documents = request.FILES.getlist('filesDocuments')

        if not copiaCedula == None:
            pendiente.copiaCedula.delete()

        if not copiaLicencia == None:
            pendiente.copiaLicencia.delete()

        for doc in documents:
            documento_creado = PendienteDocuments.objects.create(document=doc)
            pendiente.documentsPendientes.add(documento_creado)

        serializer = Proveedor_PendienteSerializer(
            pendiente, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):

        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        # documentos = pendiente.documentsPendientes.all()
        # if not pendiente.copiaCedula == None:
        #     pendiente.copiaCedula.delete()
        # if not pendiente.copiaLicencia == None:
        #     pendiente.copiaLicencia.delete()
        # for doc in documentos:
        #     document = PendienteDocuments.objects.get(id=doc.id)
        #     document.delete()
        pendiente.estado = 0

        pendiente.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Pendientes_Search_Name(APIView, MyPaginationMixin):

    queryset = Proveedor_Pendiente.objects.all()
    serializer_class = Proveedor_PendienteSerializer
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):

        page = self.paginate_queryset(self.queryset.filter(
            Q(nombres__icontains=user) | Q(apellidos__icontains=user)))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Pendientes_FilterDate(APIView, MyPaginationMixin):

    queryset = Proveedor_Pendiente.objects.all()
    serializer_class = Proveedor_PendienteSerializer
    pagination_class = MyCustomPagination

    def get(self, request):
        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(self.queryset.filter(
            fecha_registro__date__range=[fechaIn, fechaFi]))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class SolicitudAdjudicada(APIView):
    def get(self, request, solicitud_ID, format=None):
        solicitud = Solicitud.objects.get(id=solicitud_ID)
        adjudicada = Envio_Interesados.objects.all().filter(
            solicitud=solicitud, proveedor=solicitud.proveedor)
        serializer = Envio_InteresadosSerializer(adjudicada, many=True)
        return Response(serializer.data)


class AdjudicarSolicitud(APIView):
    def put(self, request, solicitud_ID, format=None):
        data = {}
        try:
            id_user = request.data.get('proveedor')
            print("is",id_user)
            print(type(id_user))
            print("hola")
            proveedor = Proveedor.objects.get(user_datos__user__id=int(id_user))
            print("soli",solicitud_ID)
            print(type(solicitud_ID))
            print("hola")
            solicitud = Solicitud.objects.get(id=int(solicitud_ID))
            solicitud.proveedor = proveedor
            solicitud.save()
            serializer = SolicitudSerializer(
                solicitud, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # Notificacion a los usuarios
                titles = 'Solicitud Adjudicada del servicio '+solicitud.servicio.nombre
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__id=proveedor.user_datos.user.id)
                tokend = devices.values_list('registration_id', flat=True)
                tokens=list(tokend)
                dataNot = {"ruta": "/historial",
                          "descripcion": "Se le ha adjudicado el siguiente servicio: " + solicitud.servicio.nombre}

                send_notificationF(tokens,titles,bodys,dataNot)


                data['message'] = 'Solicitud adjudicada exitosamente!.'
                data['success'] = True
                data['solicitud'] = serializer.data
                return Response(data)
            else:
                data['message'] = 'La solicitud no es válida.'
                data['success'] = False
                return Response(data)
        except Exception as e:
            data['message'] = "No se pudo adjudicar la solicitud: " + str(e)
            data['success'] = False
            return Response(data)


class SolicitudID(APIView):
    def get(self, request, solicitud_ID, format=None):
        solicitud = Solicitud.objects.get(id=solicitud_ID)
        serializer = SolicitudSerializer(solicitud)
        return Response(serializer.data)

# Pagintation SolicitudesPending


class SolicitudesPendingPag(APIView, MyPaginationMixin):
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudSerializer
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(solicitante__user_datos__user__email=correo, adjudicar=False,
                                          proveedor__isnull=True, termino__isnull=True, fecha_expiracion__gt=timezone.now()).order_by('-id'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes en espera: " + \
                str(e)
            data['success'] = False
            return Response(data)


class SolicitudesPending(APIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        data = {}
        current_date = timezone.now()
        try:
            solicitudes = Solicitud.objects.all().filter(solicitante__user_datos__user__email=correo, adjudicar=False,
                                                         proveedor__isnull=True, termino__isnull=True, fecha_expiracion__gt=current_date).order_by('-id')
            serializer = SolicitudSerializer(solicitudes, many=True)
            data['success'] = True
            data['num_solicitudes'] = len(solicitudes)
            data['solicitudes'] = serializer.data
            return Response(data)
        except Exception as e:
            data['message'] = "No se pudo obtener la lista de solicitudes en espera: " + \
                str(e)
            data['success'] = False
            return Response(data)

# Pagintation SolicitudesPast


class SolicitudesPastPag(APIView, MyPaginationMixin):
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudSerializer
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(Q(solicitante__user_datos__user__email=correo) & (
                Q(termino='finalizado') | Q(termino='cancelado') | Q(fecha_expiracion__lt=timezone.now(), adjudicar=False))).order_by('-id'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes pasadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class SolicitudesPast(APIView):
    def get(self, request, correo, format=None):
        data = {}
        current_date = timezone.now()
        try:
            solicitudes = Solicitud.objects.filter(Q(solicitante__user_datos__user__email=correo) & (Q(termino='finalizado') | Q(
                termino='cancelado') | Q(fecha_expiracion__lt=timezone.now(), adjudicar=False))).order_by('-id')
            serializer = SolicitudSerializer(solicitudes, many=True)
            data['success'] = True
            data['num_solicitudes'] = len(solicitudes)
            data['solicitudes'] = serializer.data
            return Response(data)
        except Exception as e:
            data['message'] = "No se pudo obtener la lista de solicitudes pasadas: " + \
                str(e)
            data['success'] = False
            return Response(data)

# Pagintation SolicitudesPaid


class SolicitudesPaidPag(APIView, MyPaginationMixin):
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudSerializer
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(
                solicitante__user_datos__user__email=correo, adjudicar=True, pagada=True, termino='pagado').order_by('-id'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes pagadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class SolicitudesPaid(APIView):
    def get(self, request, correo, format=None):
        data = {}
        current_date = timezone.now()
        try:
            solicitudes = Solicitud.objects.filter(
                solicitante__user_datos__user__email=correo, adjudicar=True, pagada=True, termino='pagado').order_by('-id')
            serializer = SolicitudSerializer(solicitudes, many=True)
            data['success'] = True
            data['num_solicitudes'] = len(solicitudes)
            data['solicitudes'] = serializer.data
            return Response(data)
        except Exception as e:
            data['success'] = False
            data['message'] = "No se pudo obtener la lista de solicitudes pagadas: " + \
                str(e)
            return Response(data)

# Pagintation SolicitudesNoPaid


class SolicitudesNoPaidPag(APIView, MyPaginationMixin):
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudSerializer
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(
                solicitante__user_datos__user__email=correo, adjudicar=True, pagada=False, proveedor__isnull=False).order_by('-id'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes no pagadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class SolicitudesNoPaid(APIView):
    def get(self, request, correo, format=None):
        data = {}
        current_date = timezone.now()
        try:
            solicitudes = Solicitud.objects.filter(
                solicitante__user_datos__user__email=correo, adjudicar=True, pagada=False, proveedor__isnull=False).order_by('-id')
            serializer = SolicitudSerializer(solicitudes, many=True)
            data['success'] = True
            data['num_solicitudes'] = len(solicitudes)
            data['solicitudes'] = serializer.data
            return Response(data)
        except Exception as e:
            data['message'] = "No se pudo obtener la lista de solicitudes no pagadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class Solicituds(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, format=None):
        solicitud = Solicitud.objects.all().filter()
        serializer = SolicitudSerializer(solicitud, many=True)

        # print(JSONRenderer().render(serializer.data))
        return Response(serializer.data)

    def put(self, request, solicitud_ID, format=None):
        data = {}
        try:
            solicitud = Solicitud.objects.get(id=solicitud_ID)
            solicitud.estado = request.data.get('estado', solicitud.estado)
            solicitud.pagada = request.data.get('pagada', solicitud.pagada)
            solicitud.termino = request.data.get('termino', solicitud.termino)
            solicitud.save()
            serializer = SolicitudSerializer(
                solicitud, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if request.data.get("termino") != "cancelado":
                    proveedor = solicitud.proveedor
                    solicitante = solicitud.solicitante
                    solicitudes = Solicitud.objects.filter(
                        proveedor=proveedor)  # .values('rating')
                    ratingProveedor = solicitudes.aggregate(
                        Sum('rating'))['rating__sum'] / len(solicitudes)
                    adjudicada = Envio_Interesados.objects.get(solicitud=solicitud, proveedor=solicitud.proveedor)
                    proveedor.rating = ratingProveedor
                    proveedor.servicios = len(solicitudes)
                    proveedor.user_datos.tramites=proveedor.user_datos.tramites +1
                    proveedor.user_datos.dinero_invertido=proveedor.user_datos.dinero_invertido + adjudicada.oferta
                    datosSolicitante= solicitante.user_datos
                    datosSolicitante.tramites=datosSolicitante.tramites +1
                    datosSolicitante.dinero_invertido=datosSolicitante.dinero_invertido + adjudicada.oferta
                    proveedor.save()
                    datosSolicitante.save()
                    datosProveedor=proveedor.user_datos
                    datosProveedor.save()
                    titles = 'Servicio finalizado: '+solicitud.servicio.nombre
                    bodys = '¡Dale un vistazo!'
                    devices = FCMDevice.objects.filter(
                        active=True, user__username=solicitud.proveedor.user_datos.user.email)

                    # Obtiene la lista de registration_ids (tokens)
                    tokend = devices.values_list('registration_id', flat=True)
                    dataNot={"ruta": "/historial", "descripcion": "Puede observar la solicitud " +
                              solicitud.servicio.nombre + " finalizada en la seccion de Historial > PASADAS"}
                    tokens=list(tokend)
                    if request.data.get("termino") != "pagado":
                        send_notificationF(tokens,titles,bodys,dataNot)


                data['message'] = 'Solicitud actualizada exitosamente!.'
                data['success'] = True
                data['solicitud'] = serializer.data
                return Response(data)
            else:
                data['message'] = 'La solicitud no es válida.'
                data['success'] = False
                return Response(data)
        except Exception as e:
            data['message'] = "No se pudo actualizar la solicitud: " + str(e)
            data['success'] = False
            return Response(data)


class AddSolicitud(APIView):
    def post(self, request, format=None):
        print('Entro Aca')
        # Data de respuesta
        data = {}

        # solicitud
        desc = request.data.get('descripcion')
        foto_desc = request.FILES.get('foto_descripcion')
        fecha_exp = request.data.get('fecha')
        fecha_creacion = request.data.get('fecha_creacion')
        user = request.data.get('solicitante')  # id solicitante
        servicio_id = request.data.get('servicio')
        pago_name = request.data.get('tipo_pago')
        # lista de primeros ids de la tabla proveedor
        proveedores_id = request.data.get('proveedores')

        # ubicacion
        lat = request.data.get('latitud')
        alt = request.data.get('altitud')
        drc = request.data.get('direccion')
        ref = request.data.get('referencia')  # descripcion
        foto_ubic = request.FILES.get('foto_ubicacion')

        print(lat)
        print(alt)
        print('aa')
        print(proveedores_id)
        # Intenta obtener o crear en un Objeto Ubicacion con los campos de la ubicacion obtenidos por el body del request.
        try:
            ubic, creado = Ubicacion.objects.get_or_create(
                latitud=lat, altitud=alt, direccion=drc, referencia=ref, foto_ubicacion=foto_ubic)
        except Exception as e:
            data['message'] = "No se pudo obtener o crear al objeto Ubicación: " + \
                str(e)
            data['success'] = False
            return Response(data)

        # Intenta obtener un Objeto Solicitante.
        try:
            solic = Solicitante.objects.get(id=user)
        except Exception as e:
            data['message'] = "No se pudo obtener al solicitante en la base de datos: " + \
                str(e)
            data['success'] = False
            return Response(data)

        # Intenta obtener un Objeto Servicio en la base de datos.
        try:
            service = Servicio.objects.get(id=servicio_id)
        except Exception as e:
            data['message'] = "No se pudo obtener al objeto Servicio en la base de datos: " + \
                str(e)
            data['success'] = False
            return Response(data)

        # Intenta obtener o crear un Objeto Tipo_Pago en la base de datos.
        try:
            t_pago, creado = Tipo_Pago.objects.get_or_create(nombre=pago_name)
        except Exception as e:
            data['message'] = "No se pudo obtener o crear al objeto Tipo_Pago: " + \
                str(e)
            data['success'] = False
            return Response(data)

        # Intenta crear un Objeto Solicitud con los campos necesarios para crear el objeto.
        try:
            solicitud = Solicitud.objects.create(descripcion=desc, fecha_expiracion=fecha_exp, solicitante=solic,
                                                 ubicacion=ubic, tipo_pago=t_pago, servicio=service,
                                                 foto_descripcion=foto_desc, rating=0)
            serializer = SolicitudSerializer(solicitud)
        except Exception as e:
            # Ahora puedes proceder a eliminar la solicitud
            if 'solicitud' in locals():
                solicitud.delete()
            data['message'] = "No se pudo crear al objeto Solicitud: " + \
                str(e)
            data['success'] = False
            return Response(data)

        # Obtencion de los IDs de los proveedores a los cuales se les enviaran la notificacion del la solicitud del servicio.
        try:
            proveedores_id = proveedores_id.split(",")
        except Exception as e:
            solicitud.delete()
            data['message'] = "Ha ocurrido un error al hacer split de la lista de proveedores: " + \
                str(e)
            data['success'] = False
            return Response(data)

        # Notificacion a los usuarios
        titles = 'Solicitud Recibida del servicio '+solicitud.servicio.nombre
        bodys = '¡Dale un vistazo!'
        data={
                        "ruta": "/main/home",
                        "descripcion": "Se ha recibido una solicitud de servicio."
                    }
        print("Proveedores:", proveedores_id)

        for proveedor in proveedores_id:
            # Intenta obtener un Objeto Proveedor en la base de datos.
            try:
                prov = Proveedor.objects.get(id=proveedor)
                print(f"Proveedor encontrado: {prov}")
            except Exception as e:
                print(f"Error al obtener el proveedor con ID {proveedor}: {e}")
                solicitud.delete()
                data['message'] = f"Error al obtener un proveedor con ID {proveedor}: {str(e)}"
                data['success'] = False
                return Response(data)

            # Intenta crear un Objeto Envio_Interesados en la base de datos.
            try:
                envio_interesados = Envio_Interesados.objects.create(
                    solicitud=solicitud,
                    proveedor=prov
                )
                print(f"Envio_Interesados creado para proveedor: {proveedor}")
            except Exception as e:
                print(f"Error al crear Envio_Interesados para el proveedor {proveedor}: {e}")
                solicitud.delete()
                data['message'] = f"Error al crear Envio_Interesados para proveedor {proveedor}: {str(e)}"
                data['success'] = False
                return Response(data)

            try:
                # Intenta mandar una notificación al proveedor con el id.
                # Filtra los dispositivos por el ID del usuario
                prov = Proveedor.objects.get(id=proveedor)
                print("id", prov)
                datos_prov = Datos.objects.get(id=prov.user_datos_id)
                user = User.objects.get(id=datos_prov.user.id)
                u_id = user.id
                print("idp", u_id)
                devices = FCMDevice.objects.filter(active=True, user_id=u_id)
                # Obtener los tokens de esos dispositivos
                tokend = devices.values_list('registration_id', flat=True)
                tokens = list(tokend)
                print(f"Tokens encontrados para el proveedor {proveedor}: {tokend}")
                send_notificationF(tokens,titles,bodys,data)
            except Exception as e:
                print(f"Error al enviar notificación al proveedor {proveedor}: {e}")
                # Realiza las eliminaciones o acciones necesarias en caso de error
                envio_interesados.delete()
                solicitud.delete()
                data['message'] = f"Error al enviar notificación al proveedor {proveedor}: {str(e)}"
                data['success'] = False
                return Response(data)

        # Todo OK!
        data['solicitud'] = serializer.data
        data['success'] = True
        return Response(data)



class Solicitudes(APIView):
   # permission_classes = (IsAuthenticated,)
   # authentication_class = (TokenAuthentication)
    def get(self, request, user, format=None):
        solicitud = Solicitud.objects.all().filter(
            solicitante__user_datos__user__email=user)
        serializer = SolicitudSerializer(solicitud, many=True)
        # print(JSONRenderer().render(serializer.data))
        return Response(serializer.data)


class Profesiones(APIView):
   # permission_classes = (IsAuthenticated,)
   # authentication_class = (TokenAuthentication)
    def get(self, request, format=None):
        profesion = Profesion.objects.all().filter(estado=1)
        serializer = ProfesionSerializer(profesion, many=True)
        # print(JSONRenderer().render(serializer.data))
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        try:
            servicioUser = Servicio.objects.get(
                nombre=request.data.get("servicio"))
            profesionCreada = Profesion.objects.create(nombre=request.data.get(
                "nombre"), descripcion=request.data.get("descripcion"))
            profesionCreada.foto = request.FILES.get('foto')
            profesionCreada.servicio.add(servicioUser)
            profesionCreada.save()
            serializer = ProfesionSerializer(profesionCreada)
            data["success"] = True
            data["mensaje"] = "Creacion de profesion exitoso"
            data["profesion"] = serializer.data
            return Response(data)
        except:
            data["success"] = False
            data["mensaje"] = "Hubo un error al crear la profesion"
            return Response(data)

    def put(self, request):

        profesion = Profesion.objects.get(id=request.data.get("id"))
        servicioNuevo = Servicio.objects.get(
            nombre=request.data.get("servicio"))
        profesion.servicio.clear()
        profesion.servicio.add(servicioNuevo)
        # request.data["servicio"] = ServicioSerializer(profesion.servicio, many=True)
        # request.data["servicio"] = [{"nombre":"Hola"}]
        # profesion.nombre = request.data.get("nombre")
        # profesion.descripcion = request.data.get("descripcion")
        # profesion.foto = request.FILES.get('foto')

        serializer = ProfesionSerializer(
            profesion, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):

        profesion = Profesion.objects.get(id=pk)
        profesion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CrearProfesionesFaltantesView(APIView):
    def post(self, request, format=None):
        # Diccionario para almacenar los resultados
        data = {
            "profesiones_creadas": [],
            "errores": []
        }

        # Obtener todos los servicios
        servicios = Servicio.objects.all()

        # Recorrer los servicios
        for servicio in servicios:
            # Verificar si ya existe una profesion con el mismo nombre
            profesion_existente = Profesion.objects.filter(nombre=servicio.nombre).first()

            if profesion_existente is None:
                try:
                    # Crear la profesion si no existe
                    profesion = Profesion.objects.create(
                        nombre=servicio.nombre,
                        descripcion=servicio.descripcion,
                        foto=servicio.foto
                    )
                    data["profesiones_creadas"].append({
                        "id": profesion.id,
                        "nombre": profesion.nombre
                    })
                except Exception as e:
                    # Capturar errores específicos de cada creación fallida
                    data["errores"].append({
                        "servicio_id": servicio.id,
                        "nombre": servicio.nombre,
                        "error": str(e)
                    })

        # Respuesta final con profesiones creadas y errores si existen
        return Response(data)



class ProfesionDetails(APIView):

    def get(self, request, pk, format=None):

        profesion = Profesion.objects.get(id=pk)
        serializer = ProfesionSerializer(profesion)
        return Response(serializer.data)


class ProfesionProveedor(APIView):
    def get(self, request, proveedor_id, format=None):
        profesiones = Profesion_Proveedor.objects.all().filter(proveedor__id=proveedor_id)
        serializer = Profesion_ProveedorSerializer(profesiones, many=True)
        return Response(serializer.data)


class ProveedoresByProfesion(APIView):
    def get(self, request, servicio_id, format=None):
        servicio= Servicio.objects.get(id=servicio_id)
        profesion= Profesion.objects.get(nombre=servicio.nombre)
        prov_prof = Profesion_Proveedor.objects.all().filter(
            profesion=profesion)
        print("servicio")
        print(servicio)
        print("prov_prof")
        print(prov_prof)
        serializer = Profesion_ProveedorSerializer(prov_prof, many=True)
        return Response(serializer.data)

class SincronizarProfesionProveedorView(APIView):
   def post(self, request, format=None):
    # Diccionario para almacenar resultados
    data = {
        "creados": [],
        "actualizados": [],
        "errores": []
    }

    # Obtener todos los servicios
    servicios = Servicio.objects.all()

    for servicio in servicios:
        try:
            # Obtener la profesión asociada al servicio (por nombre)
            profesion, _ = Profesion.objects.get_or_create(
                nombre=servicio.nombre,
                defaults={
                    "descripcion": servicio.descripcion,
                    "foto": servicio.foto
                }
            )

            # Obtener los proveedores asociados con la profesión
            proveedores = Proveedor.objects.filter(profesion=profesion)

            # Si no hay proveedores, continuar con el siguiente servicio
            if not proveedores.exists():
                continue  # No hay proveedores para esta profesión, pasar al siguiente servicio

            # Crear o actualizar Profesion_Proveedor para cada proveedor
            for proveedor in proveedores:
                profesion_proveedor, created = Profesion_Proveedor.objects.update_or_create(
                    profesion=profesion,
                    proveedor=proveedor,
                    ano_experiencia=proveedor.ano_profesion,
                )

                if created:
                    data["creados"].append({"profesion_id": profesion.id, "proveedor_id": proveedor.id})
                else:
                    data["actualizados"].append({"profesion_id": profesion.id, "proveedor_id": proveedor.id})

        except Exception as e:
            # Capturar cualquier error
            data["errores"].append({
                "servicio_id": servicio.id,
                "nombre": servicio.nombre,
                "error": str(e)
            })

    return Response(data, status=status.HTTP_200_OK)

class ValorTotalProveedores(APIView):
    def get(self, request, format=None):
        contenido = {}
        contenido["totalPendientes"] = Proveedor.objects.count()
        contenido["totalProveedores"] = PagoEfectivo.objects.count()

        return Response(contenido)


class ValorTotalSolicitantes(APIView):
    def get(self, request, format=None):
        contenido = Solicitantes.objects.count()
        return Response(contenido)


class Proveedores(APIView, MyPaginationMixin):
   # permission_classes = (IsAuthenticated,)
   # authentication_class = (TokenAuthentication)
    queryset = Proveedor.objects.all().exclude(user_datos__tipo=4).order_by('-id')
    serializer_class = ProveedorSerializer
    pagination_class = MyCustomPagination

    # def get(self, request, format=None):
    #     proveedor = Proveedor.objects.all()
    #     # proveedor = Proveedor.objects.all().exclude(user_datos__tipo=4)
    #     serializer = ProveedorSerializer(proveedor, many=True)
    #     #print(JSONRenderer().render(serializer.data))
    #     return Response(serializer.data)

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    def put(self, request, id, format=None):
        proveedor = Proveedor.objects.get(id=id)
        datoObj = Datos.objects.get(id=proveedor.user_datos.id)
        serializerDato = DatosSerializer(
            datoObj, data=request.data, partial=True)
        serializer = ProveedorSerializer(
            proveedor, data=request.data, partial=True)
        if serializer.is_valid() and serializerDato.is_valid():
            serializer.save()
            serializerDato.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        proveedor = Proveedor.objects.get(id=id)
        proveedor.estado=False
        proveedor.save()
        datos = proveedor.user_datos
        datos.estado=False
        datos.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Get_Proveedor(APIView):

    def get(self, request, pk, format=None):

        proveedor = Proveedor.objects.get(user_datos__id=pk)
        serializer = ProveedorSerializer(proveedor)
        return Response(serializer.data)


class Get_ProveedorByUser(APIView):

    def get(self, request, user, format=None):

        proveedor = Proveedor.objects.get(user_datos__user__username=user)
        serializer = ProveedorSerializer(proveedor)
        return Response(serializer.data)

class Get_AdminByUser(APIView):

    def get(self, request, user, format=None):

        proveedor = Proveedor.objects.get(user_datos__user__username=user)
        serializer = ProveedorSerializer(proveedor)
        return Response(serializer.data)

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


class SolicitudProfesionProveedor(APIView, MyPaginationMixin):

    queryset = SolicitudProfesion.objects.all()
    serializer_class = SolicitudProfesionSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class ManejoSolicitud(APIView):
    def get(self, request, format=None):
        solicitudes_profesion = SolicitudProfesion.objects.all().filter()
        serializer = SolicitudProfesionSerializer(
            solicitudes_profesion, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        correo_proveedor = request.data.get("proveedor")
        nombre_profesion = request.data.get("profesion")
        anio_exp = request.data.get("anio")
        documentos = request.FILES.get("documento")
        # Verifica el proveedor en la base de datos
        try:
            proveedorUser = Proveedor.objects.get(
                user_datos__user__username=correo_proveedor)
        except:
            data['succes'] = False
            data['message'] = 'No se ha encontrado a un proveedor en la base de datos con el correo pasado por parametro.'
            return Response(data)
        # Verifica la creacion del objeto SolicitudProfesion
        try:
            solicitud = SolicitudProfesion.objects.create(
                proveedor=proveedorUser, profesion=nombre_profesion, anio_experiencia=anio_exp, documento=documentos)
        except:
            data['succes'] = False
            data['message'] = 'No se ha podido crear el objeto SolicitudProfesion en la base de datos.'
            return Response(data)

        return Response(SolicitudProfesionSerializer(solicitud).data)

    def put(self, request, pk, format=None):

        solicitud = SolicitudProfesion.objects.get(id=pk)
        solicitud.estado = request.data.get("estado")
        solicitud.fecha = datetime.datetime.now()
        solicitud.save()
        serializer = SolicitudProfesionSerializer(solicitud)
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        solicitud = SolicitudProfesion.objects.get(id=pk)
        if not solicitud.documento == None:
            solicitud.documento.delete()
        solicitud.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CorreoSolicitud(APIView):

    def post(self, request, format=None):
        data = {}
        correo = request.data.get('email')
        profesion = request.data.get('profesion')
        emails = []
        formatEmail = FormatEmail()
        user = Datos.objects.get(user__email=correo)
        if user is not None:
            asunto = "Respuesta Solicitud"
            emails.append(correo)
            try:
                if (request.data.get("estado")):
                    thread = threading.Thread(target=formatEmail.send_email(emails, asunto, 'emails/solicitudRechazada.html', {
                                              "username": user.nombres + ' ' + user.apellidos, "user": correo, "profesion": profesion}))
                    thread.start()
                    data['success'] = True
                    return Response(data)
                else:
                    thread = threading.Thread(target=formatEmail.send_email(emails, asunto, 'emails/solicitudAceptada.html', {
                                              "username": user.nombres + ' ' + user.apellidos, "user": correo, "profesion": profesion}))
                    thread.start()
                    data['success'] = True
                    return Response(data)
            except:
                data['success'] = False
                return Response(data)
        else:
            data['success'] = False
            return Response(data)
        return Response(status=status.HTTP_200_OK)


class SolicitudByName(APIView):

    def get(self, request, user, format=None):

        solicitudes = SolicitudProfesion.objects.filter(
            proveedor__user_datos__user__username=user)
        serializer = SolicitudProfesionSerializer(solicitudes, many=True)
        return Response(serializer.data)


class SolicitudDetails(APIView):

    def get(self, request, pk, format=None):

        solicitud = SolicitudProfesion.objects.get(id=pk)
        serializer = SolicitudProfesionSerializer(solicitud)
        return Response(serializer.data)


class Solicitudes_Search_Name(APIView, MyPaginationMixin):

    queryset = SolicitudProfesion.objects.all()
    serializer_class = SolicitudProfesionSerializer
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):

        page = self.paginate_queryset(self.queryset.filter(
            Q(proveedor__user_datos__nombres__icontains=user) | Q(proveedor__user_datos__apellidos__icontains=user)))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Solicitudes_Filter_Date(APIView, MyPaginationMixin):

    queryset = SolicitudProfesion.objects.all()
    serializer_class = SolicitudProfesionSerializer
    pagination_class = MyCustomPagination

    def get(self, request):
        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(self.queryset.filter(
            fecha_solicitud__date__range=[fechaIn, fechaFi]))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Proveedores_Search_Name(APIView, MyPaginationMixin):

    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):

        page = self.paginate_queryset(self.queryset.filter(
            Q(user_datos__nombres__icontains=user) | Q(user_datos__apellidos__icontains=user)))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Proveedores_Filter_Date(APIView, MyPaginationMixin):

    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
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


class PlanProveedores_Filter_Date(APIView, MyPaginationMixin):

    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    pagination_class = MyCustomPagination

    def get(self, request):
        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(self.queryset.filter(
            planproveedor__fecha_expiracion__date__range=[fechaIn, fechaFi]))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Documentos_proveedor(APIView):

    def put(self, request, format=None):
        descripcion = request.data.get('descripcion')
        documento = Document.objects.get(descripcion=descripcion)
        serializer = DocumentSerializer(
            documento, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProveedoresDocumentsView(APIView):
    def get(self, request, format=None):
        queryset = Document.objects.all()
        serializer = DocumentSerializer(queryset, many=True)
        parser_classes = (MultiPartParser, FormParser)
        return Response(serializer.data)

    def delete(self, request, format=None):
        documento_proveedor = Document.objects.get(id=request.GET.get("id"))
        documento_proveedor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class Proveedores_Pendientes(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    # def get(self, request, format=None):
    #     proveedor_pendiente = Proveedor_Pendiente.objects.all().filter()
    #     serializer = Proveedor_PendienteSerializer(proveedor_pendiente,many= True)
    #     return Response(serializer.data)
    queryset = Proveedor_Pendiente.objects.all().order_by('-id').filter(estado=0)
    serializer_class = Proveedor_PendienteSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    def delete(self, request, username, desc, format=None):
        proveedor_pendiente = Proveedor_Pendiente.objects.get(
            proveedor__user_datos__user__username=username)
        # descripcion = request.data.get('descripcion')
        descripcion = desc.split("|")
        documento = Document.objects.get(descripcion=descripcion[0])
        if descripcion[1] == "true":
            data = {"estado": True}
            serializer = DocumentSerializer(documento, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                proveedor_pendiente.delete()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            documento.delete()
            proveedor_pendiente.delete()
            return Response(status=status.HTTP_200_OK)

    def put(self, request, format=None):
        data = {}
        desc = request.data.get('descripcion')
        profesion = request.data.get('profesion')
        documento = Document.objects.get(descripcion=desc, estado=False)
        documento.descripcion = profesion
        documento.save()
        data1 = {"descripcion": profesion}
        serializer = DocumentSerializer(documento, data=data1, partial=True)
        if serializer.is_valid():
            serializer.save()
            data['success'] = True
            return Response(data)
        data['success'] = False
        return Response(data)

        data = {}
        cuenta = Cuenta.objects.get(
            proveedor__user_datos__user__username=username)
        anio = request.POST.get('anio')
        estado = request.POST.get('estado')
        profesion = request.POST.get('profesion')
        banco = cuenta.banco
        n_cuenta = cuenta.numero_cuenta
        tipo = cuenta.tipo_cuenta
        descripcion = request.POST.get('descripcion')
        documento = request.FILES.get('documento')
        documento_creado = Document.objects.create(
            descripcion=descripcion, documento=documento)
        serializer = DocumentSerializer(documento_creado)
        data['Document'] = serializer.data
        if documento_creado:

            proveedor = Proveedor.objects.get(
                user_datos__user__username=username)
            proveedor.document.add(documento_creado)
            profesion_creada = Proveedor_Pendiente.objects.create(
                proveedor=proveedor, email=username, estado=estado, profesion=profesion, ano_experiencia=anio, banco=banco, numero_cuenta=n_cuenta, tipo_cuenta=tipo)
            serializer = Proveedor_PendienteSerializer(profesion_creada)

            data['proveedor_pendiente'] = serializer.data
            if profesion_creada:
                return Response(data)
            else:
                data['error'] = "Error al crear!."
                return Response(data)
        else:
            data['error'] = "Error al crear el documento!."
            return Response(data)


class Proveedores_Rechazados(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    # def get(self, request, format=None):
    #     proveedor_pendiente = Proveedor_Pendiente.objects.all().filter()
    #     serializer = Proveedor_PendienteSerializer(proveedor_pendiente,many= True)
    #     return Response(serializer.data)
    queryset = Proveedor_Pendiente.objects.filter(estado=1).filter(Q(rechazo__isnull=False) & ~Q(rechazo='')).order_by('-id')
    serializer_class = Proveedor_PendienteSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            print("serializer kkkkkkkkkk")
            print(serializer)
            return self.get_paginated_response(serializer.data)

    def delete(self, request, username, desc, format=None):
        proveedor_pendiente = Proveedor_Pendiente.objects.get(
            proveedor__user_datos__user__username=username)
        # descripcion = request.data.get('descripcion')
        descripcion = desc.split("|")
        documento = Document.objects.get(descripcion=descripcion[0])
        if descripcion[1] == "true":
            data = {"estado": True}
            serializer = DocumentSerializer(documento, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                proveedor_pendiente.delete()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            documento.delete()
            proveedor_pendiente.delete()
            return Response(status=status.HTTP_200_OK)

    def put(self, request, format=None):
        data = {}
        desc = request.data.get('descripcion')
        profesion = request.data.get('profesion')
        documento = Document.objects.get(descripcion=desc, estado=False)
        documento.descripcion = profesion
        documento.save()
        data1 = {"descripcion": profesion}
        serializer = DocumentSerializer(documento, data=data1, partial=True)
        if serializer.is_valid():
            serializer.save()
            data['success'] = True
            return Response(data)
        data['success'] = False
        return Response(data)

        data = {}
        cuenta = Cuenta.objects.get(
            proveedor__user_datos__user__username=username)
        anio = request.POST.get('anio')
        estado = request.POST.get('estado')
        profesion = request.POST.get('profesion')
        banco = cuenta.banco
        n_cuenta = cuenta.numero_cuenta
        tipo = cuenta.tipo_cuenta
        descripcion = request.POST.get('descripcion')
        documento = request.FILES.get('documento')
        documento_creado = Document.objects.create(
            descripcion=descripcion, documento=documento)
        serializer = DocumentSerializer(documento_creado)
        data['Document'] = serializer.data
        if documento_creado:

            proveedor = Proveedor.objects.get(
                user_datos__user__username=username)
            proveedor.document.add(documento_creado)
            profesion_creada = Proveedor_Pendiente.objects.create(
                proveedor=proveedor, email=username, estado=estado, profesion=profesion, ano_experiencia=anio, banco=banco, numero_cuenta=n_cuenta, tipo_cuenta=tipo)
            serializer = Proveedor_PendienteSerializer(profesion_creada)

            data['proveedor_pendiente'] = serializer.data
            if profesion_creada:
                return Response(data)
            else:
                data['error'] = "Error al crear!."
                return Response(data)
        else:
            data['error'] = "Error al crear el documento!."
            return Response(data)


class Proveedores_Proveedores(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    # def get(self, request, format=None):
    #     proveedor_pendiente = Proveedor_Pendiente.objects.all().filter()
    #     serializer = Proveedor_PendienteSerializer(proveedor_pendiente,many= True)
    #     return Response(serializer.data)
    print("querysetBan")
    formatEmail = FormatEmail()
    today = timezone.now().date()
    for e in Proveedor.objects.all().order_by('-id').filter(fecha_caducidad__lt=today):
        if e.estado != False:
            thread = threading.Thread(target=formatEmail.send_email([e.user_datos.user.username], "Cuenta caducada", 'emails/enviarAlerta.html', {"username":e.user_datos.user.username, "contenido": "Tu cuenta ha caducado, si deseas extender tu contrato contactanos por nuestros canales oficiales."}))
            thread.start()
        print('e.fecha_caducidad')
        print(e.fecha_caducidad)
        e.estado = False
        e.save()
        datos=e.user_datos
        datos.estado=False
        datos.save()
    queryset = Proveedor.objects.all().order_by('-id')

    serializer_class = ProveedorSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    def delete(self, request, username, desc, format=None):
        proveedor_pendiente = Proveedor_Pendiente.objects.get(
            proveedor__user_datos__user__username=username)
        # descripcion = request.data.get('descripcion')
        descripcion = desc.split("|")
        documento = Document.objects.get(descripcion=descripcion[0])
        if descripcion[1] == "true":
            data = {"estado": True}
            serializer = DocumentSerializer(documento, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                proveedor_pendiente.delete()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            documento.delete()
            proveedor_pendiente.delete()
            return Response(status=status.HTTP_200_OK)

    def put(self, request, format=None):
        data = {}
        desc = request.data.get('descripcion')
        profesion = request.data.get('profesion')
        documento = Document.objects.get(descripcion=desc, estado=False)
        documento.descripcion = profesion
        documento.save()
        data1 = {"descripcion": profesion}
        serializer = DocumentSerializer(documento, data=data1, partial=True)
        if serializer.is_valid():
            serializer.save()
            data['success'] = True
            return Response(data)
        data['success'] = False
        return Response(data)

        data = {}
        cuenta = Cuenta.objects.get(
            proveedor__user_datos__user__username=username)
        anio = request.POST.get('anio')
        estado = request.POST.get('estado')
        profesion = request.POST.get('profesion')
        banco = cuenta.banco
        n_cuenta = cuenta.numero_cuenta
        tipo = cuenta.tipo_cuenta
        descripcion = request.POST.get('descripcion')
        documento = request.FILES.get('documento')
        documento_creado = Document.objects.create(
            descripcion=descripcion, documento=documento)
        serializer = DocumentSerializer(documento_creado)
        data['Document'] = serializer.data
        if documento_creado:

            proveedor = Proveedor.objects.get(
                user_datos__user__username=username)
            proveedor.document.add(documento_creado)
            profesion_creada = Proveedor_Pendiente.objects.create(
                proveedor=proveedor, email=username, estado=estado, profesion=profesion, ano_experiencia=anio, banco=banco, numero_cuenta=n_cuenta, tipo_cuenta=tipo)
            serializer = Proveedor_PendienteSerializer(profesion_creada)

            data['proveedor_pendiente'] = serializer.data
            if profesion_creada:
                return Response(data)
            else:
                data['error'] = "Error al crear!."
                return Response(data)
        else:
            data['error'] = "Error al crear el documento!."
            return Response(data)


class CuentaProveedor(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(selt, request, proveedorID, format=None):
        cuentas = Cuenta.objects.all().filter(proveedor=proveedorID)
        serializer = CuentaSerializer(cuentas, many=True)
        return Response(serializer.data)


class DatosUsers(APIView):
    def get(self, request, format=None):
        queryset = Datos.objects.all().order_by('-id')
        serializer = DatosSerializer(queryset, many=True)
        parser_classes = (MultiPartParser, FormParser)
        return Response(serializer.data)

    def delete(self, request, format=None):
        data = {}
        try:
            dato = Datos.objects.get(id=request.GET.get("id"))
            dato.delete()
            data['sucess'] = True
            data['mensaje'] = 'Eliminacion del Objeto Dato realizado exitosamente.'
            return Response(data)
        except:
            data['sucess'] = False
            data['mensaje'] = 'Ha ocurrido un error al eliminar el Objeto Dato.'
            return Response(data)


class Usuarios(APIView):
    def get(self, request, format=None):
        queryset = User.objects.all().order_by('-id')
        serializer = UserSerializer(queryset, many=True)
        parser_classes = (MultiPartParser, FormParser)
        return Response(serializer.data)

    def delete(self, request, format=None):
        data = {}
        try:
            dato = User.objects.get(id=request.GET.get("id"))
            dato.delete()
            data['sucess'] = True
            data['mensaje'] = 'Eliminacion del Objeto User realizado exitosamente.'
            return Response(data)
        except:
            data['sucess'] = False
            data['mensaje'] = 'Ha ocurrido un error al eliminar el Objeto User.'
            return Response(data)


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

    def put(self, request, user, formato=None):
        persona = Datos.objects.get(user__email=user)
        if persona:
            nombre_user = request.data.get('nombres')
            persona.nombres = nombre_user
            ciudad_user = request.data.get('ciudad')
            persona.ciudad = ciudad_user
            cedula_user = request.data.get('cedula')
            persona.cedula = cedula_user
            apellido_user = request.data.get('apellidos')
            persona.apellidos = apellido_user
            genero_user = request.data.get('genero')
            persona.genero = genero_user
            telefono_user = request.data.get('telefono')
            persona.telefono = telefono_user
            if 'foto' in request.FILES:
                foto_user = request.FILES.get('foto')
                persona.foto = foto_user
            codigo_invitacion = request.data.get('codigo_invitacion')
            persona.codigo_invitacion = codigo_invitacion
            puntos = request.data.get('puntos')
            persona.puntos = puntos
            persona.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SolicitanteUser(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, user, format=None):
        solicitante = Solicitante.objects.filter(user_datos__user__email=user)
        serializer = SolicitanteSerializer(solicitante, many=True)
        return Response(serializer.data)


class SolicitanteByUserDatos(APIView):  #  Endopint Add
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, UserDatosId, format=None):
        solicitante = Solicitante.objects.filter(user_datos__id=UserDatosId)
        serializer = SolicitanteSerializer(solicitante, many=True)
        return Response(serializer.data)


class Solicitantes(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    queryset = Solicitante.objects.all().order_by('-id')
    serializer_class = SolicitanteSerializer
    pagination_class = MyCustomPagination

    def get(self, request, formt=None):
        print(request.GET.get("filtro"))
        if request.GET.get("filtro") == "activos":
            print(request.GET.get("filtro"))
            self.queryset = Solicitante.objects.all().filter(estado=True).order_by('-id')
        if request.GET.get("filtro") == "inactivos":
            print(request.GET.get("filtro"))
            self.queryset = Solicitante.objects.all().filter(estado=False).order_by('-id')
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    # def get(self, request, format=None):
    #     solicitantes = Solicitante.objects.all().filter()
    #     serializer = SolicitanteSerializer(solicitantes, many=True)
    #     return Response(serializer.data)

    def put(self, request, id, format=None):
        solicitante = Solicitante.objects.get(id=id)
        datoObj = Datos.objects.get(id=solicitante.user_datos.id)
        serializerDato = DatosSerializer(
            datoObj, data=request.data, partial=True)
        serializer = SolicitanteSerializer(
            solicitante, data=request.data, partial=True)
        if serializer.is_valid() and serializerDato.is_valid():
            serializer.save()
            serializerDato.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        solicitante = Solicitante.objects.get(id=id)
        solicitante.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SolicitantesFilter(APIView, MyPaginationMixin):
    queryset = Solicitante.objects.all()
    serializer_class = SolicitanteSerializer
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


class FiltroNombres(APIView, MyPaginationMixin):

    queryset = Solicitante.objects.all()
    serializer_class = SolicitanteSerializer
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):

        page = self.paginate_queryset(self.queryset.filter(
            Q(user_datos__nombres__icontains=user) | Q(user_datos__apellidos__icontains=user)))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    # def get(self, request, user, format=None):

    #     solicitante = Solicitante.objects.all().filter(user_datos__nombres__contains= user)
    #     serializer= SolicitanteSerializer(solicitante, many=True)
    #     return Response(serializer.data)


class Administradores(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    queryset = Administrador.objects.all().order_by('-id')
    serializer_class = AdministradorSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        data = {}
        userObj = request.data.get('user')
        try:
            usuario = User.objects.create_user(email=request.data.get(
                'email'), username=request.data.get('email'), password=request.data.get('password'))
            grupo = Group.objects.get(name=request.data.get('rol'))
            grupo.user_set.add(usuario)
        except:
            data['error'] = "Usuario ya existente!."
            return Response(data)

        tipoUser = request.data.get('tipo')
        nombreUser = request.data.get('nombres')
        apellidosUser = request.data.get('apellidos')
        telefonoUser = request.data.get('telefono')
        ciudadUser = request.data.get('ciudad')
        cedulaUser = request.data.get('cedula')
        generoUser = request.data.get('genero')
        # fotoUser = request.FILES.get('foto')

        data["nombre"] = nombreUser
        data["apellido"] = apellidosUser
        data["telefono"] = telefonoUser
        data["ciudad"] = ciudadUser
        data["cedula"] = cedulaUser
        data["genero"] = generoUser
        # data["foto"]= fotoUser
        data["email"] = request.data.get('email')
        data["pass"] = request.data.get('password')

        # try:
        datoCreado = Datos.objects.create(user=usuario, tipo=models.Group.objects.get(
            name='Administrador'), nombres=nombreUser, apellidos=apellidosUser, telefono=telefonoUser, genero=generoUser, ciudad=ciudadUser, cedula=cedulaUser)
        datoCreado.foto = request.FILES.get('foto')
        datoCreado.save()
        admin = Administrador.objects.create(user_datos=datoCreado)
        serializer = AdministradorSerializer(admin)
        token = Token.objects.get(user=datoCreado.user).key
        data['token'] = token
        data['sucess'] = True
        return Response(data)

        # except:
        #     data['error'] = "Erro al crear Administrador!."
        #     return Response(data)

    def put(self, request):
        ident = request.GET.get('id')
        admin = Administrador.objects.get(id=ident)
        persona = Datos.objects.get(id=admin.user_datos.id)
        admin.estado = request.data.get('estado')
        persona.estado = request.data.get('estado')
        persona.save()
        admin.save()
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, id, format=None):
        administrador = Administrador.objects.get(id=id)
        administrador.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Admin_Details(APIView):

    def get(self, request, pk, format=None):

        administrador = Administrador.objects.get(id=pk)
        serializer = AdministradorSerializer(administrador)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        data = {}
        admin = Administrador.objects.get(id=request.data.get('id'))
        persona = Datos.objects.get(user__email=request.data.get('email'))
        user = User.objects.get(email=request.data.get('email'))

        if persona:

            if User.objects.filter(email=request.data.get('emailNuevo')).exists():
                userExistente = User.objects.get(
                    email=request.data.get('emailNuevo'))
                if (user.id != userExistente.id):
                    data['error'] = 'Email ya registrado'
                    return Response(data)
                else:
                    user.email = userExistente.email
            user.email = request.data.get('emailNuevo')
            user.username = request.data.get('emailNuevo')
            user.save()
            if request.data.get('rol'):
                if user.groups.all().count() > 0:
                    grupo = Group.objects.get(id=user.groups.all()[0].id)
                    grupo.user_set.remove(user)
                grupo = Group.objects.get(name=request.data.get('rol'))
                grupo.user_set.add(user)
            persona.nombres = request.data.get('nombres')
            persona.ciudad = request.data.get('ciudad')
            persona.cedula = request.data.get('cedula')
            persona.apellidos = request.data.get('apellidos')
            persona.telefono = request.data.get('telefono')
            persona.genero = request.data.get('genero')
            # persona.estado = request.data.get('estado')
            # admin.estado = request.data.get('estado')
            admin.save()
            persona.codigo_invitacion = request.data.get('codigo_invitacion')
            persona.puntos = request.data.get('puntos')
            if 'foto' in request.FILES:
                foto_user = request.FILES.get('foto')
                persona.foto = foto_user
            persona.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        administrador = Administrador.objects.get(id=pk)
        administrador.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
   # permission_classes = (IsAuthenticated,)
   # authentication_class = (TokenAuthentication)
    def get(self, request, user, format=None):
        proveedor_profesiones = Profesion_Proveedor.objects.filter(
            proveedor__user_datos__user__username=user) | Profesion_Proveedor.objects.filter(proveedor__user_datos__user__email=user)
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
        print('JSONRenderer().render(serializer.data)')
        print(JSONRenderer().render(serializer.data))
        return Response(serializer.data)

    def post(self, request, user, format=None):
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
            proveedor = Proveedor.objects.get(user_datos__user__username=user)
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
                active=True, user__username=user)
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


class Solicitud_Servicio_User(APIView):
 # permission_classes = (IsAuthenticated,)
   # authentication_class = (TokenAuthentication)
    def get(self, request, ID_servicio, user, format=None):
        solicitud_servicio = Envio_Interesados.objects.filter(
            solicitud__servicio=ID_servicio, solicitud__estado=True, proveedor__user_datos__user__username=user, interesado=False).order_by('-fecha_creacion')
        solicitudes = []
        for solicitud in solicitud_servicio:
            solicitudes.append(solicitud.solicitud)
        serializer = SolicitudSerializer(solicitudes, many=True)
        # print(JSONRenderer().render(serializer.data))
        return Response(serializer.data)


class Service(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)

    def get(self, request, category_ID,  format=None):
        servicios = Servicio.objects.all().filter(categoria=category_ID)
        serializer = ServicioSerializer(servicios, many=True)
        return Response(serializer.data)


class Envio(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, solicitud_ID, format=None):
        envio_interesado = Envio_Interesados.objects.all().filter(
            solicitud=solicitud_ID, interesado=False)
        serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
        return Response(serializer.data)

    def put(self, request, user, solicitud_ID, format=None):
        solicitud = Solicitud.objects.get(id=solicitud_ID)
        esNuevo = solicitud.adjudicar
        solicitante = solicitud.solicitante
        envio_interesado = Envio_Interesados.objects.all().get(
            solicitud=solicitud_ID, proveedor__user_datos__user__username=user)
        serializer = Envio_InteresadosSerializer(
            envio_interesado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Notificacion al solicitante que realizo la oferta
            if esNuevo:
                titles = 'Ha cambiado el precio del servicio de ' + \
                    solicitud.servicio.nombre + ' que solicitaste.'
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__username=solicitante.user_datos.user.email)
                tokend = devices.values_list('registration_id', flat=True)

                dataNot={"ruta": "/historial",
                          "descripcion": "Ha cambiado el precio del siguiente servicio: " + solicitud.servicio.nombre}

                tokens=list(tokend)
                send_notificationF(tokens,titles,bodys,dataNot)

            else:
                titles = 'Tienes una nueva oferta en el servicio de ' + \
                    solicitud.servicio.nombre + ' que solicitaste.'
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__username=solicitante.user_datos.user.email)
                tokend = devices.values_list('registration_id', flat=True)
                dataNot={"ruta": "/historial",
                          "descripcion": "Ha recibido una oferta en el siguiente servicio: " + solicitud.servicio.nombre}
                tokens=list(tokend)
                send_notificationF(tokens,titles,bodys,dataNot)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user, solicitud_ID, format=None):
        respuesta = {}
        try:
            instance = Envio_Interesados.objects.get(
                solicitud=solicitud_ID, proveedor__user_datos__user__username=user)
            instance.delete()
            respuesta['success'] = True
            respuesta['message'] = 'Se ha eliminado el objeto Envio_Interesados correctamente de la base de datos'
            return Response(respuesta)
        except:
            respuesta['success'] = False
            respuesta['message'] = 'No se ha encontrado el objeto Envio_Interesados en la base de datos'
            return Response(respuesta)


class Notificacion_Chat(APIView):
    def post(self, request, format=None):
        remitente = request.data.get("remitente")
        remitente_nombre= Datos.objects.get(id=remitente)
        titles = 'Nuevo Mensaje de ' + remitente_nombre.nombres + remitente_nombre.apellidos
        isSolicitante = request.data.get("isSolicitante")
        bodys = request.data.get("message")
        user = request.data.get("user")
        url = request.data.get("url")
        ruta = ""
        if isSolicitante:
            ruta = "/main-tabs/chat"
            dato_prov = Datos.objects.get(user_id=user)
            dato_id_prov = dato_prov.user_id
            devices = FCMDevice.objects.filter(active=True, user_id=dato_id_prov)
            tokend = devices.values_list('registration_id', flat=True)
            tokens=list(tokend)
            data={"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}
            send_notificationF(tokens,titles,bodys,data)
        else:
            ruta = "/main/chat"
            data={"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}

            send_notificationF(tokens,titles,bodys,data)

        return Response(user)


class Notificacion_Chat_Proveedor(APIView):
    def post(self, request, format=None):
        # try:
        remitente = request.data.get("remitente")
        print(f"Remitente ID: {remitente}")

        try:
            remitente_nombre_prov = Datos.objects.get(user_id=remitente)
            print(f"Remitente Nombre: {remitente_nombre_prov.nombres}")
        except Datos.DoesNotExist:
            print(f"Error: Datos object with user_id {remitente} does not exist.")
            return Response({"error": "Remitente not found"}, status=404)

        titles = 'Nuevo Mensaje de ' + remitente_nombre_prov.nombres
        print(f"Notification Title: {titles}")

        getUsuario = request.data.get("user")
        print(f"GetUsuario: {getUsuario}")

        bodys = request.data.get("message")
        print(f"Body: {bodys}")

        try:
            solicitante = Solicitante.objects.get(user_datos__id=getUsuario)
            print(f"Solicitante: {solicitante}")
        except Solicitante.DoesNotExist:
            print(f"Error: Solicitante with user_datos__id {getUsuario} does not exist.")
            return Response({"error": "Solicitante not found"}, status=404)

        soli_id = solicitante.user_datos_id
        print(f"Soli ID: {soli_id}")

        url = request.data.get("url")
        print(f"URL: {url}")

        ruta = "/main/chat"
        print(f"Ruta: {ruta}")

        try:
            dato_soli = Datos.objects.get(id=soli_id)
            print(f"Dato Soli: {dato_soli}")
        except Datos.DoesNotExist:
            print(f"Error: Datos object with ID {soli_id} does not exist.")
            return Response({"error": "Datos not found"}, status=404)

        dato_id_soli = dato_soli.user_id
        print(f"Dato ID Soli: {dato_id_soli}")

        devices = FCMDevice.objects.filter(active=True, user_id=dato_id_soli)
        if not devices.exists():
            print("Error: No devices found.")
            return Response({"error": "No devices found"}, status=404)

        tokend = devices.values_list('registration_id', flat=True)
        tokens = list(tokend)
        print(f"Tokens: {tokens}")

        data = {"url": url, "ruta": ruta, "descripcion": "Tiene un Mensaje nuevo"}
        print(f"Notification Data: {data}")

        # Assuming send_notificationF logs or throws exceptions if something goes wrong
        try:
            send_notificationF(tokens, titles, bodys, data)
            print("Notification sent successfully.")
        except Exception as e:
            print(f"Error sending notification: {e}")

        return Response(getUsuario)


        # except Solicitante.DoesNotExist:
        #     print("Error: Solicitante not found for user ID:", getUsuario)
        #     return Response({"error": "Solicitante not found"}, status=404)

        # except Datos.DoesNotExist as e:
        #     print("Error: Datos not found. Details:", str(e))
        #     return Response({"error": "Datos not found"}, status=404)

        # except Exception as e:
        #     print("Unexpected error occurred:", str(e))
        #     return Response({"error": str(e)}, status=500)



class Notificacion_General(APIView):
    def post(self, request, format=None):
        bodys = request.data.get("message")
        user = request.data.get("user")
        titles = request.data.get("title")
        devices = FCMDevice.objects.filter(active=True, user_id=user)
        tokend = devices.values_list('registration_id', flat=True)

        data={"ruta": "Historial", "descripcion": "Proveedor Interesado"}
        tokens=list(tokend)
        send_notificationF(tokens,titles,bodys,data)

        return Response(user)

#! Paginar


class Proveedores_Interesados(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, id_proveedor_user_datos, format=None):
        envio_interesado = Envio_Interesados.objects.all().filter(
            proveedor__user_datos_id=id_proveedor_user_datos, interesado=True).order_by('-fecha_creacion')
        serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
        return Response(serializer.data)


class Proveedores_InteresadosFecha(APIView):
    def post(self, request, id_proveedor_user_datos, format=None):
        envio_interesado = Envio_Interesados.objects.all().filter(
            proveedor__user_datos_id=id_proveedor_user_datos, fecha_creacion__gte=request.data.get('dateInicio'), fecha_creacion__lte=request.data.get('dateFinal'), interesado=True).order_by('-fecha_creacion')

        serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
        return Response(serializer.data)

# Paginados


class Proveedores_Interesados_Pag(APIView, MyPaginationMixin):
    queryset = Envio_Interesados.objects.all()
    serializer_class = Envio_InteresadosSerializer
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(
                proveedor__user_datos_id=id_proveedor_user_datos, interesado=True).order_by('-fecha_creacion'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes pasadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class Proveedores_Interesados_Efectivo_Pag(APIView, MyPaginationMixin):
    queryset = Envio_Interesados.objects.all()
    serializer_class = Envio_InteresadosSerializer
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(
                proveedor__user_datos_id=id_proveedor_user_datos, interesado=True, solicitud__tipo_pago__nombre='Efectivo').order_by('-fecha_creacion'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes pasadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class Proveedores_Interesados_Tarjeta_Pag(APIView, MyPaginationMixin):
    queryset = Envio_Interesados.objects.all()
    serializer_class = Envio_InteresadosSerializer
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        try:
            page = self.paginate_queryset(self.queryset.filter(
                proveedor__user_datos_id=id_proveedor_user_datos, interesado=True, solicitud__tipo_pago__nombre='Tarjeta').order_by('-fecha_creacion'))
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            data = {}
            data['message'] = "No se pudo obtener la lista de solicitudes pasadas: " + \
                str(e)
            data['success'] = False
            return Response(data)


class SolicitudesPagadas(APIView):
    def get(self, request, id, format=None):
        envio_interesado = Envio_Interesados.objects.all().filter(proveedor__user_datos_id=id,
                                                                  interesado=True, solicitud__pagada=True).order_by('-fecha_creacion')
        serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
        return Response(serializer.data)


class Envio_Interesado(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, solicitud_ID, format=None):
        datos = []
        envio_interesado = Envio_Interesados.objects.all().filter(
            solicitud=solicitud_ID, interesado=True)
        serializer = Envio_InteresadosSerializer(envio_interesado, many=True)
        for solicitud in serializer.data:
            data = {}
            data['id'] = solicitud['proveedor']['user_datos']['user']['id']
            data['username'] = solicitud['proveedor']['user_datos']['user']['username']
            data['nombres'] = solicitud['proveedor']['user_datos']['nombres']
            data['apellidos'] = solicitud['proveedor']['user_datos']['apellidos']
            data['ciudad'] = solicitud['proveedor']['user_datos']['ciudad']
            data['telefono'] = solicitud['proveedor']['user_datos']['telefono']
            data['genero'] = solicitud['proveedor']['user_datos']['genero']
            data['foto'] = solicitud['proveedor']['user_datos']['foto']
            data['oferta'] = solicitud['oferta']
            data['descripcion'] = solicitud['proveedor']['descripcion']
            data['rating'] = solicitud['proveedor']['rating']
            data['servicios'] = solicitud['proveedor']['servicios']
            datos.append(data)

        return Response(datos)


class ChangePassword(APIView):
    def get(self, request, *args, **kwargs):
        access_security = self.kwargs["access_security"]
        if Datos.objects.filter(security_access=access_security).exists():
            return super.get(request, *args, **kwargs)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            persona = Datos.objects.get(
                security_access=self.kwargs["access_security"])
            if persona is not None:
                persona = Datos.objects.get(
                    security_access=self.kwargs["access_security"])
                proveedor = Proveedor.objects.get(user_datos=persona.nombres)
                persona.user.set_password(request.data.get('password'))
                persona.user.save()
                proveedor.estado = True
                proveedor.save()
                persona.security_access = uuid.uuid4()
                persona.save()
                data['token'] = Token.objects.get(user=persona.user).key
                data['username'] = persona.user.username
                return Response(data)
            else:
                data['error'] = "Usuario no encontrado"
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            data['error'] = str(e)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
    def post(self, request, format=None):
        res_tipo = request.data.get('tipo')
        data = {}
        form = AuthenticationForm(data=request.data)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                do_login(request, user)
                usuario = Datos.objects.get(user=user)
                tipo = usuario.tipo.name
                if (tipo == res_tipo and usuario.estado == True):
                    token, _ = Token.objects.get_or_create(user=user)
                    if (tipo == 'Proveedor'):
                        proveedor = Proveedor.objects.get(user_datos=usuario)
                        if (proveedor.estado):
                            # data['token']=token = Token.objects.get(user=user).key
                            data['token'] = token.key
                            data['active'] = True
                            data['form'] = request.data
                            return Response(data)
                        else:
                            data['clave'] = usuario.security_access
                            # data['token']=token = Token.objects.get(user=user).key
                            data['token'] = token.key
                            data['active'] = True
                            data['form'] = request.data
                            return Response(data)
                    elif (tipo == 'Solicitante'):
                        data['active'] = True
                        data['token'] = token = Token.objects.get(
                            user=user).key
                        data['form'] = request.data
                        return Response(data)
                #elif (tipo == res_tipo and usuario.estado == False):
                #    data['active'] = False
                #    data['form'] = request.data
                #    return Response(data)
                else:
                    data['error'] = 'Usuario no permitido'
                    data['active'] = True
                    data['form'] = request.data
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data['error'] = 'Error de formulario login'
            data['active'] = True
            data['form'] = request.data
            form = AuthenticationForm()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class LoginAdmin(APIView):
    def post(self, request, format=None):
        print("entra aca")
        res_tipo = request.data.get('tipo')
        data = {}
        form = AuthenticationForm(data=request.data)
        print(form)

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        print(username)
        print(password)
        user = authenticate(username=username, password=password)
        print(user)
        print("autentico")
        if user is not None:
            print("No es none")
            do_login(request, user)
            print("login?")
            usuario = Datos.objects.get(user=user)
            print(usuario)
            print(usuario.tipo)
            print("le hace get")
            tipo = usuario.tipo.name
            print("tipo "+tipo)
            print("res_tipo "+res_tipo)
            if (tipo == res_tipo and usuario.estado == True):
                print("logro entrar")
                token, _ = Token.objects.get_or_create(user=user)
                print(token)
                if (tipo == 'Administrador'):
                    print("tipo "+tipo)
                    admin = Administrador.objects.get(user_datos=usuario)
                    if (admin.estado):
                        # data['token']=token = Token.objects.get(user=user).key
                        data['token'] = token.key
                        data['active'] = True
                        data['form'] = request.data
                        print("ACABA")
                        return Response(data)
                    else:
                        data['clave'] = usuario.security_access
                        # data['token']=token = Token.objects.get(user=user).key
                        data['token'] = token.key
                        data['active'] = True
                        data['form'] = request.data
                        return Response(data)
            elif (tipo == res_tipo and usuario.estado == False):
                data['active'] = False
                data['form'] = request.data
                print("estado == false")
                return Response(data)
            else:
                data['error'] = 'Usuario no permitido'
                data['active'] = True
                data['form'] = request.data
                print("tipo != res.tipo")
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

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

    def get(self, request, identifier, format=None):
        # id -> username
        tarjetas = Tarjeta.objects.all().filter(
            solicitante__user_datos__user__username=identifier)
        serializer = TarjetaSerializer(tarjetas, many=True)
        return Response(serializer.data)

    def delete(self, request, identifier, format=None):
        # Aqui el id es el de la tarjeta
        data = {}
        data['success'] = False
        try:
            tarjeta = Tarjeta.objects.get(id=identifier)
        except:
            data['error'] = "No se encontro la tarjeta"
            return Response(data)
        else:
            try:
                tarjeta.delete()
                data['success'] = True
                data['msg'] = "Se elimino exitosamente"
                return Response(data)
            except:
                data['error'] = "No se pudo borrar la tarjeta"
                return Response(data)


class Tarjetas(APIView):

    def get(self, request, format=None):
        data = {}
        tarjetas = Tarjeta.objects.all()
        serializer = TarjetaSerializer(tarjetas, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        data['success'] = False
        user_titular = request.data.get('titular')
        user_vencimiento = request.data.get('fecha_vencimiento')
        user_solicitante = request.data.get('user')
        user_cvv = request.data.get('cvv')
        user_numero = request.data.get('numero')
        brand = request.data.get('brand')
        token_card = request.data.get('token_card')
        status = request.data.get('status')
        typ = request.data.get('type')

        try:
            solicitante = Solicitante.objects.get(
                user_datos__user__username=user_solicitante)
        except:
            data['solicitante'] = user_solicitante
            data['error'] = "No se encontró el solicitante"
            return Response(data)
        else:
            try:
                tarjeta = Tarjeta.objects.create(token=token_card, code=status, fecha_vencimiento=user_vencimiento,
                                                 cvv=user_cvv, numero=user_numero, titular=user_titular, solicitante=solicitante, brand=brand, tipo=typ)
                data['success'] = True
                data['msg'] = "La tarjeta se ha guardado exitosamente"
                serializer = TarjetaSerializer(tarjeta)
                data['tarjeta'] = serializer.data
                return Response(data)

            except:
                data['error'] = "No se pudo guardar la tarjeta"
                return Response(data)


class Datos_Users(APIView):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    def get(self, request, id, format=None):
        dato = Datos.objects.all().filter(user__id=id)
        serializer = DatosSerializer(dato, many=True)
        return Response(serializer.data)


class Complete_Data_User(APIView):
    def put(self, request, username, format=None):
        data = {}
        data['success'] = False
        try:
            dato = Datos.objects.get(user__username=username)
        except:
            data['error'] = "No se encontró el usuario"
            return Response(data)
        else:
            cedula_user = request.data.get('cedula')
            ciudad_user = request.data.get('ciudad')
            try:
                dato.ciudad = ciudad_user
                dato.cedula = cedula_user

                dato.save()
                data['success'] = True
                data['msg'] = "Se guardaron los cambios"
                return Response(data)
            except:
                data['error'] = "No se pudo actualizar los datos"
                return Response(data)


class Notificaciones(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    # def get(self, request, format=None):
    #     notificacion = Notificacion.objects.all().filter()
    #     serializer = NotificacionSerializer(notificacion, many=True)
    #     return Response(serializer.data)

    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    # def post(self, request, format=None):

    #     data = {}
    #     titulo = request.data.get('titulo')
    #     descripcion = request.data.get('descripcion')
    #     imagen = request.data.get('imagen')

    #     try:
    #         notificacionCreada = Notificacion.objects.create(titulo = titulo, descripcion = descripcion , imagen = imagen)
    #     except:
    #         data["error"]= "Notificacion no creada"
    #         return Response(data)


    def post(self, request, format=None):
        data = {}
        user = User.objects.first()
        nombre = request.data.get('nombre')
        titles = request.data.get('titulo')
        descripcion = request.data.get('descripcion')
        tipo_proveedores = request.data.get('tipo_proveedores')
        frecuencia = request.data.get('frecuencia')
        imagen = request.FILES.get('imagen')
        ruta = request.data.get('ruta')
        ini = request.data.get('fecha_iniciacion')
        exp = request.data.get('fecha_expiracion')
        hora=request.data.get('hora')

        notificacion = Notificacion.objects.create(
            user=user,
            nombre = nombre,
            titulo=titles,
            descripcion=descripcion,
            tipo_proveedores=tipo_proveedores,
            frecuencia=frecuencia,
            ruta=ruta,
            imagen=imagen,
            fecha_iniciacion=ini,
            fecha_expiracion=exp,
            hora=hora,
        )
        notificacion.save()
        dataNot = {}
        if imagen is not None:
            dataNot["imagen"] = notificacion.imagen.url
        dataNot["ruta"] = ruta
        dataNot["descripcion"] = descripcion
        try:
            devices = FCMDevice.objects.filter(active=True)
            tokend = devices.values_list('registration_id', flat=True)

            tokens=list(tokend)
            send_notificationF(tokens,titles,descripcion,dataNot)

            data['success'] = True
            data['message'] = "La notificación ha sido creada correctamente."
            serializer = NotificacionSerializer(notificacion)
            data['notificacion'] = serializer.data
            return Response(data)
        except Exception as e:
            notificacion.delete()
            data['success'] = False
            data['message'] = f"Hubo un error al enviar la notificación: {str(e)}"
            return Response(data)

    def put(self, request, id, format=None):
        try:
            id = int(id)
            notificacion = Notificacion.objects.get(id=id)
            serializer = NotificacionSerializer(notificacion, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            print("Errores de validación:", serializer.errors)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Notificacion.DoesNotExist:
            return Response({"error": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self,  request, id, format=None):
        data = {}
        try:
            notificacion= Notificacion.objects.get(id=id)
            notificacion.delete()

            devices = FCMDevice.objects.filter(active=True)
            tokend = devices.values_list('registration_id', flat=True)
            tokens=list(tokend)
            titles = "Notificacion eliminada:" + notificacion.titulo
            descripcion = notificacion.descripcion
            dataNot = {}
            dataNot["descripcion"] = descripcion

            send_notificationF(tokens,titles,descripcion,dataNot)
            data['success'] = True
            data['message'] = "Se ha eliminado la notificación exitosamente."
            return Response(data, status=status.HTTP_200_OK)
        except:
            data['success'] = False
            data['message'] = "La notificación no fue encontrada en la base de datos."
            return Response(data, status=status.HTTP_204_NO_CONTENT)

class Notificaciones_Details(APIView):

    def get(self, request, pk, format=None):

        noti= Notificacion.objects.get(id=pk)
        serializer = NotificacionSerializer(noti)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        noti = Notificacion.objects.get(id=ident)
        noti.estado = request.data.get('estado')
        noti.save()
        return Response(status=status.HTTP_200_OK)

    def post(self, request):
        pk = request.GET.get('id')
        prove_select = Notificacion.objects.get(id=pk)
        serializer = NotificacionSerializer(prove_select)
        # Obtener el tipo de proveedor desde la notificación masiva
        tipo_proveedor = prove_select.tipo_proveedores  # Suponiendo que tipo_proveedores es un campo en NotificacionMasiva

        # Preparar los datos de la notificación
        descripcion = prove_select.descripcion
        dataNot = {
            "descripcion": descripcion
        }

        # Filtrar proveedores cuya profesión coincida con el tipo de proveedor
        proveedores = Proveedor.objects.all()
        for proveedor in proveedores:
            if ',' in proveedor.profesion:
                profesiones = proveedor.profesion.split(",")
                if tipo_proveedor in profesiones:
                    print(f'Proveedor {proveedor} tiene la profesión {tipo_proveedor}')
                    p_user_id = proveedor.user_datos.id
                    print("id", p_user_id)
                    datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
                    user = User.objects.get(id=datos_prov.user.id)
                    u_id = user.id
                    print("idp", u_id)

                    devices = FCMDevice.objects.filter(active=True, user_id=u_id)
                    # Obtener los tokens de esos dispositivos
                    tokens = devices.values_list('registration_id', flat=True)

                    if tokens:
                        # Enviar la notificación solo si existen tokens
                        send_notificationF(list(tokens), prove_select.titulo, descripcion, dataNot)
                    else:
                        # Si no hay dispositivos activos para este proveedor, puedes registrar un error o continuar
                        print(f"No se encontraron dispositivos activos para el proveedor con user_id {p_user_id}")
            else:
                # Si la profesión no tiene comas, es un solo valor
                if proveedor.profesion == tipo_proveedor:
                    print(f'Proveedor {proveedor} tiene la profesión {tipo_proveedor}')
                    p_user_id = proveedor.user_datos.id
                    print("id", p_user_id)
                    datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
                    user = User.objects.get(id=datos_prov.user.id)
                    u_id = user.id
                    print("idp", u_id)

                    devices = FCMDevice.objects.filter(active=True, user_id=u_id)
                    # Obtener los tokens de esos dispositivos
                    tokens = devices.values_list('registration_id', flat=True)

                    if tokens:
                        # Enviar la notificación solo si existen tokens
                        send_notificationF(list(tokens), prove_select.titulo, descripcion, dataNot)
                    else:
                        # Si no hay dispositivos activos para este proveedor, puedes registrar un error o continuar
                        print(f"No se encontraron dispositivos activos para el proveedor con user_id {p_user_id}")

        return Response({"message": "Notificación enviada correctamente a los proveedores seleccionados."}, status=status.HTTP_200_OK)

class Grupos(APIView):
    def get(self, request, format=None):

        grupos = Group.objects.all()
        serializer = GroupSerializer(grupos, many=True)
        return Response(serializer.data)


class Promociones(APIView):
    def get(self, request, format=None):
        today = date.today()
        enddate = today + timedelta(days=30)
        promociones = Promocion.objects.all().filter(
            fecha_expiracion__range=[today, enddate])
        serializer = PromocionSerializer(promociones, many=True)
        return Response(serializer.data)

    def delete(self, request, id, format=None):
        promocion = Promocion.objects.get(id=id)
        promocion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        data = {}
        data['success'] = False

        code = request.data.get('codigo')
        title = request.data.get('titulo')
        desc = request.data.get('descripcion')
        ini = request.data.get('fecha_iniciacion')
        exp = request.data.get('fecha_expiracion')
        descuent = request.data.get('porcentaje')
        cant = request.data.get('cantidad')
        partic = request.data.get('participantes')
        photo = request.data.get('foto')
        type_category = request.data.get('tipo_categoria')

        try:
            promocion = Promocion.objects.create(titulo=title, descripcion=desc, fecha_expiracion=exp, porcentaje=descuent,
                                                 codigo=code, fecha_iniciacion=ini, participantes=partic, foto=photo, tipo_categoria=type_category, cantidad=cant)

        except:
            data['error'] = "No se pudo crear la promoción"
            return Response(data)
        else:

            try:
                for categoria in request.POST.getlist('categorias'):
                    categ = Categoria.objects.all().filter(nombre=categoria)
                    promcat = PromocionCategoria.objects.create(
                        categoria=categ[0], promocion=promocion)
            except:
                promocion.delete()
                data['error'] = "No se pudo asignar las categorias"
                return Response(data)
            else:

                titles = 'Nueva Promoción '+promocion.titulo
                bodys = promocion.descripcion
                devices = FCMDevice.objects.filter(
                    active=True, user__groups__name='Solicitante')
                tokend = devices.values_list('registration_id', flat=True)

                dataNot={"ruta": "Home",
                          "descripcion": "Se ha creado una nueva promoción"}
                tokens=list(tokend)
                send_notificationF(tokens,titles,bodys,dataNot)

                data['success'] = True
                data['msg'] = "La promoción se ha creado exitosamente"
                serializer = PromocionSerializer(promocion)
                data['promocion'] = serializer.data
                return Response(data)

    def put(self, request, id, format=None):
        data = {}
        data['success'] = False
        code = request.data.get('codigo')
        title = request.data.get('titulo')
        desc = request.data.get('descripcion')
        ini = request.data.get('fecha_iniciacion')
        exp = request.data.get('fecha_expiracion')
        descuent = request.data.get('porcentaje')
        cant = request.data.get('cantidad')
        partic = request.data.get('participantes')
        # photo = request.data.get('foto') #
        if request.data.get('foto') is not None:
            photo = request.data.get('foto')

        type_category = request.data.get('tipo_categoria')

        try:
            promocion = Promocion.objects.get(codigo=code)
        except:
            data['error'] = "No se encontró la promoción"
            return Response(data)
        else:
            promocion.titulo = title
            promocion.descripcion = desc
            promocion.participantes = partic
            promocion.porcentaje = descuent
            promocion.cantidad = cant
            promocion.fecha_iniciacion = ini
            promocion.fecha_expiracion = exp
            # promocion.foto = photo
            if request.data.get('foto') is not None:
                promocion.foto = photo

            promocion.save()
            try:

                data['code'] = 2
                # Primero creo las que no existian

                catnom = []

                for promctg in PromocionCategoria.objects.all().filter(promocion__codigo=code):
                    catnom.append(promctg.categoria.nombre)

                for cat in request.POST.getlist('categorias'):
                    if cat not in catnom:
                        categ = Categoria.objects.get(nombre=cat)
                        created = PromocionCategoria.objects.create(
                            promocion=promocion, categoria=categ)

                data['code'] = 3
                # elimino las que ya no existen
                promctg = PromocionCategoria.objects.all().filter(promocion__codigo=code)

                for ctg in promctg:
                    if ctg.categoria.nombre not in request.POST.getlist('categorias'):
                        cat = PromocionCategoria.objects.filter(
                            categoria=ctg.categoria)
                        cat.delete()
            except:
                data['error'] = "No se pudo actualizar las categorias"
                return Response(data)
            else:
                data['success'] = True
                data['msg'] = "La promoción se ha actualizado exitosamente"
                serializer = PromocionSerializer(promocion)
                data['promocion'] = serializer.data
                return Response(data)


class Promocion_Details(APIView):

    def get(self, request, pk, format=None):

        promocion = Promocion.objects.get(id=pk)
        serializer = PromocionSerializer(promocion)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        promo = Promocion.objects.get(id=ident)
        promo.estado = request.data.get('estado')
        promo.save()
        return Response(status=status.HTTP_200_OK)


class Cupones(APIView):
    def get(self, request, format=None):
        today = date.today()
        enddate = today + timedelta(days=30)
        cupones = Cupon.objects.all().filter(
            fecha_expiracion__range=[today, enddate])
        serializer = CuponSerializer(cupones, many=True)
        return Response(serializer.data)

    def delete(self, request, id, format=None):
        cupon = Cupon.objects.get(id=id)
        cupon.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        data = {}
        data['success'] = False
        code = request.data.get('codigo')
        title = request.data.get('titulo')
        desc = request.data.get('descripcion')
        ini = request.data.get('fecha_iniciacion')
        exp = request.data.get('fecha_expiracion')
        descuent = request.data.get('porcentaje')
        partic = request.data.get('participantes')
        cant = request.data.get('cantidad')
        puntos = request.data.get('puntos')
        photo = request.data.get('foto')
        type_category = request.data.get('tipo_categoria')

        try:
            cupon = Cupon.objects.create(titulo=title, descripcion=desc, fecha_expiracion=exp, porcentaje=descuent, participantes=partic,
                                         codigo=code, fecha_iniciacion=ini, puntos=puntos, foto=photo, tipo_categoria=type_category, cantidad=cant)

        except:
            data['error'] = "No se pudo crear el cupon {str(e)}"
            return Response(data)
        else:

            try:
                for type_category in request.POST.getlist('categorias'):
                    categ = Categoria.objects.all().filter(nombre=type_category)
                    CuponCategoria.objects.create(
                    categoria=categ[0], cupon=cupon)

            except:
                cupon.delete()
                data['error'] = "No se pudo asignar las categorias"
                return Response(data)
            else:

                titles = 'Nuevo Cupón de descuento '+cupon.titulo
                bodys = cupon.descripcion
                devices = FCMDevice.objects.filter(
                    active=True, user__groups__name="Solicitante")
                tokend = devices.values_list('registration_id', flat=True)

                dataNot={"ruta": "/promociones",
                          "descripcion": "Se encuentra disponible un nuevo cupón!"}
                tokens=list(tokend)
                send_notificationF(tokens,titles,bodys,dataNot)

                data['success'] = True
                data['msg'] = "El cupon se ha creado exitosamente"
                serializer = CuponSerializer(cupon)
                data['cupon'] = serializer.data
                return Response(data)

    def put(self, request, id, format=None):
        data = {}
        data['success'] = False
        code = request.data.get('codigo')
        title = request.data.get('titulo')
        desc = request.data.get('descripcion')
        ini = request.data.get('fecha_iniciacion')
        exp = request.data.get('fecha_expiracion')
        descuent = request.data.get('porcentaje')
        partic = request.data.get('participantes')
        cant = request.data.get('cantidad')
        puntos = request.data.get('puntos')
        # photo = request.data.get('foto') #
        if request.data.get('foto') is not None:
            photo = request.data.get('foto')
        type_category = request.data.get('tipo_categoria')

        try:
            cupon = Cupon.objects.get(codigo=code)
        except:
            data['success'] = False
            data['error'] = "No se encontró el cupon"
            return Response(data)
        else:
            cupon.titulo = title
            cupon.descripcion = desc
            cupon.puntos = puntos
            cupon.porcentaje = descuent
            cupon.cantidad = cant
            cupon.fecha_iniciacion = ini
            cupon.fecha_expiracion = exp
            cupon.participantes = partic
            cupon.tipo_categoria = type_category
            if request.data.get('foto') is not None:
                cupon.foto = photo
            cupon.save()

            try:
                data['code'] = 2
                # Primero creo las que no existian
                catnom = []
                for cuponctg in CuponCategoria.objects.all().filter(cupon__codigo=code):
                    catnom.append(cuponctg.categoria.nombre)

                if type_category not in catnom:
                    categ = Categoria.objects.get(nombre=type_category)
                    created = CuponCategoria.objects.create(
                        cupon=cupon, categoria=categ)

                data['code'] = 3
                # Se eliminan los objetos CuponCategoria que ya no existen
                cupones_categoria = CuponCategoria.objects.all().filter(cupon__codigo=code)
                for cupon_categoria in cupones_categoria:
                    if cupon_categoria.categoria.nombre != type_category:
                        cupon_categoria.delete()
            except:
                data['success'] = False
                data['error'] = "No se pudo actualizar las categorias"
                return Response(data)
            else:
                data['success'] = True
                data['msg'] = "El cupón se ha actualizado exitosamente"
                serializer = CuponSerializer(cupon)
                data['cupon'] = serializer.data
                return Response(data)


class Cupon_Details(APIView):

    def get(self, request, pk, format=None):

        cupon = Cupon.objects.get(id=pk)
        serializer = CuponSerializer(cupon)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        cupo = Cupon.objects.get(id=ident)
        cupo.estado = request.data.get('estado')
        cupo.save()
        return Response(status=status.HTTP_200_OK)


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


class AllCuponesCategoria(APIView):
    def get(self, request, format=None):
        cupones = CuponCategoria.objects.all()
        cupones = CuponCategoria.objects.all().filter(cupon__fecha_expiracion__gte = datetime.datetime.today())
        cupones = cupones.filter(cupon__fecha_iniciacion__lte = datetime.datetime.today())
        serializer = CuponCategoriaSerializer(cupones, many=True)
        return Response(serializer.data)


class PagosTarjeta(APIView):
    def post(self, request, format=None):
        data = {}
        data['success'] = False
        user = request.data.get('username')
        tarjeta_user = request.data.get('tarjeta')  # numero de la tarjeta
        promotion = request.data.get('promocion')  # codigo de la promocion
        amount = request.data.get('valor')
        desc = request.data.get('descripcion')
        descuento = request.data.get('descuento')
        impuesto = request.data.get('impuesto')
        referencia = request.data.get('referencia')
        solicitud_ID = request.data.get('solicitud')  # id de la solicitud
        carrier_ID = request.data.get('carrier')
        carrier_c = request.data.get('carrier_code')
        carg_Pay = request.data.get('cargo_paymentez')
        carg_Banc = request.data.get('cargo_banco')
        carg_Sis = request.data.get('cargo_sistema')
        us = request.data.get('usuario')
        serv = request.data.get('servicio')
        prov = request.data.get('proveedor')
        prov_phone = request.data.get('prov_phone')
        prov_email = request.data.get('prov_email')

        try:
            data['detail'] = "User"
            usuario = User.objects.get(username=user)
            data['detail'] = "Tarjeta"
            tarjeta = Tarjeta.objects.get(id=tarjeta_user)
            data['detail'] = "Promocion"
            promocion = Promocion.objects.get(codigo=promotion)
            data['detail'] = "Solicitud"
            solicitud = Solicitud.objects.get(id=solicitud_ID)

        except Exception as e:
            # data['error']="No se encontraron los datos de tarjeta/promocion"
            data['error'] = str(e)
            return Response(data)

        else:
            try:
                data['detail'] = "pago_tarjeta"
                pago_tarjeta_user = PagoTarjeta.objects.create(user=usuario, tarjeta=tarjeta, carrier_id=carrier_ID, carrier_code=carrier_c, promocion=promocion, valor=amount, descripcion=desc, impuesto=impuesto, solicitud=solicitud,
                                                               referencia=referencia, cargo_paymentez=carg_Pay, cargo_banco=carg_Banc, cargo_sistema=carg_Sis, usuario=us, servicio=serv, proveedor=prov, prov_correo=prov_email, prov_telefono=prov_phone)
                data['detail'] = "pago_solicitud"
                pago_solicitud = PagoSolicitud.objects.create(
                    pago_tarjeta=pago_tarjeta_user, solicitud=solicitud)
            except:
                data['error'] = "No se pudo guardar el pago/sin embargo, si se realizo"
                return Response(data)
            else:
                solicitud.descuento=descuento
                solicitud.save()
                data['success'] = True
                data['msg'] = "El pago se guardo exitosamente"
                serializer = PagoTarjetaSerializer(pago_tarjeta_user)
                data['pago_tarjeta'] = serializer.data
                titles = 'Servicio pagado: '+solicitud.servicio.nombre
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__username=solicitud.proveedor.user_datos.user.email)
                tokend = devices.values_list('registration_id', flat=True)

                dataNot={"ruta": "/historial", "descripcion": "El pago por el servicio de " +
                          solicitud.servicio.nombre + " fue existoso"}
                tokens=list(tokend)
                send_notificationF(tokens,titles,bodys,dataNot)

                return Response(data)


class PagosEfectivo(APIView):
    def post(self, request, format=None):
        data = {}
        data['success'] = False
        user = request.data.get('username')
        promotion = request.data.get('promocion')  # codigo de la promocion
        amount = request.data.get('valor')
        descuento = request.data.get('descuento')
        desc = request.data.get('descripcion')
        referencia = request.data.get('referencia')
        solicitud_ID = request.data.get('solicitud')  # id de la solicitud
        us = request.data.get('usuario')
        serv = request.data.get('servicio')
        prov = request.data.get('proveedor')
        prov_phone = request.data.get('prov_phone')
        prov_email = request.data.get('prov_email')
        us_phone = request.data.get('user_phone')

        try:
            usuario = User.objects.get(username=user)
            promocion = Promocion.objects.get(codigo=promotion)
            solicitud = Solicitud.objects.get(id=solicitud_ID)
        except:
            data['error'] = "No se encontraron los datos de la promocion"
            return Response(data)

        else:
            try:
                data['detail'] = "pago_efectivo"
                pago_efectivo_user = PagoEfectivo.objects.create(user=usuario, promocion=promocion, valor=amount, descripcion=desc, referencia=referencia, oferta=descuento, solicitud=solicitud,
                                                                 usuario=us, servicio=serv, proveedor=prov, prov_correo=prov_email, prov_telefono=prov_phone, user_telefono=us_phone)
                data['detail'] = "pago_solicitud"
                data['oferta'] = descuento
                pago_solicitud = PagoSolicitud.objects.create(
                    pago_efectivo=pago_efectivo_user, solicitud=solicitud)
            except:
                data['error'] = "No se pudo guardar el pago/sin embargo, si se realizo"
                data['oferta'] = descuento
                return Response(data)
            else:
                solicitud.descuento=descuento
                solicitud.save()
                data['success'] = True
                data['msg'] = "El pago se guardo exitosamente"
                serializer = PagoEfectivoSerializer(pago_efectivo_user)
                data['pago_efectivo'] = serializer.data

                titles = 'Servicio pagado: '+solicitud.servicio.nombre
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__id=solicitud.proveedor.user_datos.user.id)
                tokend = devices.values_list('registration_id', flat=True)

                dataNot={"ruta": "/historial", "descripcion": "El pago por el servicio de " +
                          solicitud.servicio.nombre + " fue existoso"}
                tokens=list(tokend)
                send_notificationF(tokens,titles,bodys,dataNot)

                return Response(data)


class PagosTarjetaUser(APIView):
    def get(self, request, format=None):
        pagost = PagoTarjeta.objects.all().filter()
        serializer = PagoTarjetaSerializer(pagost, many=True)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        pago = PagoTarjeta.objects.get(id=ident)
        pago.pago_proveedor = request.data.get('estado')
        pago.save()
        return Response(status=status.HTTP_200_OK)


class PagosEfectivoUser(APIView):
    def get(self, request, format=None):
        pagose = PagoEfectivo.objects.all().filter()
        serializer = PagoEfectivoSerializer(pagose, many=True)
        return Response(serializer.data)


class PagosEfectivoUserP(APIView, MyPaginationMixin):
    queryset = PagoEfectivo.objects.all().order_by('-id')
    serializer_class = PagoEfectivoSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class EfectivosFilter(APIView, MyPaginationMixin):
    queryset = PagoEfectivo.objects.all()
    serializer_class = PagoEfectivoSerializer
    pagination_class = MyCustomPagination

    def get(self, request):
        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(self.queryset.filter(
            fecha_creacion__date__range=[fechaIn, fechaFi]))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class ValorTotalEfectivo(APIView):
    def get(self, request, format=None):
        total = PagoEfectivo.objects.aggregate(Sum('valor'))
        return Response(total)


class ValorTotalTarjeta(APIView):
    def get(self, request, format=None):
        total = PagoTarjeta.objects.aggregate(Sum('valor'))
        return Response(total)


class ValorTotalPayTarjeta(APIView):
    def get(self, request, format=None):
        total = PagoTarjeta.objects.aggregate(Sum('cargo_paymentez'))
        return Response(total)


class ValorTotalBancTarjeta(APIView):
    def get(self, request, format=None):
        total = PagoTarjeta.objects.aggregate(Sum('cargo_banco'))
        return Response(total)


class ValorTotalSisTarjeta(APIView):
    def get(self, request, format=None):
        total = PagoTarjeta.objects.aggregate(Sum('cargo_sistema'))
        return Response(total)


class ValorTotal(APIView):

     def get(self, request, format=None):
        totalE = PagoEfectivo.objects.aggregate(total=Sum('valor'))['total'] or 0
        totalT = PagoTarjeta.objects.aggregate(total=Sum('valor'))['total'] or 0

        total = totalE + totalT

        return Response({'total': total})


class TarjetasFilter(APIView, MyPaginationMixin):
    queryset = PagoTarjeta.objects.all()
    serializer_class = PagoTarjetaSerializer
    pagination_class = MyCustomPagination

    def get(self, request):
        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(self.queryset.filter(
            fecha_creacion__date__range=[fechaIn, fechaFi]))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class PagosTarjetaUserP(APIView, MyPaginationMixin):
    queryset = PagoTarjeta.objects.all().order_by('-id')
    serializer_class = PagoTarjetaSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class PagosSolicitudesEfectivo(APIView):
    def get(self, request, pago_ID, format=None):
        pagos = PagoSolicitud.objects.all().filter(pago_efectivo=pago_ID)
        serializer = PagoSolicitudSerializer(pagos, many=True)
        return Response(serializer.data)


class PagosSolicitudesTarjeta(APIView):
    def get(self, request, pago_ID, format=None):
        pagos = PagoSolicitud.objects.all().filter(pago_tarjeta=pago_ID)
        serializer = PagoSolicitudSerializer(pagos, many=True)
        return Response(serializer.data)


class Suggestions(APIView):

    def get(self, request, format=None):
        sugerencia = Suggestion.objects.all().filter()
        serializer = SuggestionSerializer(sugerencia, many=True)
        return Response(serializer.data)

    '''def delete(self,request,id, format=None):
        categoria = Categoria.objects.get(id=id)
        servicios = Servicio.objects.filter(categoria=categoria)
        servicios.delete()
        categoria.delete()
        #Notificacion a los usuarios
        devices = FCMDevice.objects.filter(active=True)
        tokend = devices.values_list('registration_id', flat=True)
        devices.send_message(
            titles="categoria Eliminada: "+categoria.nombre,
            bodys="¡Sorry, no podrás acceder a la categoria!",
        )
        tokens=list(tokend)
        send_notificationF(tokens,titles,bodys,data)
        return Response(status=status.HTTP_204_NO_CONTENT)'''

    def post(self, request, format=None):
        data = {}

        descripcion = request.POST.get('descripcion')
        foto = request.FILES.get('foto')
        usuario = request.POST.get("usuario")
        correo = request.POST.get("correo")
        sugerencia = Suggestion.objects.create(
            descripcion=descripcion, foto=foto, usuario=usuario, correo=correo)
        serializer = SuggestionSerializer(sugerencia)
        data['sugerencia'] = serializer.data
        if sugerencia:
            return Response(data)
        else:
            data['error'] = "Error al crear!."
            return Response(data)


class Suggestions_Details(APIView):

    def get(self, request, pk, format=None):

        sugerencia = Suggestion.objects.get(id=pk)
        serializer = SuggestionSerializer(sugerencia)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        sugerencia = Suggestion.objects.get(id=pk)
        estado = request.data.get("estado")
        if estado:
            sugerencia.estado = estado
            sugerencia.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ReadSuggestions(APIView, MyPaginationMixin):
    queryset = Suggestion.objects.all().filter(estado=True)
    serializer_class = SuggestionSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class UnreadSuggestions(APIView, MyPaginationMixin):

    queryset = Suggestion.objects.all().filter(estado=False)
    serializer_class = SuggestionSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class Politics(APIView):

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


class Planes(APIView):

    def get(self, request, format=None):
        planes = Plan.objects.all().filter()
        serializer = PlanSerializer(planes, many=True)
        return Response(serializer.data)

    def post(self, request):

        serializer = PlanSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save()
            return Response(PlanSerializer(plan).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):

        plan = Plan.objects.get(id=request.data.get("id"))
        serializer = PlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):

        plan = Plan.objects.get(id=id)
        plan.delete()
        return Response(PlanSerializer(plan).data)


class Publicidades(APIView, MyPaginationMixin):

    queryset = Publicidad.objects.all()
    serializer_class = PublicidadSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):

        serializer = PublicidadSerializer(data=request.data)
        if serializer.is_valid():
            publicidad = serializer.save()
            return Response(PublicidadSerializer(publicidad).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):

        publicidad = Publicidad.objects.get(id=request.data.get("id"))
        serializer = PublicidadSerializer(
            publicidad, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):

        publicidad = Publicidad.objects.get(id=id)
        publicidad.delete()
        return Response(PublicidadSerializer(publicidad).data)


class FiltroPublicidadesNombres(APIView, MyPaginationMixin):

    queryset = Publicidad.objects.all()
    serializer_class = PublicidadSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):

        page = self.paginate_queryset(self.queryset.filter(Q(titulo__icontains=request.GET.get(
            'buscar')) | Q(descripcion__icontains=request.GET.get('buscar'))))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class AdminUser(APIView):

    def get(self, request, user):
        user = User.objects.get(email=user)
        user_datos = Datos.objects.get(user=user)
        admin = Administrador.objects.get(user_datos=user_datos)
        serializer = AdministradorSerializer(admin)
        return Response(serializer.data)


class AdminUserPass(APIView):

    def post(self, request, format=None):

        data = {}

        username = request.data.get("username")
        password = request.data.get("password")
        inf = {}
        inf['username'] = username
        inf['password'] = password

        form = AuthenticationForm(data=inf)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                do_login(request, user)
                usuario = Datos.objects.get(user=user)

                if (usuario.estado == True):
                    token, _ = Token.objects.get_or_create(user=user)
                    admin = Administrador.objects.get(user_datos=usuario)
                    # data['token']=token = Token.objects.get(user=user).key
                    serializer = AdministradorSerializer(admin)
                    data['token'] = token.key
                    data['active'] = True
                    data['admin'] = serializer.data

                    return Response(data)

                elif (usuario.estado == False):
                    data['active'] = False
                    return Response(data)
                else:
                    data['error'] = 'Usuario no permitido'
                    data['active'] = True
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data['error'] = 'Error de formulario'
            data['active'] = True
            form = AuthenticationForm()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class Ciudades(APIView):

    # queryset = Ciudad.objects.all()
    # serializer_class = CiudadSerializer
    # pagination_class = MyCustomPagination

    def get(self, request, formt=None):

        # page = self.paginate_queryset(self.queryset)
        # if page is not None:
        #     serializer = self.serializer_class(page, many=True)
        # return self.get_paginated_response(serializer.data)
        ciudades = Ciudad.objects.all().filter()
        serializer = CiudadSerializer(ciudades, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CiudadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlanProveedorView(APIView):

    def get(self, request, format=None):
        planProveedor = PlanProveedor.objects.all().filter()
        serializer = PlanProveedorSerializer(planProveedor, many=True)
        return Response(serializer.data)

    def post(self, request):

        serializer = PlanProveedorSerializer(data=request.data)
        if serializer.is_valid():
            planProveedor = serializer.save()
            return Response(PlanProveedorSerializer(planProveedor).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):

        planProveedor = PlanProveedor.objects.get(id=request.data.get("id"))
        serializer = PlanProveedorSerializer(
            planProveedor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):

        planProveedor = PlanProveedor.objects.get(id=id)
        planProveedor.delete()
        return Response(PlanProveedorSerializer(planProveedor).data)


class PlanesEstado(APIView):

    def get(self, request, format=None):
        planes = Plan.objects.all().filter(estado=True)
        serializer = PlanSerializer(planes, many=True)
        return Response(serializer.data)


# class PlanillasView(ModelViewSet):

#     queryset = Planilla_Servicios.objects.all()
#     serializer_class = PlanillasServiciosSerializer
#     parser_classes = (MultiPartParser, FormParser)


class PendientesDocumentsView(APIView):

    def get(self, request, format=None):
        queryset = PendienteDocuments.objects.all()
        serializer = PendientesDocumentsSerializer(queryset, many=True)
        parser_classes = (MultiPartParser, FormParser)
        return Response(serializer.data)

    def delete(self, request, format=None):

        pendiente = PendienteDocuments.objects.get(id=request.GET.get("id"))
        pendiente.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresDate_Search_Name(APIView, MyPaginationMixin):

    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    pagination_class = MyCustomPagination

    def get(self, request, format=None):

        fechaIn = datetime.datetime.strptime(
            request.GET.get("fechaInicio"), "%Y-%m-%d")
        fechaFi = datetime.datetime.strptime(
            request.GET.get("fechaFin"), "%Y-%m-%d")
        user = request.GET.get("user")
        page = self.paginate_queryset(self.queryset.filter(Q(user_datos__nombres__icontains=user, planproveedor__fecha_expiracion__date__range=[
                                      fechaIn, fechaFi]) | Q(user_datos__apellidos__icontains=user, planproveedor__fecha_expiracion__date__range=[fechaIn, fechaFi])))
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)


class ProveedorRegistro(APIView):

    def post(self, request, format=None):
        passw = User.objects.make_random_password()
        grupoProveedor = Group.objects.get(name='Proveedor')
        data = {}
        try:
            usuario = User.objects.create_user(email=request.data.get(
                'email'), username=request.data.get('email'), password=passw)
            grupoProveedor.user_set.add(usuario)
        except:
            data['error'] = "Correo ya empleado"
            return Response(data)

        nombreUsuario = request.data.get('nombres')
        apellidosUsuario = request.data.get('apellidos')
        ciudadUsuario = request.data.get('ciudad')
        cedulaUsuario = request.data.get('cedula')
        telefonoUsuario = request.data.get('telefono')
        generoUsuario = request.data.get('genero')
        foto_user = request.FILES.get('foto')
        data["nombre"] = nombreUsuario
        data["apellido"] = apellidosUsuario
        data["telefono"] = telefonoUsuario
        data["ciudad"] = ciudadUsuario
        data["cedula"] = cedulaUsuario
        data["genero"] = generoUsuario
        data["foto"] = foto_user
        data["email"] = request.data.get('email')
        data["password"] = passw

        try:
            datoCreado = Datos.objects.create(user=usuario, tipo=models.Group.objects.get(name='Proveedor'), nombres=nombreUsuario,
                                              apellidos=apellidosUsuario, telefono=telefonoUsuario, genero=generoUsuario, foto=foto_user, ciudad=ciudadUsuario, cedula=cedulaUsuario)

        except:
            data['error'] = "Error al almacenar Datos"
            return Response(data)

        direccionUsuario = request.data.get('direccion')
        licenciaUsuario = request.data.get('licencia')
        copiaLicenciaUsuario = request.data.get('copiaLicencia')
        profesionUsuario = request.data.get('profesion')
        anioExperUsuario = request.data.get('anio_experiencia')
        tipoCuenta = request.data.get('tipo_cuenta')
        descripcionUsuario = request.data.get('descripcion')
        bancoUsuario = request.data.get('banco')
        numeroCuenta = request.data.get('numero_cuenta')
        documentos = request.FILES.getlist('documentos')

        pendiente = Proveedor_Pendiente.objects.get(id=request.data.get('id'))

        uploaded_cedula = pendiente.copiaCedula
        uploaded_licencia = pendiente.copiaLicencia
        uploaded_documents = pendiente.documentsPendientes
        try:
            proveedorCreado = Proveedor.objects.create(user_datos=datoCreado, descripcion=descripcionUsuario, profesion=profesionUsuario, direccion=direccionUsuario,
                                                       licencia=licenciaUsuario, ano_profesion=anioExperUsuario, banco=bancoUsuario, numero_cuenta=numeroCuenta, tipo_cuenta=tipoCuenta)
            if not uploaded_cedula == None:
                proveedorCreado.copiaCedula = File(
                    uploaded_cedula, os.path.basename(uploaded_cedula.name))
            if not uploaded_licencia == None:
                proveedorCreado.copiaLicencia = File(
                    uploaded_licencia, os.path.basename(uploaded_licencia.name))
            proveedorCreado.save()

            # banco_user = Banco.objects.get_or_create(nombre= bancoUsuario)
            # tipo_cuenta_user= Tipo_Cuenta.objects.get(nombre = tipoCuenta)
            # cuenta = Cuenta.objects.create(banco= banco_user, tipo_cuenta= tipo_cuenta_user, proveedor= proveedorCreado, numero_cuenta= numeroCuenta)

        except:
            data['error'] = "Error al crear Proveedor"
            return Response(data)

        for documento in uploaded_documents.all():
            documento_creado = Document.objects.create(descripcion=request.data.get(
                'descripcionDoc'), documento=File(documento.document, os.path.basename(documento.document.name)))
            proveedorCreado.document.add(documento_creado)

        proveedorCreado.save()
        profesionObj = Profesion.objects.get(nombre=profesionUsuario)
        profesion_creada = Profesion_Proveedor.objects.create(
            proveedor=proveedorCreado, profesion=profesionObj, ano_experiencia=anioExperUsuario)

        return Response(data)


class ProveedorEdicion(APIView):

    def put(self, request, format=None):
        data = {}
        # try:
        proveedor = Proveedor.objects.get(id=request.data.get('id'))
        datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
        # user = User.objects.get(email= request.data.get('email'))
        user = User.objects.get(id=datos_prov.user.id)

        if datos_prov:
            if User.objects.filter(email=request.data.get('emailNuevo')).exists():
                userExistente = User.objects.get(
                    email=request.data.get('emailNuevo'))
                if (user.id != userExistente.id):
                    data['errorEmail'] = 'Email ya registrado'
                    return Response(data)
                else:
                    user.email = userExistente.email
            user.email = request.data.get('emailNuevo')
            user.username = request.data.get('emailNuevo')
            user.save()

        datos_prov.nombres = request.data.get("nombres")
        datos_prov.apellidos = request.data.get("apellidos")
        datos_prov.ciudad = request.data.get("ciudad")
        datos_prov.cedula = request.data.get("cedula")
        datos_prov.genero = request.data.get("genero")
        datos_prov.telefono = request.data.get("telefono")
        datos_prov.save()

        proveedor.direccion = request.data.get("direccion")
        proveedor.licencia = request.data.get("licencia")
        proveedor.descripcion = request.data.get("descripcion")
        proveedor.banco = request.data.get("banco")
        proveedor.numero_cuenta = request.data.get("numero_cuenta")
        proveedor.tipo_cuenta = request.data.get("tipo_cuenta")

        copiaCedula = request.data.get('copiaCedula')
        copiaLicencia = request.data.get('copiaLicencia')
        documents = request.FILES.getlist('filesDocuments')

        if not copiaCedula == None:
            proveedor.copiaCedula.delete()
            proveedor.copiaCedula = copiaCedula

        if not copiaLicencia == None:
            proveedor.copiaLicencia.delete()
            proveedor.copiaLicencia = copiaLicencia

        for doc in documents:
            documento_creado = Document.objects.create(
                descripcion="Documento", documento=doc)
            proveedor.document.add(documento_creado)

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
        data["sucess"] = "Exito"
        return Response(data)
        # except:
        #     data["error"] = "Error"
        #     return Response(data)


class SendNotificacion(APIView):

    def get(self, request, format=None):
        notificaciones = NotificacionMasiva.objects.all()
        serializer = NotificacionMasivaSerializer(notificaciones, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        nombre = request.data.get('nombre')
        titles = request.data.get('titulo')
        descripcion = request.data.get('descripcion')
        tipo_proveedores = request.data.get('tipo_proveedores')
        frecuencia = request.data.get('frecuencia')
        imagen = request.FILES.get('imagen')
        ruta = request.data.get('ruta')
        ini = request.data.get('fecha_iniciacion')
        exp = request.data.get('fecha_expiracion')
        hora=request.data.get('hora')

        notificacion = NotificacionMasiva.objects.create(
            nombre = nombre,
            titulo=titles,
            descripcion=descripcion,
            tipo_proveedores=tipo_proveedores,
            frecuencia=frecuencia,
            ruta=ruta,
            imagen=imagen,
            fecha_iniciacion=ini,
            fecha_expiracion=exp,
            hora=hora,
        )
        notificacion.save()
        dataNot = {}
        if imagen is not None:
            dataNot["imagen"] = notificacion.imagen.url
        dataNot["ruta"] = ruta
        dataNot["descripcion"] = descripcion
        try:
            devices = FCMDevice.objects.filter(active=True)
            tokend = devices.values_list('registration_id', flat=True)
            tokens=list(tokend)

            send_notificationF(tokens,titles,descripcion,dataNot)

            data['success'] = True
            data['message'] = "La notificación ha sido creada correctamente."
            serializer = NotificacionMasivaSerializer(notificacion)
            data['notificacion_masiva'] = serializer.data
            return Response(data)
        except Exception as e:
            notificacion.delete()
            data['success'] = False
            data['message'] = f"Hubo un error al enviar la notificación: {str(e)}"
            return Response(data)

    def put(self, request, id, format=None):
        try:
            id = int(id)
            notificacion = NotificacionMasiva.objects.get(id=id)
            serializer = NotificacionMasivaSerializer(notificacion, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            print("Errores de validación:", serializer.errors)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except NotificacionMasiva.DoesNotExist:
            return Response({"error": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request, id):
        data = {}
        try:
            notificacion_masiva = NotificacionMasiva.objects.get(id=id)
            notificacion_masiva.delete()

            devices = FCMDevice.objects.filter(active=True)
            tokend = devices.values_list('registration_id', flat=True)
            tokens=list(tokend)
            titles = "Notificacion eliminada:" + notificacion_masiva.titulo
            descripcion = notificacion_masiva.descripcion
            dataNot = {}
            dataNot["descripcion"] = descripcion

            send_notificationF(tokens,titles,descripcion,dataNot)

            data['success'] = True
            data['message'] = "Se ha eliminado la notificación exitosamente."
            return Response(data)
        except:
            data['success'] = False
            data['message'] = "La notificación no fue encontrada en la base de datos."
            return Response(data)

class SendNotificacion_Details(APIView):

    def get(self, request, pk, format=None):

        noti= NotificacionMasiva.objects.get(id=pk)
        serializer = NotificacionMasivaSerializer(noti)
        return Response(serializer.data)

    def put(self, request):
        ident = request.GET.get('id')
        noti = NotificacionMasiva.objects.get(id=ident)
        noti.estado = request.data.get('estado')
        noti.save()
        return Response(status=status.HTTP_200_OK)

    def post(self, request):
        pk = request.GET.get('id')
        prove_select = NotificacionMasiva.objects.get(id=pk)
        serializer = NotificacionMasivaSerializer(prove_select)
        # Obtener el tipo de proveedor desde la notificación masiva
        tipo_proveedor = prove_select.tipo_proveedores  # Suponiendo que tipo_proveedores es un campo en NotificacionMasiva
        # Preparar los datos de la notificación
        descripcion = prove_select.descripcion
        dataNot = {
            "descripcion": descripcion
        }
        # Filtrar proveedores cuya profesión coincida con el tipo de proveedor
        proveedores = Proveedor.objects.all()
        for proveedor in proveedores:
            if ',' in proveedor.profesion:
                profesiones = proveedor.profesion.split(",")
                if tipo_proveedor in profesiones:
                    print(f'Proveedor {proveedor} tiene la profesión {tipo_proveedor}')
                    p_user_id = proveedor.user_datos.id
                    print("id", p_user_id)
                    datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
                    user = User.objects.get(id=datos_prov.user.id)
                    u_id = user.id
                    print("idp", u_id)

                    devices = FCMDevice.objects.filter(active=True, user_id=u_id)

                    # Obtener los tokens de esos dispositivos
                    tokens = devices.values_list('registration_id', flat=True)

                    if tokens:
                        # Enviar la notificación solo si existen tokens
                        send_notificationF(list(tokens), prove_select.titulo, descripcion, dataNot)
                    else:
                        # Si no hay dispositivos activos para este proveedor, puedes registrar un error o continuar
                        print(f"No se encontraron dispositivos activos para el proveedor con user_id {u_id}")
            else:
                # Si la profesión no tiene comas, es un solo valor
                if proveedor.profesion == tipo_proveedor:
                    print(f'Proveedor {proveedor} tiene la profesión {tipo_proveedor}')
                    p_user_id = proveedor.user_datos.id
                    print("id", p_user_id)
                    datos_prov = Datos.objects.get(id=proveedor.user_datos.id)
                    user = User.objects.get(id=datos_prov.user.id)
                    u_id = user.id
                    print("idp", u_id)

                    devices = FCMDevice.objects.filter(active=True, user_id=u_id)

                    # Obtener los tokens de esos dispositivos
                    tokens = devices.values_list('registration_id', flat=True)

                    if tokens:
                        # Enviar la notificación solo si existen tokens
                        send_notificationF(list(tokens), prove_select.titulo, descripcion, dataNot)
                    else:
                        # Si no hay dispositivos activos para este proveedor, puedes registrar un error o continuar
                        print(f"No se encontraron dispositivos activos para el proveedor con user_id {u_id}")

        return Response({"message": "Notificación enviada correctamente a los proveedores seleccionados."}, status=status.HTTP_200_OK)



class RolesPermisos(APIView):

    def get(self, request, id):

        grupo = Group.objects.get(name=id)
        serializer = GroupSerializer(grupo)
        return Response(serializer.data)

    def post(self, request):

        grupoNuevo = Group.objects.create(name=request.data.get("nombre"))
        for permiso in request.POST.getlist('permisos'):
            objPermiso = Permission.objects.get(name=permiso)
            grupoNuevo.permissions.add(objPermiso)
        serializer = GroupSerializer(grupoNuevo)
        return Response(serializer.data)

    def put(self, request):

        grupo = Group.objects.get(id=request.data.get("id"))
        permisos = []

        for permiso in grupo.permissions.all():
            permisos.append(permiso.name)

        permisosEnviados = []
        for permiso in request.POST.getlist('permisos'):
            permisosEnviados.append(permiso)
            if permiso not in permisos:
                objPermiso = Permission.objects.get(name=permiso)
                grupo.permissions.add(objPermiso)

        for permiso in permisos:
            if permiso in permisosEnviados:
                objPermiso = Permission.objects.get(name=permiso)
                grupo.permissions.remove(objPermiso)

        serializer = GroupSerializer(grupo)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):

        grupo = Group.objects.get(id=id)
        grupo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Permisos(APIView):

    def get(self, request):

        permisos = Permission.objects.all()
        serializer = PermissionSerializer(permisos, many=True)
        return Response(serializer.data)


class Cargos(APIView):

    def get(self, request, formt=None):
        cargos = Cargo.objects.all().filter()
        serializer = CargoSerializer(cargos, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = {}
        name = request.POST.get('nombre')
        title = request.POST.get('titulo')
        porcen = request.POST.get('porcentaje')
        cargo_creado = Cargo.objects.create(
            nombre=name, porcentaje=porcen, titulo=title)
        serializer = CargoSerializer(cargo_creado)
        data['cargo'] = serializer.data
        if cargo_creado:
            return Response(data)
        else:
            data['error'] = "Error al crear un cargo!."
            return Response(data)

    def delete(self, request, id, format=None):
        cargo = Cargo.objects.get(id=id)
        cargo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, id, format=None):
        cargo = Cargo.objects.get(id=id)
        serializer = CargoSerializer(cargo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Cargo_Details(APIView):

    def get(self, request, pk, format=None):

        cargo = Cargo.objects.get(id=pk)
        serializer = CargoSerializer(cargo)
        return Response(serializer.data)

    # def put(self, request):
        # ident = request.GET.get('id')
        # insig = Insignia.objects.get(id = ident)
        # insig.estado = request.data.get('estado')
        # insig.save()
        # return Response(status=status.HTTP_200_OK)

class Puntos(APIView):
    def get(self, request, email):
        data = {}
        try:
            usuario = Datos.objects.get(user__email=email)
            data['valid'] = "OK"
            data['puntos'] = usuario.puntos
            return Response(data)
        except:
            data['valid'] = "error"
            data['puntos'] = 0
            return Response(data)

class Politica(APIView):
    def get(self, request):
        return HttpResponse('TÉRMINOS Y CONDICIONES PARA USO DE LA APLICACIÓN “VIVEFÁCIL” Reglamento de Uso de la Aplicación Móvil El presente documento establece las condiciones mediante las cuales se regirá el uso de la aplicación móvil “VIVEFÁCIL”, la cual es operada por DIANA ALEJANDRA PEÑA HERRERA domiciliada en Ecuador, Provincia del Guayas Cantón Daule, con RUC No. 0932562812001 La aplicación funcionará como un nuevo canal para la realización de diversas actividades descritas más adelante con el objeto de facilitar el acceso a los usuarios. El usuario se compromete a leer los términos y condiciones aquí establecidos, previamente a la descarga de la aplicación, por tanto, en caso de realizar la instalación se entiende que cuenta con el conocimiento integral de este documento y la consecuente aceptación de la totalidad de sus estipulaciones. El usuario reconoce que el ingreso de su información personal, y los datos que contiene la aplicación a su disposición respecto a los productos y/o servicios activos registrados dentro de la aplicación, la realizan de manera voluntaria, quienes optan por acceder a esta aplicación en Ecuador o desde fuera del territorio nacional, lo hacen por iniciativa propia y son responsables del cumplimiento de las leyes locales, en la medida en que dichas leyes sean aplicables en su correspondiente país. En caso de que se acceda por parte de menores de edad, deben contar con la supervisión de un adulto en todo momento desde la descarga y durante el uso de la aplicación, en el evento en que no se cumpla esta condición, le agradecemos no hacer uso de la aplicación. Alcance y Uso El usuario de la aplicación entiende y acepta que la información contenida en la misma es operada por DIANA ALEJANDRA PEÑA HERRERA, la misma que será la referente a su vínculo comercial o contractual con cada usuario, por tanto, las funcionalidades ofrecidas por la aplicación serán entregadas con el objetivo vinculado a las necesidades del beneficiario. En la aplicación se pondrá a disposición del CLIENTE información y/o permitirá la realización de las transacciones determinadas o habilitadas por VIVEFÁCIL para cada producto y/o servicio en particular. VIVEFÁCIL podrá adicionar, modificar o eliminar las funcionalidades en cualquier momento, lo cual acepta el usuario mediante la instalación de la aplicación. En todo caso, al momento de realizar dichas modificaciones se notificarán al usuario a través de la misma aplicación móvil una vez inicie sesión. Los tiempos de respuesta, trámites y demás solicitudes efectuadas por el usuario mediante la aplicación serán procesadas de conformidad con las especificaciones de cada producto y/o servicio activo con VIVEFÁCIL. El usuario acepta y autoriza que los registros electrónicos de las actividades mencionadas, que realice en la aplicación constituyen plena prueba de los mismos. Requisitos para uso El usuario deberá contar con un dispositivo móvil inteligente (Smartphone) o Tableta con sistema operativo Android o IOS, cualquiera de estos con acceso a internet, ambos seguros y confiables. VIVEFÁCIL no será responsable por la seguridad de los equipos Smartphone propiedad de los usuarios utilizados para el acceso al canal, ni por la disponibilidad del servicio en los dispositivos en los cuales se descargue la aplicación. En la forma permitida por la ley, los materiales de la aplicación se suministran sin garantía de ningún género, expresa o implícita, incluyendo sin limitación las garantías de calidad satisfactoria, comerciabilidad, adecuación para un fin particular o no infracción, por tanto, VIVEFÁCIL no garantiza el funcionamiento adecuado en los distintos sistemas operativos o dispositivos en los cuales se haga uso de la aplicación. Para acceder al portal, EL CLIENTE contará con Usuario y Clave, que lo identifica en su relación con VIVEFÁCIL. Obligaciones de los usuarios El usuario se obliga a usar la aplicación y los contenidos encontrados en ella de una manera diligente, correcta, lícita y en especial, se compromete a NO realizar las conductas descritas a continuación: • Utilizar los contenidos de forma, con fines o efectos contrarios a la ley, a la moral y a las buenas costumbres generalmente aceptadas o al orden público; • Reproducir, copiar, representar, utilizar, distribuir, transformar o modificar los contenidos de la aplicación, por cualquier procedimiento o sobre cualquier soporte, total o parcial, o permitir el acceso del público a través de cualquier modalidad de comunicación pública; • Utilizar los contenidos de cualquier manera que entrañen un riesgo de daño o inutilización de la aplicación o de los contenidos o de terceros; • Suprimir, eludir o manipular el derecho de autor y demás datos identificativos de los derechos de autor incorporados a los contenidos, así como los dispositivos técnicos de protección, o cualesquiera mecanismos de información que pudieren tener los contenidos; • Emplear los contenidos y, en particular, la información de cualquier clase obtenida a través de la aplicación para distribuir, transmitir, remitir, modificar, rehusar o reportar la publicidad o los contenidos de esta con fines de venta directa o con cualquier otra clase de finalidad comercial, mensajes no solicitados dirigidos a una pluralidad de personas con independencia de su finalidad, así como comercializar o divulgar de cualquier modo dicha información; • No permitir que terceros ajenos a usted usen la aplicación móvil con su clave; • Utilizar la aplicación y los contenidos con fines lícitos y/o ilícitos, contrarios a lo establecido en estos Términos y Condiciones, o al uso mismo de la aplicación, que sean lesivos de los derechos e intereses de terceros, o que de cualquier forma puedan dañar, inutilizar, sobrecargar o deteriorar la aplicación y los contenidos o impedir la normal utilización o disfrute de esta y de los contenidos por parte de los usuarios. Condiciones de Pago y Facturación Las tarifas aplicables al Servicio serán recaudadas por VIVEFÁCIL de forma automática, a través de los datos de la tarjeta de crédito / débito facilitado por el usuario, o efectivo u otros métodos acordados con el proveedor. Tras la petición del Servicio, VIVEFÁCIL se reserva el derecho a solicitar la pre-autorización del cobro a la entidad de crédito vinculada a la tarjeta de crédito/débito que el usuario hubiera introducido en la Aplicación. Tras la petición del Servicio, VIVEFÁCIL realizará el cobro efectivo del total del Servicio que vaya a requerirse. Las tarifas cobradas podrán, previo análisis, ser reembolsables en los siguientes casos: a) VIVEFÁCIL hará por medio de acreditación bancaria al no darse el servicio en un plazo de 72 horas hábiles después de haber recibido y verificado la queja y que sea válido el reclamo; b) En caso de requerir el servicio y pago con tarjeta de crédito y se desiste al día siguiente por 4 horas antes del servicio se cobrará una penalidad del 25%, si es pasado de las 24 horas antes del servicio se reintegra el valor total del mismo descontada la tarifa bancaria; c) En caso de que el usuario no reciba el servicio por no encontrarse en el lugar indicado por casos de eventualidad o fuerza mayor y se pasó de la fecha y hora del servicio se realizará la devolución con una penalidad del 50%; d) En caso de cobros duplicados se devolverá en plazo máximo de 72 horas hábiles toda vez que se verifique la duplicidad. Las tarifas y los gastos de cancelación y compensación, así como sus actualizaciones, están disponibles en todo momento en la y están sujetas a modificaciones. Se recomienda al Usuario y al Proveedor de los servicios que acceda periódicamente a la Aplicación para conocer las tarifas aplicables en cada momento. Los valores recaudados serán acreditados a los Proveedores de los Servicios, descontando el porcentaje establecido por el uso de los botones de pago y de la plataforma en caso de que aplique. El Proveedor de los servicios entregará a los clientes, una vez cumplido el servicio, la nota de venta o factura física o electrónica correspondiente, dependiendo de si el Proveedor tiene RISE o RUC. Los recibos de las transacciones realizadas estarán a disposición de los usuarios en el respectivo correo electrónico, sin perjuicio de que puedan consultarlas a través de la Aplicación. Los cargos realizados en tarjetas de crédito o débito se realizarán en todos los casos en dólares americanos (USD) o en la moneda de curso legal dentro de la República del Ecuador. VIVEFÁCIL no es responsable frente al usuario por cargos adicionales provenientes de bancos, emisores de tarjetas de crédito/débito, impuestos o en general cualquier cargo que no esté directamente realizado por VIVEFÁCIL y que se relacione con el uso del servicio. VIVEFÁCIL en ningún momento será responsable por cargos realizados en una tarjeta de crédito o débito que no cuenten con la autorización expresa del titular de la tarjeta. Para efectos del uso de la presente aplicación, VIVEFÁCIL presume que todos los cargos son realizados únicamente por los titulares y/o tarjetahabientes autorizados. El usuario declara conocer que los pagos realizados por objeto del servicio se realizan en el Ecuador pero podrían realizarse en el extranjero, en tal virtud los pagos realizados desde el Ecuador, con tarjetas de crédito/débito emitidas por bancos locales estarán sujetas al pago de cualquier valor adicional que la legislación vigente establezca. En ningún momento VIVEFÁCIL será responsable de asumir estos costos o será responsable por los tributos que correspondan a cada usuario. Licencia para copiar para uso personal Usted podrá leer, visualizar, imprimir y descargar el material de sus productos y/o servicios. Ninguna parte de la aplicación podrá ser reproducida o transmitida o almacenada en otro sitio web o en otra forma de sistema de recuperación electrónico. Ya sea que se reconozca específicamente o no, las marcas comerciales, las marcas de servicio y los logos visualizados en esta aplicación pertenecen a DIANA ALEJANDRA PEÑA HERRERA, sus socios promocionales u otros terceros. VIVEFÁCIL no interfiere, no toma decisiones, ni garantiza las relaciones que los usuarios lleguen a sostener o las vinculaciones con terceros que pauten y/o promocionen sus productos y servicios. Estas marcas de terceros se utilizan solamente para identificar los productos y servicios de sus respectivos propietarios y el patrocinio o el aval por parte de VIVEFÁCIL no se deben inferir con el uso de estas marcas comerciales. Integración con otras aplicaciones Los links de Facebook®, Instagram®, Twitter® en esta aplicación pueden mostrar contenido que no están bajo el control de VIVEFÁCIL. Aunque esta aplicación de VIVEFÁCIL trata de suministrar links solamente a sitios y aplicaciones de terceros que cumplan con las leyes y regulaciones aplicables y las normas de VIVEFÁCIL, el usuario debe entender que VIVEFÁCIL no tiene control sobre la naturaleza y el contenido de esos sitios y no está recomendando estos sitios, la información que contienen ni los productos o servicios de terceros. VIVEFÁCIL no acepta responsabilidad por el contenido del sitio de un tercero con el cual existe un link de hipertexto y no ofrece garantía (explícita o implícita) en cuanto al contenido de la información en esos sitios, ya que no recomienda estos sitios. Usted debe verificar las secciones de términos y condiciones, política legal y de privacidad de algunos otros sitios de VIVEFÁCIL o de un tercero con los cuales se enlaza. VIVEFÁCIL no asume ninguna responsabilidad por pérdida directa, indirecta o consecuencial por el uso de un sitio de un tercero. Uso de información y privacidad Con la descarga de la APP usted acepta y autoriza que DIANA ALEJANDRA PEÑA HERRERA, utilice sus datos en calidad de responsable del tratamiento para fines derivados de la ejecución de la APP. DIANA ALEJANDRA PEÑA HERRERA informa que podrá ejercer sus derechos a conocer, actualizar, rectificar y suprimir su información personal; así como el derecho a revocar el consentimiento otorgado para el tratamiento de datos personales previstos en la Ley Orgánica De Protección De Datos Personales, siendo voluntario responder preguntas sobre información sensible o de menores de edad. DIANA ALEJANDRA PEÑA HERRERA podrá dar a conocer, transferir y/o trasmitir sus datos personales dentro y fuera del país a cualquier empresa vinculada con DIANA ALEJANDRA PEÑA HERRERA, así como a terceros a consecuencia de un contrato, ley o vínculo lícito que así lo requiera, para todo lo anterior otorgo mi autorización expresa e inequívoca. De conformidad a lo anterior autoriza el tratamiento de su información en los términos señalados, y transfiere a VIVEFÁCIL de manera total, y sin limitación mis derechos de imagen y patrimoniales de autor, de manera voluntaria, previa, explícita, informada e inequívoca. Responsabilidad de VIVEFÁCIL VIVEFÁCIL procurará garantizar disponibilidad, continuidad o buen funcionamiento de la aplicación. VIVEFÁCIL podrá bloquear, interrumpir o restringir el acceso a esta cuando lo considere necesario para el mejoramiento de la aplicación o por dada de baja de la misma. Se recomienda al usuario tomar medidas adecuadas y actuar diligentemente al momento de acceder a la aplicación, como por ejemplo, contar con programas de protección, antivirus, para manejo de malware, spyware y herramientas similares. VIVEFÁCIL no será responsable por: a) Fuerza mayor o caso fortuito; b) Por la pérdida, extravío o hurto de su dispositivo móvil que implique el acceso de terceros a la aplicación móvil; c) Por errores en la digitación o accesos por parte del cliente; d) Por los perjuicios, lucro cesante, daño emergente, morales, y en general sumas a cargo de VIVEFÁCIL, por los retrasos, no procesamiento de información o suspensión del servicio del operador móvil o daños en los dispositivos móviles. e) no será vinculada a ningún proceso legal tanto civil como penal ya que la obligación recae en quien ofrece el servicio o proveedor ya que la aplicación es solo un medio de contacto con el proveedor. Denegación y Retirada del Acceso a la Aplicación En el evento en que un usuario incumpla estos Términos y Condiciones, o cualesquiera otras disposiciones que resulten de aplicación, VIVEFÁCIL podrá suspender su acceso a la aplicación. Términos y Condiciones El usuario acepta expresamente los Términos y Condiciones, siendo condición esencial para la utilización de la aplicación. En el evento en que se encuentre en desacuerdo con estos Términos y Condiciones, solicitamos abandonar la aplicación inmediatamente. VIVEFÁCIL podrá modificar los presentes términos y condiciones, avisando a los usuarios de la aplicación mediante la difusión de las modificaciones por algún medio electrónico, redes sociales, SMS y/o correo electrónico, lo cual se entenderá aceptado por el usuario si éste continua con el uso de la aplicación. Jurisdicción Estos términos y condiciones y todo lo que tenga que ver con esta aplicación, se rigen por las leyes ecuatorianas. Uso de información no personal VIVEFÁCIL también recolecta información no personal en forma agregada para seguimiento de datos como el número total de descargas de la aplicación. Utilizamos esta información, que permanece en forma agregada, para entender el comportamiento de la aplicación. Uso de Direcciones IP Una dirección de Protocolo de Internet (IP) es un conjunto de números que se asigna automáticamente a su o dispositivo móvil cuando usted accede a su proveedor de servicios de internet, o a través de la red de área local (LAN) de su organización o la red de área amplia (WAN). Los servidores web automáticamente identifican su dispositivo móvil por la dirección IP asignada a él durante su sesión en línea. VIVEFÁCIL podrá recolectar direcciones IP para propósitos de administración de sistemas y para auditar el uso de nuestro sitio, todo lo anterior de acuerdo con la autorización de protección de datos que se suscribe para tal efecto. Normalmente no vinculamos la dirección IP de un usuario con la información personal de ese usuario, lo que significa que cada sesión de usuario se registra, pero el usuario sigue siendo anónimo para nosotros. Sin embargo, podemos usar las direcciones IP para identificar a los usuarios de nuestro sitio cuando sea necesario con el objeto de exigir el cumplimiento de los términos de uso del sitio, o para proteger nuestro servicio, sitio u otros usuarios. Seguridad VIVEFÁCIL está comprometido en la protección de la seguridad de su información personal. VIVEFÁCIL tiene implementados mecanismos de seguridad que aseguran la protección de la información personal, así como los accesos únicamente al personal y sistemas autorizados, también contra la pérdida, uso indebido y alteración de sus datos de usuario bajo nuestro control. Excepto como se indica a continuación, sólo personal autorizado tiene acceso a la información que nos proporciona. Además, hemos impuesto reglas estrictas a los colaboradores de VIVEFÁCIL con acceso a las bases de datos que almacenan información del usuario o a los servidores que hospedan nuestros servicios')

class ConfirmarDescuento(APIView):
    def get(self, request, mail):
        try:
            usuario = Datos.objects.get(user__email=mail)
            if usuario.descuento == 0:
                usuario.descuento = 1
                usuario.save()
                return Response("descuento")
            elif usuario.descuento == 1:
                return Response("reclamado")
            else:
                return Response("usado")
        except:
            return Response("no_existe")

class RevisarDescuentoUnico(APIView):
    def get(self, request, mail):
        try:
            usuario = Datos.objects.get(user__email=mail)
            if usuario.descuento == 1:
                return Response("descuento")
            else:
                return Response("no")
        except:
            return Response("error")

class UsarDescuentoUnico(APIView):
    def get(self, request, mail):
        try:
            usuario = Datos.objects.get(user__email=mail)
            if usuario.descuento == 1:
                usuario.descuento = 2
                usuario.save()
                return Response("usado")
            else:
                return Response("error")
        except:
            return Response("error")


class AdminPage(APIView):
    def get (self, request):
        return redirect(to="/static/index.html")

class ActualizarCaducidad (APIView):
    print("Cosa Ver Aca0")
    def put(self, request, pk):
        try:
            consola=request.data.get('id')
            proveedor = Proveedor.objects.get(id=request.data.get('id'))
            numero=request.data.get('input')
            novafecha=datetime.datetime.strptime(numero, '%Y-%m-%d').date()
            proveedor.fecha_caducidad= novafecha
            proveedor.estado = True
            proveedor.save()
            datos=proveedor.user_datos
            datos.estado=True
            datos.save()
            formatEmail = FormatEmail()
            thread = threading.Thread(target=formatEmail.send_email([proveedor.user_datos.user.username], "Cambio de fecha de contrato", 'emails/enviarAlerta.html', {"username":proveedor.user_datos.user.username, "contenido": "Tu fecha de contrato a cambiado, tu contrato expira el " + numero}))

            for e in Proveedor.objects.all().order_by('-id').filter(fecha_caducidad__lt=date.today()):
                if e.estado != False:
                    thread = threading.Thread(target=formatEmail.send_email([e.user_datos.user.username], "Cuenta caducada", 'emails/enviarAlerta.html', {"username":e.user_datos.user.username, "contenido": "Tu cuenta ha caducado, si deseas extender tu contrato contactanos por nuestros canales oficiales."}))
                e.estado = False
                e.save()
                datos=e.user_datos
                datos.estado=False
                datos.save()
            return Response(proveedor.fecha_caducidad)
        except Exception as e:
            return Response("error: " + str(e))

class RevisarCaducidad (APIView):
    print("Cosa Ver Aca0")
    def put(self, request, pk):
        try:
            formatEmail = FormatEmail()
            for e in Proveedor.objects.all().order_by('-id').filter(fecha_caducidad__lt=date.today()):
                if e.estado != False:
                    thread = threading.Thread(target=formatEmail.send_email([e.user_datos.user.username], "Cuenta caducada", 'emails/enviarAlerta.html', {"username":e.user_datos.user.username, "contenido": "Tu cuenta ha caducado, si deseas extender tu contrato contactanos por nuestros canales oficiales."}))
                e.estado = False
                e.save()
                datos=e.user_datos
                datos.estado=False
                datos.save()

            return Response("OK")
        except:
            return Response("error: ")

class Bancos(APIView):
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


class VerionAndroidSolicitante(APIView):
    def get(self, request):
        return Response(1)

class VerionIosProveedor(APIView):
    def get(self, request):
        return Response(1)

class VerionAndroidProveedor(APIView):
    def get(self, request):
        return Response(1)

class VerionIosProveedor(APIView):
    def get(self, request):
        return Response(1)