from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.timezone import now

from core.campos import URLCompletaImageField


class Insignia(models.Model):
    # PK legacy es INT en la BD; el app_config global usa BigAutoField, así que
    # lo declaramos explícito para que las FK nuevas hacia Insignia salgan INT y
    # no bigint (si no, MySQL rechaza la FK por tipos incompatibles).
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    imagen = URLCompletaImageField(upload_to='insignias', blank=True)
    tipo_usuario = models.CharField(max_length=25, default=" ")
    servicio = models.CharField(max_length=25)
    tipo = models.CharField(max_length=50, null=True)
    estado = models.BooleanField(default=True)
    pedidos = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    descripcion = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "api_insignia"

    def __str__(self):
        return self.nombre


class InsigniaObtenida(models.Model):
    """Cuándo obtuvo el usuario la insignia.

    Qué insignias le tocan se sigue calculando en
    `content.services.insignias_personales*` (proveedor: `servicios` vs
    `pedidos`); esta tabla solo guarda la fecha, que antes no existía y obligaba
    a mostrar `Insignia.fecha_creacion` (la del catálogo) como si fuera la de
    obtención. Va por `Datos` y no por `Proveedor` para servir a las dos apps.
    """
    # AutoField explícito: las tablas legacy tienen PK int(11) y el app_config
    # global usa BigAutoField, así la FK sale int y MySQL no la rechaza.
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        'accounts.Datos', on_delete=models.CASCADE, related_name='insignias_obtenidas')
    insignia = models.ForeignKey('content.Insignia', on_delete=models.CASCADE)
    # No es auto_now_add: al registrarla se backfillea la fecha real en que se
    # cruzó el umbral, que suele ser anterior a la fila.
    fecha_obtencion = models.DateTimeField(default=now)

    class Meta:
        db_table = "api_insignia_obtenida"
        unique_together = ('usuario', 'insignia')

    def __str__(self):
        return str(self.usuario) + " | " + str(self.insignia)


class Medalla(models.Model):
    nombre = models.CharField(max_length=25)
    descripcion = models.CharField(max_length=255, null=True)
    imagen = URLCompletaImageField(upload_to='insignias', blank=True)
    estado = models.BooleanField(default=True)
    tiempo = models.PositiveIntegerField(default=0)
    valor = models.PositiveIntegerField(default=0)
    cantidad = models.PositiveIntegerField(default=0)
    puntos = models.PositiveIntegerField(default=10)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_medalla"

    def __str__(self):
        return self.nombre


class Publicidad(models.Model):
    titulo = models.CharField(max_length=255, null=True)
    descripcion = models.CharField(max_length=255, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_inicio = models.DateTimeField(null=False)
    fecha_expiracion = models.DateTimeField(null=False)
    imagen = URLCompletaImageField(upload_to='publicidad', null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "api_publicidad"

    def __str__(self):
        return self.titulo | self.descripcion


class Suggestion(models.Model):
    descripcion = models.TextField()
    foto = URLCompletaImageField(upload_to='suggestion')
    usuario = models.CharField(max_length=255, default="")
    correo = models.CharField(max_length=255, default="")
    estado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_suggestion"

    def __str__(self):
        return self.descripcion


class Politicas(models.Model):
    identifier = models.TextField()
    terminos = models.TextField()

    class Meta:
        db_table = "api_politicas"

    def __str__(self):
        return self.terminos


POLITICAS_CACHE_KEY = "politicas_list"


@receiver([post_save, post_delete], sender=Politicas)
def invalidar_cache_politicas(sender, **kwargs):
    cache.delete(POLITICAS_CACHE_KEY)


class TipoCargo(models.TextChoices):
    BANCO = "banco", "Banco"
    PAYMENTEZ = "paymentez", "Paymentez"
    SISTEMA = "sistema", "Sistema"


class Cargo(models.Model):
    nombre = models.CharField(max_length=200)
    porcentaje = models.FloatField(default=0.0)
    titulo = models.CharField(max_length=200, default=" ")
    # Solo puede haber un cargo activo por tipo: es lo que se descuenta del
    # pago al proveedor (ver pagos.services.pago_controller). Nulo = cargo
    # legacy sin tipo asignado, no participa en el cálculo.
    tipo = models.CharField(
        max_length=20, choices=TipoCargo.choices, unique=True, null=True, blank=True)

    class Meta:
        db_table = "api_cargo"

    def __str__(self):
        return self.nombre + "|" + str(self.porcentaje)


class clientexmedalla(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    medalla = models.ForeignKey('content.Medalla', on_delete=models.CASCADE, null=True)
    tipoUsuario = models.BooleanField(default=True)
    # La fila se crea en el momento en que se gana la medalla, así que de acá en
    # adelante la fecha es real. Las filas anteriores a este campo quedan NULL:
    # la medalla depende de tres umbrales a la vez (tiempo, cantidad, valor) y
    # no hay forma honesta de reconstruir cuándo se cumplieron los tres.
    fecha_obtencion = models.DateTimeField(default=now, null=True, blank=True)

    class Meta:
        db_table = "api_clientexmedalla"
