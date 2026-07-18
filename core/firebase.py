import logging

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


class TokenFirebase:
    expirado = False
    nuevo_token = None


def get_firebase_access_token():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        import os
        from TomeSoft_1.settings import BASE_DIR

        credentials = service_account.Credentials.from_service_account_file(
            os.path.join(BASE_DIR, 'TomeSoft_1/vive-facil-66ae4-firebase-adminsdk-fo42r-94d590fc9a.json'),
            scopes=["https://www.googleapis.com/auth/firebase.messaging"]
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception:
        logger.error("Error al inicializar Firebase Admin SDK o al obtener el token de acceso", exc_info=True)
        return None


@csrf_exempt
def send_notificationF(tokend, title, body, data):
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
