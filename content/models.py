from django.db import models


class Insignia(models.Model):
    nombre = models.CharField(max_length=25)
    imagen = models.ImageField(upload_to='insignias', blank=True)
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


class Medalla(models.Model):
    nombre = models.CharField(max_length=25)
    descripcion = models.CharField(max_length=255, null=True)
    imagen = models.ImageField(upload_to='insignias', blank=True)
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
    imagen = models.ImageField(upload_to='publicidad', null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "api_publicidad"

    def __str__(self):
        return self.titulo | self.descripcion


class Suggestion(models.Model):
    descripcion = models.TextField()
    foto = models.ImageField(upload_to='suggestion')
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


class Cargo(models.Model):
    nombre = models.CharField(max_length=200)
    porcentaje = models.FloatField(default=0.0)
    titulo = models.CharField(max_length=200, default=" ")

    class Meta:
        db_table = "api_cargo"

    def __str__(self):
        return self.nombre + "|" + self.porcentaje


class clientexmedalla(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    medalla = models.ForeignKey('content.Medalla', on_delete=models.CASCADE, null=True)
    tipoUsuario = models.BooleanField(default=True)

    class Meta:
        db_table = "api_clientexmedalla"
