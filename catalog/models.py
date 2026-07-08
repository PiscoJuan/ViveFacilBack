from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField()
    foto = models.ImageField(upload_to='categoria')
    foto2 = models.ImageField(upload_to='categoria2')
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_categoria"

    def __str__(self):
        return self.nombre + " | " + self.descripcion


class Servicio(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    foto = models.ImageField(upload_to='servicio', null=True)

    class Meta:
        db_table = "api_servicio"

    def __str__(self):
        return self.nombre + " | " + self.descripcion + " | " + self.categoria.nombre


class Profesion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    estado = models.BooleanField(default=True)
    servicio = models.ManyToManyField(Servicio, db_table="api_profesion_servicio")
    foto = models.ImageField(upload_to='profesion', null=True)
    descripcion = models.CharField(max_length=255, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "api_profesion"

    def __str__(self):
        return self.nombre


class Profesion_Proveedor(models.Model):
    proveedor = models.ForeignKey(
        'accounts.Proveedor', on_delete=models.CASCADE, null=True, blank=True)
    profesion = models.ForeignKey(
        Profesion, on_delete=models.CASCADE, null=True)
    ano_experiencia = models.PositiveIntegerField(default=0)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_profesion_proveedor"

    def __str__(self):
        return self.profesion.nombre + " | " + str(self.ano_experiencia) + " | " + self.proveedor.user_datos.nombres + "  " + self.proveedor.user_datos.apellidos


class Ciudad_Disponible(models.Model):
    ciudad = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "api_ciudad_disponible"

    def __str__(self):
        return self.ciudad


class Ciudad(models.Model):
    nombre = models.CharField(max_length=200)

    class Meta:
        db_table = "api_ciudad"


class SolicitudProfesion(models.Model):
    proveedor = models.ForeignKey(
        'accounts.Proveedor', on_delete=models.CASCADE, null=True)
    profesion = models.CharField(max_length=150)
    anio_experiencia = models.PositiveIntegerField(default=0)
    fecha_solicitud = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True)
    documento = models.FileField(upload_to='solicitudes', null=True)

    class Meta:
        db_table = "api_solicitudprofesion"

    def __str__(self):
        return self.proveedor.user_datos.nombres + "|" + self.profesion + "|" + self.anio_experiencia
