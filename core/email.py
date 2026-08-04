from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.templatetags.static import static
from rest_framework.views import APIView

FACEBOOK_URL = "https://www.facebook.com/vivefacil.ec"
INSTAGRAM_URL = "https://www.instagram.com/vivefacil_ec"


def brand_context():
    """Logo y redes de la marca. Fuera de FormatEmail porque la página web de
    cambio de contraseña también la usa, y no manda correos."""
    host = settings.URL_BACKEND_HOST.rstrip('/')
    return {
        "logo_url": host + static("vivefacil/logo.png"),
        "icon_facebook": host + static("vivefacil/facebook.png"),
        "icon_instagram": host + static("vivefacil/instagram.png"),
        "url_facebook": FACEBOOK_URL,
        "url_instagram": INSTAGRAM_URL,
    }


class FormatEmail(APIView):
    def _brand_context(self):
        return brand_context()

    def create_email(self, email, subject, template_path, context):
        template = get_template(template_path)
        content = template.render({**self._brand_context(), **context})
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
