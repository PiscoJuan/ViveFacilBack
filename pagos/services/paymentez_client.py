"""
Cliente de la API de Paymentez/Nuvei.

La tokenización de la tarjeta ocurre en el frontend con el SDK JS de Paymentez;
el backend nunca recibe el PAN, solo el `token`, `bin`, `type`, etc.

Solo se implementa lo necesario para este proyecto (sin pago diferido):
    - debit            (transaction/debit)
    - verify           (transaction/verify)  -> OTP / 3DS
    - list_cards       (card/list)
    - delete_card      (card/delete)
    - refund           (transaction/refund)
"""
import hashlib
import hmac
import time
from base64 import b64encode
from decimal import Decimal
from hashlib import sha256

import requests
from django.conf import settings

from pagos.models import ConfiguracionPaymentez
from pagos.services.responses import interpretar_respuesta

TIMEOUT = 30


class PaymentezError(Exception):
    """Error de conexión/configuración con Paymentez."""


class PaymentezClient:
    def __init__(self, config: ConfiguracionPaymentez = None):
        self.config = config or ConfiguracionPaymentez.objects.filter(is_active=True).first()
        if not self.config:
            raise PaymentezError("No hay una configuración de Paymentez activa.")
        self.base_url = self.config.url_base
        if not self.base_url.endswith("/"):
            self.base_url += "/"

    # ------------------------------------------------------------------ auth
    def _auth_token(self) -> str:
        server_code = self.config.app_code_server
        server_key = self.config.app_key_server
        unix_timestamp = str(int(time.time()))
        uniq = sha256(f"{server_key}{unix_timestamp}".encode()).hexdigest()
        token = f"{server_code};{unix_timestamp};{uniq}".encode()
        return b64encode(token).decode()

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Auth-Token": self._auth_token(),
        }

    def _post(self, path, payload, endpoint):
        try:
            resp = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=self._headers(),
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise PaymentezError(f"No se pudo conectar con Paymentez: {exc}")
        return interpretar_respuesta(resp, endpoint)

    # --------------------------------------------------------------- payloads
    def build_payload_debit(self, *, user_id, email, monto, descripcion,
                            dev_reference, card_token, card_cvc, browser_info=None,
                            threeds_ctx=None, vat=0, taxable_amount=0, tax_percentage=0):
        payload = {
            "user": {"id": str(user_id), "email": email or "sincorreo@vivefacil.ec"},
            "order": {
                "amount": float(round(monto, 2)),
                "description": descripcion,
                "dev_reference": dev_reference,
                "vat": float(round(vat, 2)),
                "taxable_amount": float(round(taxable_amount, 2)),
                "tax_percentage": float(round(tax_percentage, 2)),
            },
            "card": {
                "token": card_token,
                "cvc": card_cvc,
            },
        }
        if browser_info and threeds_ctx:
            term_url = (
                f"{settings.URL_BACKEND_HOST}/solicitante/pagos/3ds-term/{threeds_ctx}/"
            )
            payload["extra_params"] = {
                "threeDS2_data": {
                    "term_url": term_url,
                    "device_type": "browser",
                    "process_anyway": False,
                },
                "browser_info": browser_info,
            }
        return payload

    @staticmethod
    def build_payload_verify(transaction_id, value, user_id, tipo="BY_OTP"):
        return {
            "user": {"id": str(user_id)},
            "transaction": {"id": transaction_id},
            "type": tipo,
            "value": value,
            "more_info": True,
        }

    # --------------------------------------------------------------- webhook
    @staticmethod
    def stoken_valido(transaction_id, user_id, stoken_recibido, config=None) -> bool:
        """
        Verifica la autenticidad del webhook de Nuvei/Paymentez:
        stoken = MD5("[transaction_id]_[application_code]_[user_id]_[app_key]")
        usando las credenciales server (app_code_server / app_key_server).
        """
        config = config or ConfiguracionPaymentez.objects.filter(is_active=True).first()
        if not config or not stoken_recibido or not transaction_id:
            return False
        base = (
            f"{transaction_id}_{config.app_code_server}_{user_id}_{config.app_key_server}"
        )
        esperado = hashlib.md5(base.encode()).hexdigest()
        return hmac.compare_digest(esperado, str(stoken_recibido))

    # ------------------------------------------------------------- operaciones
    def debit(self, payload):
        return self._post("transaction/debit/", payload, "debit")

    def verify(self, transaction_id, value, user_id, tipo="BY_OTP"):
        payload = self.build_payload_verify(transaction_id, value, user_id, tipo)
        return self._post("transaction/verify/", payload, "verify")

    def delete_card(self, token, user_id):
        payload = {"card": {"token": token}, "user": {"id": str(user_id)}}
        return self._post("card/delete/", payload, "delete_card")

    def list_cards(self, user_id):
        try:
            resp = requests.get(
                f"{self.base_url}card/list",
                headers=self._headers(),
                params={"uid": str(user_id)},
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise PaymentezError(f"No se pudo conectar con Paymentez: {exc}")
        try:
            data = resp.json()
        except ValueError:
            raise PaymentezError("Respuesta inválida de Paymentez al listar tarjetas.")
        return data.get("cards", []) or []

    def refund(self, transaction_id, amount=None):
        """
        Reembolsa una transacción de TARJETA vía ccapi (transaction/refund/),
        el mismo host/credenciales del débito. amount=None => reembolso total.
        Devuelve {ok, mensaje, data, status_detail}.
        """
        payload = {"transaction": {"id": str(transaction_id)}}
        if amount is not None:
            payload["order"] = {"amount": float(round(Decimal(str(amount)), 2))}
        try:
            resp = requests.post(
                f"{self.base_url}transaction/refund/",
                json=payload,
                headers=self._headers(),
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise PaymentezError(f"No se pudo conectar con Paymentez: {exc}")
        try:
            data = resp.json()
        except ValueError:
            raise PaymentezError("Respuesta inválida de Paymentez en el reembolso.")

        error = data.get("error") or {}
        tx = data.get("transaction") or {}
        ok = (
            resp.status_code == 200
            and not error
            and data.get("status") != "failure"
            and tx.get("status") != "failure"
        )
        if error:
            mensaje = error.get("description") or error.get("help") or error.get("type")
        else:
            mensaje = data.get("detail") or tx.get("message")
        return {
            "ok": ok,
            "mensaje": str(mensaje) if mensaje else "",
            "data": data,
            "status_detail": tx.get("status_detail"),
        }
