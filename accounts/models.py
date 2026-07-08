from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from rest_framework.authtoken.models import Token


class Document(models.Model):
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    documento = models.FileField(upload_to='documents', null=True)
    estado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_document"

    def __str__(self):
        return str(self.descripcion)

    def delete(self, *args, **kwargs):
        self.documento.delete()
        super().delete(*args, **kwargs)


class Datos(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    tipo = models.ForeignKey('auth.group', on_delete=models.PROTECT, null=True)
    nombres = models.CharField(max_length=255, null=True)
    apellidos = models.CharField(max_length=255, null=True)
    ciudad = models.CharField(max_length=20, null=True)
    cedula = models.CharField(max_length=20, null=True, default="0999999999")
    telefono = models.CharField(max_length=15)
    genero = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='foto_perfil', null=True, blank=True)
    estado = models.BooleanField(default=True)
    security_access = models.UUIDField(
        primary_key=False, editable=False, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    puntos = models.PositiveIntegerField(default=0, null=True)
    codigo_invitacion = models.CharField(max_length=12, default="", null=True)
    dinero_invertido = models.PositiveIntegerField(default=0, null=True)
    tramites = models.PositiveIntegerField(default=0, null=True)
    descuento = models.PositiveIntegerField(default=0, null=True)

    class Meta:
        db_table = "api_datos"

    def __str__(self):
        return str(self.nombres) + " | " + str(self.apellidos) + " | " + self.genero


class Codigos(models.Model):  # codigos que se envian para reestablecer contrasena
    user_datos = models.ForeignKey(Datos, on_delete=models.CASCADE, null=True)
    codigo = models.CharField(max_length=255, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_codigos"


class Proveedor(models.Model):
    user_datos = models.OneToOneField(
        Datos, on_delete=models.CASCADE, null=True)
    rating = models.FloatField(default=4.0)
    servicios = models.PositiveIntegerField(default=0)
    descripcion = models.CharField(max_length=255)
    document = models.ManyToManyField(Document, db_table="api_proveedor_document")
    estado = models.BooleanField(default=True)
    profesion = models.CharField(max_length=400, default='')

    copiaCedula = models.FileField(
        upload_to='documentos-Proveedor', null=True, blank=True)
    direccion = models.CharField(max_length=300, default='')
    licencia = models.CharField(max_length=55, default='')
    copiaLicencia = models.FileField(
        upload_to='documentos-Proveedor', null=True, blank=True)

    ano_profesion = models.CharField(max_length=400, default='')
    banco = models.CharField(max_length=255, default='')
    numero_cuenta = models.CharField(max_length=25, default='')
    tipo_cuenta = models.CharField(max_length=50, default='')

    fecha_caducidad = models.DateTimeField(default=now, null=True)

    class Meta:
        db_table = "api_proveedor"

    def __str__(self):
        return self.user_datos.nombres + " " + self.user_datos.apellidos + " | " + self.profesion


class PendienteDocuments(models.Model):
    document = models.FileField(
        upload_to='pendientes-documents', null=True, blank=True)

    class Meta:
        db_table = "api_pendientedocuments"

    def delete(self, *args, **kwargs):
        self.document.delete()
        super().delete(*args, **kwargs)


# tabla que guarda la info de las personas que quieren ser proveedores.
class Proveedor_Pendiente(models.Model):
    nombres = models.CharField(max_length=255, default='')
    apellidos = models.CharField(max_length=255, default='')
    ciudad = models.CharField(max_length=255, default='')
    direccion = models.CharField(max_length=300, default='')
    genero = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=255, default='')
    copiaCedula = models.FileField(upload_to='pendientes-copias', null=True)
    telefono = models.CharField(max_length=255, default='')
    descripcion = models.TextField()
    cedula = models.CharField(max_length=255, default='')
    estado = models.BooleanField(default=False)
    profesion = models.CharField(max_length=255, default='')
    licencia = models.CharField(max_length=55, default='')
    copiaLicencia = models.FileField(upload_to='pendientes-copias', null=True)
    ano_experiencia = models.PositiveIntegerField(default=0)
    banco = models.CharField(max_length=255, default='')
    numero_cuenta = models.CharField(max_length=25, default='')
    rechazo = models.CharField(max_length=255, default='', null=True)
    tipo_cuenta = models.CharField(max_length=50, default='')
    documentsPendientes = models.ManyToManyField(
        PendienteDocuments, db_table="api_proveedor_pendiente_documentspendientes")
    foto = models.ImageField(upload_to='foto_proveedor', null=True, blank=True)

    class Meta:
        db_table = "api_proveedor_pendiente"

    def __str__(self):
        return self.email + " | " + self.nombres + " | " + self.apellidos + " | " + self.profesion + " | " + str(self.ano_experiencia)


class Solicitante(models.Model):
    user_datos = models.OneToOneField(
        Datos, on_delete=models.CASCADE, null=True)
    bool_registro_completo = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_solicitante"

    def __str__(self):
        return self.user_datos.nombres + " | " + self.user_datos.user.email


class Administrador(models.Model):
    user_datos = models.OneToOneField(
        Datos, on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_administrador"

    def __str__(self):
        return self.user_datos.nombres + " | " + self.user_datos.user.email


@receiver(post_save, sender='auth.User')
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
