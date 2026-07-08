from django.db import models


class Notificacion(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    nombre = models.CharField(max_length=255, null=True)
    titulo = models.CharField(max_length=255, null=True)
    descripcion = models.TextField()
    tipo_proveedores = models.CharField(max_length=100, null=True)
    frecuencia = models.CharField(max_length=100, null=True)
    ruta = models.CharField(max_length=100, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=True)
    hora = models.TimeField(null=True)
    estado = models.BooleanField(default=True)
    imagen = models.ImageField(
        upload_to='notificaciones', null=True, blank=True)

    class Meta:
        db_table = "api_notificacion"

    def __str__(self):
        return str(self.titulo) + " | " + str(self.descripcion) + " | " + str(self.ruta)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        super().delete(*args, **kwargs)


class NotificacionMasiva(models.Model):
    nombre = models.CharField(max_length=255, null=True)
    titulo = models.CharField(max_length=255, null=True)
    descripcion = models.TextField()
    tipo_proveedores = models.CharField(max_length=100, null=True)
    frecuencia = models.CharField(max_length=100, null=True)
    ruta = models.CharField(max_length=100, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=True)
    hora = models.TimeField(null=True)
    estado = models.BooleanField(default=True)
    imagen = models.ImageField(
        upload_to='notificaciones-masivas', null=True, blank=True)

    class Meta:
        db_table = "api_notificacionmasiva"

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        super().delete(*args, **kwargs)
