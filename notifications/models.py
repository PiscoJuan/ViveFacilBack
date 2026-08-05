from django.db import models

from core.campos import URLCompletaImageField

# A qué app va dirigida la notificación. El filtro de profesiones solo tiene
# sentido con DIRIGIDA_PROVEEDOR (un solicitante no tiene profesión).
DIRIGIDA_SOLICITANTE = 'solicitante'
DIRIGIDA_PROVEEDOR = 'proveedor'
DIRIGIDA_AMBAS = 'ambas'
DIRIGIDA_CHOICES = [
    (DIRIGIDA_SOLICITANTE, 'Solo solicitantes'),
    (DIRIGIDA_PROVEEDOR, 'Solo proveedores'),
    (DIRIGIDA_AMBAS, 'Ambas apps'),
]

# Solo para las programadas. Las masivas siempre son de un único envío.
FRECUENCIA_UNICA = 'unica'
FRECUENCIA_DIARIA = 'diaria'
FRECUENCIA_SEMANAL = 'semanal'
FRECUENCIA_CHOICES = [
    (FRECUENCIA_UNICA, 'Una sola vez'),
    (FRECUENCIA_DIARIA, 'Todos los días'),
    (FRECUENCIA_SEMANAL, 'Días específicos de la semana'),
]


class Notificacion(models.Model):
    """Notificación programada: solo push, nunca aparece en la lista in-app.

    Puede ser de un único envío o recurrente (diaria o en días concretos de la
    semana). La dispara `manage.py enviar_notificaciones_programadas`.
    """

    # PK legacy INT, ver catalog/migrations/0003 y accounts/models.py.
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    nombre = models.CharField(max_length=255, null=True)
    titulo = models.CharField(max_length=255, null=True)
    descripcion = models.TextField()
    # Deprecado: lo reemplazan `dirigida_a` + `profesiones`. Se conserva porque
    # borrar una columna en producción es puerta de una sola dirección.
    tipo_proveedores = models.CharField(max_length=100, null=True)
    frecuencia = models.CharField(max_length=100, null=True, choices=FRECUENCIA_CHOICES)
    ruta = models.CharField(max_length=100, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    # Ventana de vigencia de la recurrencia: fuera de ella el job no dispara.
    fecha_iniciacion = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=True)
    hora = models.TimeField(null=True)
    estado = models.BooleanField(default=True)
    imagen = URLCompletaImageField(
        upload_to='notificaciones', null=True, blank=True)

    dirigida_a = models.CharField(
        max_length=20, choices=DIRIGIDA_CHOICES, default=DIRIGIDA_AMBAS)
    profesiones = models.ManyToManyField(
        'catalog.Profesion', blank=True,
        related_name='notificaciones_programadas',
        db_table='api_notificacion_profesion')
    # CSV de date.weekday(): '0'=Lunes ... '6'=Domingo. Solo se lee cuando
    # frecuencia == FRECUENCIA_SEMANAL.
    dias_semana = models.CharField(max_length=20, default='', blank=True)
    veces_enviada = models.PositiveIntegerField(default=0)
    ultimo_envio = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_notificacion"

    def __str__(self):
        return str(self.titulo) + " | " + str(self.descripcion) + " | " + str(self.ruta)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        super().delete(*args, **kwargs)


class NotificacionMasiva(models.Model):
    """Notificación masiva: un único envío, por push y además visible en la
    lista de notificaciones de las apps.

    `programada_para` nulo significa "enviar al crear". Con valor, la recoge el
    job en la marca de media hora correspondiente.
    """

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, null=True)
    titulo = models.CharField(max_length=255, null=True)
    descripcion = models.TextField()
    # Deprecados: `tipo_proveedores` lo reemplazan `dirigida_a` + `profesiones`;
    # `frecuencia`, `fecha_iniciacion`, `fecha_expiracion` y `hora` los reemplaza
    # `programada_para` (una masiva se envía una sola vez y no expira).
    tipo_proveedores = models.CharField(max_length=100, null=True)
    frecuencia = models.CharField(max_length=100, null=True)
    ruta = models.CharField(max_length=100, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=True)
    hora = models.TimeField(null=True)
    estado = models.BooleanField(default=True)
    imagen = URLCompletaImageField(
        upload_to='notificaciones-masivas', null=True, blank=True)

    dirigida_a = models.CharField(
        max_length=20, choices=DIRIGIDA_CHOICES, default=DIRIGIDA_AMBAS)
    profesiones = models.ManyToManyField(
        'catalog.Profesion', blank=True,
        related_name='notificaciones_masivas',
        db_table='api_notificacionmasiva_profesion')
    programada_para = models.DateTimeField(null=True, blank=True)
    # Doble función: marca anti-duplicado para el job, y criterio de visibilidad
    # en la campanita (nula = todavía no salió, no se muestra a nadie).
    enviada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_notificacionmasiva"

    def __str__(self):
        return str(self.titulo) + " | " + str(self.dirigida_a)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        super().delete(*args, **kwargs)
