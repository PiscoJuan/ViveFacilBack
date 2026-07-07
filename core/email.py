from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from rest_framework.views import APIView


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
