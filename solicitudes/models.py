from django.db import models
from django.utils.timezone import now

from core.campos import URLCompletaImageField


class Tipo_Pago(models.Model):
    nombre = models.CharField(max_length=100, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_tipo_pago"

    def __str__(self):
        return str(self.nombre)


class Ubicacion(models.Model):
    latitud = models.DecimalField(null=False, max_digits=30, decimal_places=15)
    altitud = models.DecimalField(null=False, max_digits=30, decimal_places=15)
    direccion = models.CharField(max_length=300, null=True)
    referencia = models.CharField(max_length=300, null=True, blank=True)
    foto_ubicacion = URLCompletaImageField(
        upload_to='foto_solicitud/foto_ubicacion', null=True, blank=True)

    class Meta:
        db_table = "api_ubicacion"

    def __str__(self):
        return str(self.latitud) + " | " + str(self.altitud)


class Termino_solcitud(models.TextChoices):
    FINALIZADO = 'finalizado', 'finalizado'
    CANCELADO = 'cancelado', 'cancelado'
    PAGADO = 'pagado', 'pagado'


class Solicitud(models.Model):
    solicitante = models.ForeignKey('accounts.Solicitante', on_delete=models.CASCADE)
    ubicacion = models.OneToOneField(Ubicacion, on_delete=models.CASCADE)
    tipo_pago = models.ForeignKey(Tipo_Pago, on_delete=models.CASCADE)
    servicio = models.ForeignKey('catalog.Servicio', on_delete=models.CASCADE)
    proveedor = models.ForeignKey(
        'accounts.Proveedor', on_delete=models.PROTECT, null=True, blank=True)
    descripcion = models.CharField(max_length=500)
    foto_descripcion = URLCompletaImageField(
        upload_to='foto_solicitud/foto_descripcion', null=True, blank=True)
    fecha_expiracion = models.DateTimeField(max_length=200, default=now)
    adjudicar = models.BooleanField(default=False)
    pagada = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)
    descuento = models.FloatField(default=0.0)
    termino = models.CharField(max_length=50, null=True, blank=True, choices=Termino_solcitud.choices, default=None)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    descripcion_rating = models.CharField(
        max_length=100, default=" ", null=True, blank=True)
    rating = models.FloatField(default=0)
    # Reseña inversa: el proveedor califica al cliente (solicitante).
    descripcion_rating_solicitante = models.CharField(
        max_length=100, default=" ", null=True, blank=True)
    rating_solicitante = models.FloatField(default=0)

    class Meta:
        db_table = "api_solicitud"

    def __str__(self):
        return self.solicitante.user_datos.user.email + " | " + str(self.descripcion)


class Envio_Interesados(models.Model):
    proveedor = models.ForeignKey(
        'accounts.Proveedor', on_delete=models.CASCADE, null=True)
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.PROTECT, null=True)
    interesado = models.BooleanField(default=False)
    oferta = models.DecimalField(
        null=True, blank=True, max_digits=30, decimal_places=15)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_envio_interesados"

    def __str__(self):
        return self.proveedor.user_datos.nombres + " | " + str(self.oferta)
