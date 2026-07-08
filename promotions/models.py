from django.db import models


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
    foto = models.ImageField(upload_to='cupones', null=True, blank=True)
    tipo_categoria = models.CharField(max_length=25, null=True)

    class Meta:
        db_table = "api_cupon"

    def __str__(self):
        return self.titulo


class Cupon_Aplicado(models.Model):
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE)
    user = models.CharField(max_length=300, null=False)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_cupon_aplicado"

    def __str__(self):
        return self.cupon.codigo + " | " + str(self.user)


class Promocion(models.Model):
    codigo = models.CharField(max_length=25, null=True,  unique=True)
    cantidad = models.IntegerField(default=1)
    titulo = models.CharField(max_length=255, null=True)
    descripcion = models.CharField(max_length=255, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=False)
    porcentaje = models.IntegerField(null=False)
    participantes = models.CharField(max_length=255, null=True)
    estado = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='promociones', null=True, blank=True)
    tipo_categoria = models.CharField(max_length=25, null=True)

    class Meta:
        db_table = "api_promocion"

    def __str__(self):
        return self.titulo

    def delete(self, *args, **kwargs):
        self.foto.delete(save=False)
        super().delete(*args, **kwargs)


class PromocionCategoria(models.Model):
    promocion = models.ForeignKey(
        Promocion, on_delete=models.CASCADE, null=False)
    categoria = models.ForeignKey(
        'catalog.Categoria', on_delete=models.CASCADE, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_promocioncategoria"


class CuponCategoria(models.Model):
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, null=False)
    categoria = models.ForeignKey(
        'catalog.Categoria', on_delete=models.CASCADE, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_cuponcategoria"
