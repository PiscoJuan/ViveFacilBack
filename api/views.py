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
from rest_auth.registration.views import SocialLoginView
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as do_login
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.template.loader import get_template
from fcm_django.models import FCMDevice
from pyfcm import FCMNotification
# from firebase_admin.messaging import Message, Notification
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
        devices = FCMDevice.objects.filter(user=correo)
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
        device = FCMDevice.objects.filter(registration_id=token)
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
        devices = FCMDevice.objects.filter(user=correo)
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
            # emails = request.data.get('emails')
            try:
                asunto = 'Factura Pago de Servicios Vive Fácil'
                thread = threading.Thread(target=formatEmail.send_email(emails, asunto, 'emails/factura.html', {"fecha_today": fecha, "fecha_emision": fecha, "solicitante_name": user.nombres + ' ' + user.apellidos, "solicitud_descripcion": descripcion,
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
                codigo = get_random_string(length=6).upper()
                codigo_creada = Codigos.objects.create(
                    user_datos=user_dato, codigo=codigo, estado=True)
                formatEmail = FormatEmail()
                asunto = 'Código para Reestablecer Contraseña | TO-ME'
                thread = threading.Thread(target=formatEmail.send_email(
                    [user_email], asunto, 'emails/emailCodigo.html', {"username": user_dato.nombres, "codigo": codigo}))
                thread.start()
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
                devices.send_message(
                    data=dataMensaje,
                    title=titles,
                    body=bodys,
                )
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
        dataMensaje["descripcion"] = "Lamentamos informarles que la Categoría " + \
            categoria.nombre + " ha sido eliminada de la aplicación"
        dataMensaje["ruta"] = "/main-tabs/home"
        devices.send_message(
            data=dataMensaje,
            title="Categoría Eliminada: "+categoria.nombre,
            body="¡Sorry, no podrás acceder a la categoría!",
        )
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
        devices.send_message(

            title="Nueva Categoría: "+nombre,
            body="¡Dale un vistazo!",
            data={"ruta": "/main-tabs/home",
                  "descripcion": "Vive Fácil cuenta con una nueva Categoría llamada " + categoria_creada.nombre},
        )

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
        servicios = Servicio.objects.all().filter()
        serializer = ServicioSerializer(servicios, many=True)
        return Response(serializer.data)

    def put(self, request, id, format=None):
        servicios = Servicio.objects.get(id=id)
        serializer = ServicioSerializer(
            servicios, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        servicios = Servicio.objects.get(id=id)
        nombreServico = servicios.nombre
        servicios.delete()
        # Notificacion a los usuarios
        devices = FCMDevice.objects.filter(
            active=True, user__groups__name='Solicitante')
        devices.send_message(
            title="Servicio Eliminado: " + nombreServico,
            body="¡Sorry, no podrás acceder al Servicio!",
            data={"ruta": "/main-tabs/home", "descripcion": "El servicio " +
                  nombreServico + " se ha eliminado de nuestro aplicativo"},
        )
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
        if servicio_creado:
            # Notificacion a los usuarios

            #devices = FCMDevice.objects.filter(
            #    active=True, user__groups__name="Solicitante")
            #devices.send_message(
            #    data={"ruta": "/main-tabs/home", "descripcion": "El servicio " +
            #          nombre + " se ha agregado a nuestro aplicativo"},
            #    title="Nuevo Servicio: "+nombre,
            #    body="¡Dale un vistazo!",
            #)

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
                    elif tipo_user == 'Proveedor':
                        # Proveedor.objects.create(user_datos= dato, bool_registro_completo= True)
                        try:
                            proveedor_user, created = Proveedor.objects.get_or_create(user_datos=dato, ano_profesion=0)
                            # pendiente, created_p = Proveedor_Pendiente.get_or_create(proveedor=proveedor_user, email = request.data.get('email'))
                            print("Proveedor email: " + proveedor_user.user_datos.user.email)
                        except:
                            print("No se pudo crear el perfil de proveedor")
                            data['error'] = "No se pudo crear el perfil de proveedor"
                            data['success'] = False
                            return Response(data)
                        else:
                            try:
                                #trabajo
                                print("trabalho?")
                                profesion_obnj = Profesion.objects.get(nombre=request.POST.get('profesion'))
                                profesion_proveedor = Profesion_Proveedor.objects.create(proveedor=proveedor_user, profesion=profesion_obnj,ano_experiencia=request.POST.get('ano_experiencia'))
                                print("trabalho!!!!!!")
                                # crear cuenta
                                banco_user = Banco.objects.get_or_create(nombre=request.POST.get('banco'))
                                tipo_cuenta_user = Tipo_Cuenta.objects.get_or_create(nombre=request.POST.get('tipo_cuenta'))
                                numero_account = request.POST.get('numero_cuenta')
                                cuenta = Cuenta.objects.get_or_create(banco=banco_user[0], tipo_cuenta=tipo_cuenta_user[0], proveedor=proveedor_user, numero_cuenta=numero_account)
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
                # thread = threading.Thread(target =email.send_email(user_email,'Bienvenido a TOME','emails/welcome.html',{"username":nombre_user}))
                # thread.start()
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
                cupon_1 = Cupon.objects.get(id='1')

                if (cupon_1):
                    data['cr'] = True

                cup_create, creado = Cupon_Aplicado.objects.get_or_create(
                    cupon=Cupon.objects.get(id=cup_id), user=user_dat, estado=estado_dat)
                data['creado'] = True
            else:
                data['creado'] = False

            data['success'] = True
        except:
            data['error'] = "No se pudo adjudicar el cupon"
            data['success'] = False
            data['user'] = user
            data['cupon'] = cupon

            return Response(data)
        else:
            return Response(data)

    def put(self, request, formato=None):
        user_dat = request.data.get('user')
        cup_id = request.data.get('cupon_id')
        cupon_aplic = Cupon_Aplicado.objects.filter(
            user=user_dat, cupon=Cupon.objects.get(id=cup_id))
        if cupon_apic:
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
                    data['error'] = "No se pudo crear el perfil de proveedor"
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
                    data['error'] = "No se pudo crear el perfil de proveedor"
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
        documentos = request.FILES.getlist('planilla_servicios')

        data['data'] = {nombres_prov}

        proveedor_pend = Proveedor_Pendiente.objects.create(nombres=nombres_prov, apellidos=apellidos_prov, genero=genero_prov, telefono=telefono_prov, cedula=cedula_prov, copiaCedula=cedula_copia, ciudad=ciudad_prov, direccion=direccion_prov,
                                                            email=email_prov, licencia=licencia, copiaLicencia=licencia_copia, profesion=profesion_prov, ano_experiencia=ano_experiencia_prov, banco=banco_prov, numero_cuenta=numero_cuenta_prov, tipo_cuenta=tipo_cuenta_prov, descripcion=descripcion)
        prov_pendiente = Proveedor_Pendiente.objects.get(id=proveedor_pend.id)
        for doc in documentos:

            documento_creado = PendienteDocuments.objects.create(document=doc)
            prov_pendiente.documentsPendientes.add(documento_creado)

        serializer = Proveedor_PendienteSerializer(proveedor_pend)

        data['success'] = True
        data['serializer'] = serializer.data

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


class Proveedores_Pendientes_Details(APIView):

    def get(self, request, pk, format=None):

        administrador = Proveedor_Pendiente.objects.get(id=pk)
        serializer = Proveedor_PendienteSerializer(administrador)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        pendiente = Proveedor_Pendiente.objects.get(id=pk)
        copiaCedula = request.data.get('copiaCedula')
        copiaLicencia = request.data.get('copiaLicencia')
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


class Proveedores_Rechazados_Details(APIView):

    def get(self, request, pk, format=None):

        administrador = Proveedor_Pendiente.objects.get(id=pk)
        serializer = Proveedor_PendienteSerializer(administrador)
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
            proveedor = Proveedor.objects.get(user_datos__user__id=id_user)
            solicitud = Solicitud.objects.get(id=solicitud_ID)
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
                devices.send_message(
                    data={"ruta": "/historial",
                          "descripcion": "Se le ha adjudicado el siguiente servicio: " + solicitud.servicio.nombre},
                    title=titles,
                    body=bodys,
                )
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
            serializer = SolicitudSerializer(
                solicitud, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if request.data.get("termino") != "cancelado":
                    proveedor = solicitud.proveedor
                    solicitudes = Solicitud.objects.filter(
                        proveedor=proveedor)  # .values('rating')
                    ratingProveedor = solicitudes.aggregate(
                        Sum('rating'))['rating__sum'] / len(solicitudes)
                    proveedor.rating = ratingProveedor
                    proveedor.servicios = len(solicitudes)
                    proveedor.save()
                    titles = 'Servicio finalizado: '+solicitud.servicio.nombre
                    bodys = '¡Dale un vistazo!'
                    devices = FCMDevice.objects.filter(
                        active=True, user__username=solicitud.proveedor.user_datos.user.email)
                    devices.send_message(
                        data={"ruta": "/historial", "descripcion": "Puede observar la solicitud " +
                              solicitud.servicio.nombre + " finalizada en la seccion de Historial > PASADAS"},
                        title=titles,
                        body=bodys,
                    )
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
        # Data de respuesta
        data = {}

        # solicitud
        desc = request.data.get('descripcion')
        foto_desc = request.data.get('foto_descripcion')
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
        foto_ubic = request.data.get('foto_ubicacion')

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
                                                 ubicacion=ubic, tipo_pago=t_pago, servicio=service, foto_descripcion=foto_desc)
            serializer = SolicitudSerializer(solicitud)
        except Exception as e:
            solicitud.delete()
            data['message'] = "No se pudo o crear al objeto Solicitud: " + \
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
        # devices = FCMDevice.objects.filter(active=True,user__groups__name='Proveedor')
        # devices = FCMDevice.objects.filter(user__groups__name='Proveedor')
        # devices.send_message(
        #     data = {"ruta": "Carrito", "descripcion": "Se ha recibido una solicitud del siguiente servicio: " +solicitud.servicio.nombre},
        #     title=titles,
        #     body=bodys,
        # )
        for proveedor in proveedores_id:
            # Intenta obtener un Objeto Proveedor en la base de datos.
            try:
                prov = Proveedor.objects.get(id=proveedor)
            except Exception as e:
                solicitud.delete()
                data['message'] = "Ha ocurrido un error al obtener un objeto Proveedor de la base de datos: " + \
                    str(e)
                data['success'] = False
                return Response(data)

            # Intenta crear un Objeto Envio_Interesados en la base de datos.
            try:
                envio_interesados = Envio_Interesados.objects.create(
                    solicitud=solicitud, proveedor=prov)
            except Exception as e:
                solicitud.delete()
                envio_interesados.delete()
                data['message'] = "Ha ocurrido un error al crear el objeto Envio_Interesados: " + \
                    str(e)
                data['success'] = False
                return Response(data)

            # Intenta mandar una notificacion al proveedor con el id.
            try:
                devices = FCMDevice.objects.filter(
                    user__id=prov.user_datos.user.id)
                devices.send_message(
                    data={"ruta": "/main/home",
                          "descripcion": "Se ha recibido una solicitud del siguiente servicio: " + solicitud.servicio.nombre},
                    title=titles,
                    body=bodys,
                )
            except Exception as e:
                solicitud.delete()
                envio_interesados.delete()
                data['message'] = "Ha ocurrido un error al enviar la notificacion al proveedor: " + \
                    str(e)
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
        profesion = Profesion.objects.all().filter()
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
        prov_prof = Profesion_Proveedor.objects.all().filter(
            profesion__servicio__id=servicio_id)
        serializer = Profesion_ProveedorSerializer(prov_prof, many=True)
        return Response(serializer.data)


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
        proveedor.delete()
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
            devices = FCMDevice.objects.filter(
                user__id=proveedorActual.user_datos.user.id)
            dataMensaje["ruta"] = "/perfil"
            dataMensaje["descripcion"] = "¡Su solicitud de agregar profesión fue aceptada!"
            devices.send_message(
                title="Tienes una Nueva Profesión: "+profesion,
                body="¡Dale un vistazo!",
                data=dataMensaje,

            )
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

    def post(self, request, format=None):  # Modified by Kevin
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
    queryset = Proveedor_Pendiente.objects.all().order_by('-id').filter(estado=1)
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


class Proveedores_Proveedores(APIView, MyPaginationMixin):
    # permission_classes = (IsAuthenticated,)
    # authentication_class = (TokenAuthentication)
    # def get(self, request, format=None):
    #     proveedor_pendiente = Proveedor_Pendiente.objects.all().filter()
    #     serializer = Proveedor_PendienteSerializer(proveedor_pendiente,many= True)
    #     return Response(serializer.data)
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


class DatosUsers(APIView):  # Created By KevinChevez
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


class Usuarios(APIView):  # Created By KevinChevez
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


class SolicitanteByUserDatos(APIView):  # Kevin Endopint Add
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
        # print(JSONRenderer().render(serializer.data))
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
            devices.send_message(
                title="Tienes una Nueva Profesión: "+profesion,
                body="¡Dale un vistazo!",
            )
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
        solicitante = solicitud.solicitante
        envio_interesado = Envio_Interesados.objects.all().get(
            solicitud=solicitud_ID, proveedor__user_datos__user__username=user)
        serializer = Envio_InteresadosSerializer(
            envio_interesado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Notificacion al solicitante que realizo la oferta
            titles = 'Tienes una nueva oferta en el servicio de ' + \
                solicitud.servicio.nombre + ' que solicitaste.'
            bodys = '¡Dale un vistazo!'
            devices = FCMDevice.objects.filter(
                active=True, user__username=solicitante.user_datos.user.email)
            devices.send_message(
                data={"ruta": "/historial",
                      "descripcion": "Ha recibido una oferta en el siguiente servicio: " + solicitud.servicio.nombre},
                title=titles,
                body=bodys,
            )
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
        title = 'Nuevo Mensaje de ' + str(remitente)
        isSolicitante = request.data.get("isSolicitante")
        body = request.data.get("message")
        user = request.data.get("user")
        url = request.data.get("url")
        ruta = ""
        if isSolicitante:
            ruta = "/main-tabs/chat"
        else:
            ruta = "/main/chat"
        devices = FCMDevice.objects.filter(user=user)
        devices.send_message(
            title=title,
            body=body,
            data={"url": url, "ruta": ruta,
                  "descripcion": "Tiene un Mensaje nuevo"}
        )
        return Response(user)


class Notificacion_Chat_Proveedor(APIView):
    def post(self, request, format=None):
        remitente = request.data.get("remitente")
        getUsuario = request.data.get("user")
        # usuario = Datos.objects.get(user_#id=getUsuario)
        solicitante = Solicitante.objects.get(user_datos__id=getUsuario)
        titles = 'Nuevo Mensaje de ' + str(remitente)
        bodys = request.data.get("message")
        devices = FCMDevice.objects.filter(
            active=True, user__username=solicitante.user_datos.user.email)
        devices.send_message(
            data={"ruta": "/main/chat",
                  "descripcion": "Tiene un Mensaje nuevo"},
            title=titles,
            body=bodys,
        )
        return Response(getUsuario)


class Notificacion_General(APIView):
    def post(self, request, format=None):
        body = request.data.get("message")
        user = request.data.get("user")
        title = request.data.get("title")
        devices = FCMDevice.objects.filter(user__username=user)
        devices.send_message(
            data={"ruta": "Historial", "descripcion": "Proveedor Interesado"},
            title=title,
            body=body
        )
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
                proveedor = Proveedor.objects.get(user_datos=usuario)
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
                elif (tipo == res_tipo and usuario.estado == False):
                    data['active'] = False
                    data['form'] = request.data
                    return Response(data)
                else:
                    data['error'] = 'Usuario no permitido'
                    data['active'] = True
                    data['form'] = request.data
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data['error'] = 'Error de formulario'
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
                return Response(data)
            else:
                data['error'] = 'Usuario no permitido'
                data['active'] = True
                data['form'] = request.data
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
                return Responde(data)


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

    def delete(self, request, id, format=None):
        notificacion = Notificacion.objects.get(id=id)
        notificacion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
                devices.send_message(
                    data={"ruta": "Home",
                          "descripcion": "Se ha creado una nueva promoción"},
                    title=titles,
                    body=bodys,
                )

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
        cant = request.data.get('cantidad')
        puntos = request.data.get('puntos')
        photo = request.data.get('foto')
        type_category = request.data.get('tipo_categoria')

        try:
            cupon = Cupon.objects.create(titulo=title, descripcion=desc, fecha_expiracion=exp, porcentaje=descuent,
                                         codigo=code, fecha_iniciacion=ini, puntos=puntos, foto=photo, tipo_categoria=type_category, cantidad=cant)

        except:
            data['error'] = "No se pudo crear el cupon"
            return Response(data)
        else:

            try:
                for categoria in request.POST.getlist('categorias'):
                    categ = Categoria.objects.all().filter(nombre=categoria)
                    promcat = CuponCategoria.objects.create(
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
                devices.send_message(
                    data={"ruta": "/promociones",
                          "descripcion": "Se encuentra disponible un nuevo cupón!"},
                    title=titles,
                    body=bodys,
                )

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
        # Cambio CuponesCategoria por CuponCategoria. Kevin
        cupones = CuponCategoria.objects.all().filter(cupon__codigo=cupCode)
        serializer = CuponCategoriaSerializer(cupones, many=True)
        return Response(serializer.data)


class AllCuponesCategoria(APIView):  # Created By Kevin
    def get(self, request, format=None):
        cupones = CuponCategoria.objects.all()
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
                pago_tarjeta_user = PagoTarjeta.objects.create(user=usuario, tarjeta=tarjeta, carrier_id=carrier_ID, carrier_code=carrier_c, promocion=promocion, valor=amount, descripcion=desc, impuesto=impuesto,
                                                               referencia=referencia, cargo_paymentez=carg_Pay, cargo_banco=carg_Banc, cargo_sistema=carg_Sis, usuario=us, servicio=serv, proveedor=prov, prov_correo=prov_email, prov_telefono=prov_phone)
                data['detail'] = "pago_solicitud"
                pago_solicitud = PagoSolicitud.objects.create(
                    pago_tarjeta=pago_tarjeta_user, solicitud=solicitud)
            except:
                data['error'] = "No se pudo guardar el pago/sin embargo, si se realizo"
                return Response(data)
            else:
                data['success'] = True
                data['msg'] = "El pago se guardo exitosamente"
                serializer = PagoTarjetaSerializer(pago_tarjeta_user)
                data['pago_tarjeta'] = serializer.data
                titles = 'Servicio pagado: '+solicitud.servicio.nombre
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__username=solicitud.proveedor.user_datos.user.email)
                devices.send_message(
                    data={"ruta": "/historial", "descripcion": "El pago por el servicio de " +
                          solicitud.servicio.nombre + " fue existoso"},
                    title=titles,
                    body=bodys,
                )
                return Response(data)


class PagosEfectivo(APIView):
    def post(self, request, format=None):
        data = {}
        data['success'] = False
        user = request.data.get('username')
        promotion = request.data.get('promocion')  # codigo de la promocion
        amount = request.data.get('valor')
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
                pago_efectivo_user = PagoEfectivo.objects.create(user=usuario, promocion=promocion, valor=amount, descripcion=desc, referencia=referencia,
                                                                 usuario=us, servicio=serv, proveedor=prov, prov_correo=prov_email, prov_telefono=prov_phone, user_telefono=us_phone)
                data['detail'] = "pago_solicitud"
                pago_solicitud = PagoSolicitud.objects.create(
                    pago_efectivo=pago_efectivo_user, solicitud=solicitud)
            except:
                data['error'] = "No se pudo guardar el pago/sin embargo, si se realizo"
                return Response(data)
            else:
                data['success'] = True
                data['msg'] = "El pago se guardo exitosamente"
                serializer = PagoEfectivoSerializer(pago_efectivo_user)
                data['pago_efectivo'] = serializer.data

                titles = 'Servicio pagado: '+solicitud.servicio.nombre
                bodys = '¡Dale un vistazo!'
                devices = FCMDevice.objects.filter(
                    active=True, user__id=solicitud.proveedor.user_datos.user.id)
                devices.send_message(
                    data={"ruta": "/historial", "descripcion": "El pago por el servicio de " +
                          solicitud.servicio.nombre + " fue existoso"},
                    title=titles,
                    body=bodys,
                )
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
        totalE = PagoEfectivo.objects.aggregate(Sum('valor'))
        totalT = PagoTarjeta.objects.aggregate(Sum('valor'))
        total = totalE["valor__sum"] + totalT["valor__sum"]

        return Response(total)


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
        devices.send_message(
            title="categoria Eliminada: "+categoria.nombre,
            body="¡Sorry, no podrás acceder a la categoria!",
        )
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
        if politics:
            return Response(data)
        else:
            data['error'] = "Error al crear!."
            return Response(data)


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
        return Response(PlanProveedorSerializer(plan).data)


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
        proveedor.tipo: cuenta = request.data.get("tipo_cuenta")

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
        titles = request.data.get('titulo')
        body_notificacion = request.data.get('mensaje')
        imagen = request.FILES.get('imagen')
        ruta = request.data.get('ruta')
        descripcion = request.data.get('descripcion')

        notificacion = NotificacionMasiva.objects.create(
            titulo=titles, mensaje=body_notificacion, descripcion=descripcion, ruta=ruta, imagen=imagen)
        notificacion.save()
        dataNot = {}
        if imagen is not None:
            dataNot["imagen"] = notificacion.imagen.url
        dataNot["ruta"] = ruta
        dataNot["descripcion"] = descripcion
        try:
            devices = FCMDevice.objects.filter(active=True)
            devices.send_message(
                data=dataNot,
                title=titles,
                body=body_notificacion,
            )
            data['success'] = True
            data['message'] = "La notificación ha sido creada correctamente."
            serializer = NotificacionMasivaSerializer(notificacion)
            data['notificacion_masiva'] = serializer.data
            return Response(data)
        except:
            notificacion.delete()
            data['success'] = False
            data['message'] = "Hubo un error al enviar la notificación."
            return Response(data)

    def delete(self, request, id):
        data = {}
        notificaciones = NotificacionMasiva.objects.all()
        # for notificacion in notificaciones:
        #     notificacion.delete()
        # data['success']= True
        # data['message']= "Se ha eliminado la notificación exitosamente."
        # return Response(data)
        try:
            notificacion_masiva = NotificacionMasiva.objects.get(id=id)
            notificacion_masiva.delete()
            data['success'] = True
            data['message'] = "Se ha eliminado la notificación exitosamente."
            return Response(data)
        except:
            data['success'] = False
            data['message'] = "La notificación no fue encontrada en la base de datos."
            return Response(data)


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
