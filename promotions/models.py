from django.db import models

from core.campos import URLCompletaImageField


class Cupon(models.Model):
    codigo = models.CharField(max_length=25, null=True,  unique=True)
    titulo = models.CharField(max_length=255, null=True)
    cantidad = models.IntegerField(default=1)
    descripcion = models.CharField(max_length=255, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null=False)
    fecha_expiracion = models.DateTimeField(null=False)
    porcentaje = models.IntegerField(null=False)
    participantes = models.CharField(max_length=255, null=True)
    puntos = models.IntegerField(null=False)
    estado = models.BooleanField(default=True)
    foto = URLCompletaImageField(upload_to='cupones', null=True, blank=True)
    tipo_categoria = models.CharField(max_length=25, null=True)

    class Meta:
        db_table = "api_cupon"

    def __str__(self):
        return self.titulo


class Cupon_Aplicado(models.Model):
    """Canje de un cupón por parte de un usuario.

    Ojo con `estado`, que es el punto que más confunde: True = canjeado y
    todavía disponible para usar en un pago; False = ya se usó (lo consume
    pagos/services/pago_controller.py al aprobarse el pago). No es un
    "activo/inactivo" administrativo.
    """

    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE)
    # username del solicitante (que en este sistema es su correo), no un FK.
    user = models.CharField(max_length=300, null=False)
    estado = models.BooleanField(default=True)
    # Nulas en los canjes anteriores a estos campos.
    fecha_canje = models.DateTimeField(auto_now_add=True, null=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_cupon_aplicado"
        ordering = ["-id"]

    def __str__(self):
        return self.cupon.codigo + " | " + str(self.user)


class CuponCategoria(models.Model):
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, null=False)
    categoria = models.ForeignKey(
        'catalog.Categoria', on_delete=models.CASCADE, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_cuponcategoria"
