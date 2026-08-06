from django.db import models

from core.campos import URLCompletaFileField, URLCompletaImageField


class Categoria(models.Model):
    # Pin explícito: la columna real es INT(11), no BigAutoField. Mientras
    # nada apuntara una FK nueva hacia acá daba igual, pero promotions.Cupon sí
    # lo hace y MySQL rechaza una FK BIGINT contra un PK INT (errno 3780).
    # Mismo patrón que catalog/migrations/0003_profesion_pk_int.py.
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField()
    foto = URLCompletaImageField(upload_to='categoria')
    foto2 = URLCompletaImageField(upload_to='categoria2')
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
    foto = URLCompletaImageField(upload_to='servicio', null=True)

    class Meta:
        db_table = "api_servicio"

    def __str__(self):
        return self.nombre + " | " + self.descripcion + " | " + self.categoria.nombre


class Profesion(models.Model):
    # PK legacy: la columna es INT en la BD, pero catalog/apps.py fuerza
    # BigAutoField. Sin este pin, cualquier FK nueva hacia acá (p.ej. la M2M de
    # notifications) se crea BIGINT y MySQL la rechaza con errno 3780. Mismo
    # arreglo que Datos en accounts/models.py.
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)
    estado = models.BooleanField(default=True)
    servicio = models.ManyToManyField(Servicio, db_table="api_profesion_servicio")
    foto = URLCompletaImageField(upload_to='profesion', null=True)
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
    documento = URLCompletaFileField(upload_to='solicitudes', null=True)

    class Meta:
        db_table = "api_solicitudprofesion"

    def __str__(self):
        return self.proveedor.user_datos.nombres + "|" + self.profesion + "|" + self.anio_experiencia
