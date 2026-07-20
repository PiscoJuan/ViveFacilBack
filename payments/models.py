from django.db import models

from core.campos import URLCompletaImageField


class Plan(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255)
    imagen = URLCompletaImageField(upload_to='planes', null=True, blank=True)
    duracion = models.IntegerField(default=0)
    precio = models.FloatField(null=False)
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_plan"

    def __str__(self):
        return self.nombre + " | " + self.descripcion


class PlanProveedor(models.Model):
    proveedor = models.ForeignKey(
        'accounts.Proveedor', on_delete=models.CASCADE, null=True)
    planProveedor = models.ForeignKey(
        Plan, on_delete=models.CASCADE, null=True)
    fecha_inicio = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=False)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_planproveedor"


class Tipo_Cuenta(models.Model):  # debito credito
    nombre = models.CharField(max_length=255)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_tipo_cuenta"

    def __str__(self):
        return self.nombre


class Banco(models.Model):
    nombre = models.CharField(max_length=255)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_banco"

    def __str__(self):
        return self.nombre


class Cuenta(models.Model):
    proveedor = models.ForeignKey(
        'accounts.Proveedor', on_delete=models.CASCADE, null=True)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, null=True)
    tipo_cuenta = models.ForeignKey(
        Tipo_Cuenta, on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)
    numero_cuenta = models.CharField(max_length=25, default="0999999999")

    class Meta:
        db_table = "api_cuenta"

    def __str__(self):
        return self.proveedor.user_datos.nombres + " | " + self.banco.nombre + " | " + self.tipo_cuenta.nombre + " | " + self.numero_cuenta


class Tarjeta(models.Model):
    solicitante = models.ForeignKey(
        'accounts.Solicitante', on_delete=models.CASCADE, null=False)
    tipo = models.CharField(max_length=400, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    cvv = models.CharField(max_length=100, null=False)
    estado = models.BooleanField(default=True)
    titular = models.CharField(max_length=400, null=False)
    fecha_vencimiento = models.DateTimeField(auto_now_add=False, null=False)
    numero = models.BigIntegerField(null=False)
    brand = models.CharField(max_length=200, null=True)
    code = models.CharField(max_length=20, null=True)
    token = models.CharField(max_length=400, null=True)

    class Meta:
        db_table = "api_tarjeta"

    def __str__(self):
        return self.solicitante.user_datos.nombres + "|" + str(self.fecha_vencimiento) + "|" + self.titular


class PagoTarjeta(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE, null=True)
    promocion = models.ForeignKey(
        'promotions.Promocion', on_delete=models.CASCADE, null=True, blank=True)
    cupon = models.ForeignKey(
        'promotions.Cupon', on_delete=models.CASCADE, null=True, blank=True)
    valor = models.FloatField(default=0.0)
    descripcion = models.CharField(max_length=255, null=True)
    impuesto = models.IntegerField(null=False)
    referencia = models.CharField(max_length=255, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    carrier_id = models.CharField(max_length=255, null=True)
    concepto = models.CharField(max_length=255, null=True, default="Solicitud")
    carrier_code = models.CharField(max_length=255, null=True)
    estado = models.BooleanField(default=True)
    pago_proveedor = models.BooleanField(default=False)
    cargo_paymentez = models.FloatField(default=0.0)
    cargo_banco = models.FloatField(default=0.0)
    cargo_sistema = models.FloatField(default=0.0)
    proveedor = models.CharField(max_length=255, default="")
    prov_correo = models.CharField(max_length=255, default="")
    prov_telefono = models.CharField(max_length=15, default="0999999999")
    servicio = models.CharField(max_length=255, default="")
    usuario = models.CharField(max_length=255, default="")
    solicitud = models.ForeignKey(
        'solicitudes.Solicitud', on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "api_pagotarjeta"


class PagoEfectivo(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    promocion = models.ForeignKey(
        'promotions.Promocion', on_delete=models.CASCADE, null=True,  blank=True)
    cupon = models.ForeignKey(
        'promotions.Cupon', on_delete=models.CASCADE, null=True,  blank=True)
    valor = models.FloatField(default=0.0)
    oferta = models.FloatField(default=0.0)
    descripcion = models.CharField(max_length=255, null=True)
    concepto = models.CharField(max_length=255, null=True, default="Solicitud")
    referencia = models.CharField(max_length=255, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)
    proveedor = models.CharField(max_length=255, default="")
    servicio = models.CharField(max_length=255, default="")
    usuario = models.CharField(max_length=255, default="")
    prov_correo = models.CharField(max_length=255, default="")
    prov_telefono = models.CharField(max_length=15, default="0999999999")
    user_telefono = models.CharField(max_length=15, default="0999999999")
    solicitud = models.ForeignKey(
        'solicitudes.Solicitud', on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "api_pagoefectivo"


class PagoSolicitud(models.Model):
    pago_tarjeta = models.ForeignKey(
        PagoTarjeta, on_delete=models.CASCADE, null=True, blank=True)
    pago_efectivo = models.ForeignKey(
        PagoEfectivo, on_delete=models.CASCADE, null=True, blank=True)
    solicitud = models.ForeignKey(
        'solicitudes.Solicitud', on_delete=models.CASCADE, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "api_pagosolicitud"
