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


class AdminPage(APIView):
    def get (self, request):
        return redirect(to="/static/index.html")
