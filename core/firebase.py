import logging
import threading

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

def borrar_cuenta_firebase(email):
    """Borra de Firebase Auth la cuenta de `email`. True si la borró, False si
    no existía. Cualquier otro error se propaga."""
    import firebase_admin
    from firebase_admin import auth, credentials

    # settings ya hace initialize_app al importarse; esto solo cubre el caso de
    # que ese try haya fallado (credenciales ausentes, red caída al arrancar).
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(settings.CRED_PATH))
    try:
        auth.delete_user(auth.get_user_by_email(email).uid)
        return True
    except auth.UserNotFoundError:
        return False


class TokenFirebase:
    expirado = False
    nuevo_token = None


def get_firebase_access_token():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            settings.CRED_PATH,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"]
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception:
        logger.error("Error al inicializar Firebase Admin SDK o al obtener el token de acceso", exc_info=True)
        return None


def _desactivar_token(token):
    """FCM contestó 404 (UNREGISTERED): la app se desinstaló o el token rotó.
    Se da de baja el dispositivo para dejar de enviarle — sin esto los tokens
    viejos se acumulan (hay usuarios con 10-17 activos) y cada notificación
    cuesta un POST por cada uno."""
    try:
        from fcm_django.models import FCMDevice
        bajas = FCMDevice.objects.filter(registration_id=token, active=True).update(active=False)
        if bajas:
            logger.info("Token FCM dado de baja (no registrado)", extra={"fcm_token": token})
    except Exception:
        logger.exception("No se pudo dar de baja el token FCM")


def send_notificationF_async(tokend, title, body, data, tag=None):
    """Igual que `send_notificationF` pero fuera del request.

    El envío hace un POST por token con timeout de 15s y en serie, así que con
    varios destinatarios el request se alargaba tanto que el cliente lo
    abandonaba, y la conexión MySQL —abierta y ociosa mientras tanto— se moría
    con "Lost connection to MySQL server during query" (2013).
    """
    def _worker():
        try:
            send_notificationF(tokend, title, body, data, tag=tag)
        except Exception:
            logger.exception("Fallo enviando notificaciones en segundo plano")
        finally:
            # El hilo abre su propia conexión a la BD (`_desactivar_token`); si
            # no se cierra queda colgando y se agotan las del plan.
            from django.db import connection
            connection.close()

    threading.Thread(target=_worker, daemon=True).start()


@csrf_exempt
def send_notificationF(tokend, title, body, data, tag=None):
    """`tag` agrupa notificaciones que se reemplazan entre sí (una sola en la
    bandeja, con el último contenido). Se usa para el chat: sin esto cada
    mensaje apilaba una notificación nueva y el historial entero terminaba ahí.
    Es opcional a propósito — las notificaciones que no lo pasan (ofertas,
    solicitudes, anuncios) se comportan exactamente igual que antes."""
    try:
        responses = []
        success_flag = False
        token_trabajo = settings.FIREBASE_ACCESS_TOKEN
        if not token_trabajo or TokenFirebase.expirado:
            token_trabajo = TokenFirebase.nuevo_token
        if not token_trabajo:
            logger.error("No se pudo obtener el token de Firebase")
            return JsonResponse({"error": "No se pudo obtener el token de Firebase"}, status=500)

        unique_tokens = list(set(tokend))
        logger.info("Token Firebase listo, notificando", extra={"num_tokens": len(unique_tokens)})

        for token in unique_tokens:
            message = {
                "message": {
                    "token": token,
                    "notification": {"title": title, "body": body},
                    "data": data
                }
            }

            if tag:
                # `notification.tag`: Android reemplaza la anterior con ese tag.
                # `collapse_key`: si el equipo estuvo sin red, FCM entrega solo
                # la última en vez de la ráfaga entera.
                message["message"]["android"] = {
                    "collapse_key": tag,
                    "notification": {"tag": tag},
                }
                message["message"]["apns"] = {"headers": {"apns-collapse-id": tag}}

            # ponytail: timeout explícito — sin esto, si fcm.googleapis.com se
            # cuelga, requests espera para siempre y bloquea todo el request de
            # crear_solicitud (visto en campo: sube el 100% y nunca llega respuesta).
            response = requests.post(
                settings.ACCESS_URL,
                json=message,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token_trabajo}'
                },
                timeout=15,
            )

            # Si el token expiró (401/403), lo renovamos y reintentamos una vez
            if response.status_code in (401, 403):
                logger.warning("Token Firebase expirado, renovando...")
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
                        },
                        timeout=15,
                    )

            logger.info("Respuesta Firebase", extra={"fcm_token": token, "status_code": response.status_code})

            # Solo el 404 significa "este token ya no existe". Un 400 puede ser
            # un payload mal armado y daría de baja tokens sanos.
            if response.status_code == 404:
                _desactivar_token(token)

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
        logger.error("Error general al enviar notificación", exc_info=True)
        return JsonResponse({"error": "Error interno en el servidor", "details": str(e)}, status=500)
