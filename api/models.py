from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.postgres.fields import ArrayField

#clase para paymentez
class Cardauth(models.Model):
    id_cardauth = models.AutoField(primary_key=True)
    token = models.CharField(max_length=20)
    auth = models.CharField(max_length=3)


# clase insignia
class Insignia(models.Model):
    nombre = models.CharField(max_length=25)
    imagen = models.ImageField(upload_to='insignias',blank=True)
    tipo_usuario = models.CharField(max_length= 25, default=" ")
    servicio = models.CharField(max_length=25)
    tipo = models.CharField(max_length=50,null=True)
    estado = models.BooleanField(default=True)
    pedidos = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    descripcion = models.CharField(max_length=255,null =True)
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField()
    foto = models.ImageField(upload_to='categoria')
    foto2 = models.ImageField(upload_to='categoria2')
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    def __str__(self):
        return self.nombre + " | " + self.descripcion

class Servicio(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion =models.CharField(max_length=255)
    categoria = models.ForeignKey(Categoria,on_delete= models.PROTECT, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    foto = models.ImageField(upload_to='servicio',null=True)
    def __str__(self):
        return self.nombre + " | " + self.descripcion + " | " + self.categoria.nombre



class Profesion(models.Model):
    nombre = models.CharField(max_length=255,unique=True)
    estado = models.BooleanField(default=True)
    servicio = models.ManyToManyField(Servicio, null=False)
    foto = models.ImageField(upload_to='profesion',null=True)
    estado = models.BooleanField(default=True)
    descripcion = models.CharField(max_length=255, null = True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    def __str__(self):
        return self.nombre

class Cupon(models.Model):
    codigo = models.CharField(max_length=25, null =True,  unique=True)
    titulo = models.CharField(max_length=255, null =True)
    cantidad = models.IntegerField(default = 1)
    descripcion = models.CharField(max_length=255, null = True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null= False)
    fecha_expiracion = models.DateTimeField(null=False)
    porcentaje = models.IntegerField(null=False)
    puntos= models.IntegerField(null=False)
    estado = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='cupones', null=True,blank=True)
    tipo_categoria = models.CharField(max_length=25, null =True)
    def __str__(self):
        return self.titulo

class Publicidad(models.Model):

    titulo = models.CharField(max_length=255, null =True)
    descripcion = models.CharField(max_length=255, null = True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_inicio = models.DateTimeField(null=False)
    fecha_expiracion = models.DateTimeField(null=False)
    imagen = models.ImageField(upload_to='publicidad', null=True,blank=True)
    url = models.CharField(max_length=255, null =True,blank=True)

    def __str__(self):
        return self.titulo | self.descripcion

class Document(models.Model):
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    documento = models.FileField(upload_to='documents', null=True)
    estado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return str(self.descripcion)

    def delete(self, *args, **kwargs):
        self.documento.delete()
        super().delete(*args, **kwargs)

class Datos(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    tipo = models.ForeignKey('auth.group', on_delete= models.PROTECT, null=True)
    nombres = models.CharField(max_length=255, null =True)
    apellidos = models.CharField(max_length=255, null = True)
    ciudad = models.CharField(max_length=20, null=True)
    cedula=models.CharField(max_length=20, null=True, default="0999999999")
    telefono = models.CharField(max_length=15)
    genero = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='foto_perfil', null=True, blank=True)
    estado = models.BooleanField(default=True)
    security_access = models.UUIDField(primary_key=False, editable=False, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    puntos = models.PositiveIntegerField(default=0, null=True)
    codigo_invitacion = models.CharField(max_length=12, default="", null=True)
    def __str__(self):
        return str(self.nombres) + " | " + str(self.apellidos) + " | " + self.genero

class Plan(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='planes', null=True, blank=True)
    duracion = models.IntegerField(default =0)
    precio = models.FloatField(null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre + " | " + self.descripcion

class Codigos(models.Model): #codigos que se envian para reestablecer contrasena
    user_datos = models.ForeignKey(Datos, on_delete=models.CASCADE, null=True)
    codigo = models.CharField(max_length=255, null =True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)



class Proveedor(models.Model):
    user_datos = models.OneToOneField(Datos, on_delete=models.CASCADE, null=True)
    rating= models.FloatField(default=4.0)
    servicios=models.PositiveIntegerField(default=0)
    descripcion = models.CharField(max_length=255)
    document = models.ManyToManyField(Document, null=False)
    estado = models.BooleanField(default=True)
    profesion = models.CharField(max_length=400, default='')

    copiaCedula = models.FileField(upload_to='documentos-Proveedor', null=True,blank = True)
    direccion = models.CharField(max_length=300, default ='')
    licencia = models.CharField(max_length=55, default='')
    copiaLicencia = models.FileField(upload_to='documentos-Proveedor', null=True,blank = True)

    ano_profesion =  models.CharField(max_length=400, default='')
    banco = models.CharField(max_length=255,default='')
    numero_cuenta = models.CharField(max_length=25, default='')
    tipo_cuenta = models.CharField(max_length=50,default='')
    # planilla_servicios = models.FileField(upload_to='documents', null=True)

    def __str__(self):
        return self.user_datos.nombres +  " " + self.user_datos.apellidos +  " | " + self.profesion

class Profesion_Proveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE,null=True,blank = True)
    profesion = models.ForeignKey(Profesion, on_delete=models.CASCADE,null=True)
    ano_experiencia = models.PositiveIntegerField(default=0)
    estado = models.BooleanField(default=True)

    # self.proveedor.user_datos.nombres  +  " " +self.proveedor.user_datos.apellidos
    def __str__(self):
        return self.profesion.nombre + " | " + str(self.ano_experiencia) + " | " + self.proveedor.user_datos.nombres + "  " + self.proveedor.user_datos.apellidos


class PlanProveedor(models.Model):

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True)
    planProveedor = models.ForeignKey(Plan, on_delete=models.CASCADE, null=True)
    fecha_inicio = models.DateTimeField(null=True)
    fecha_expiracion = models.DateTimeField(null=False)
    estado = models.BooleanField(default=True)

class PendienteDocuments(models.Model):

    document = models.FileField(upload_to='pendientes-documents',null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.document.delete()
        super().delete(*args, **kwargs)


class Proveedor_Pendiente(models.Model): #tabla que guarda la info de las personas que quieren ser proveedores.
    # proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True)
    nombres= models.CharField(max_length=255,default='')
    apellidos= models.CharField(max_length=255, default='')
    ciudad=models.CharField(max_length=255, default ='')
    direccion = models.CharField(max_length=300, default ='')
    genero = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=255, default='')
    copiaCedula=models.FileField(upload_to='pendientes-copias',null=True)
    telefono=models.CharField(max_length=255, default='')
    descripcion = models.TextField()
    cedula=models.CharField(max_length=255, default='')
    estado = models.BooleanField(default=False)
    profesion = models.CharField(max_length=255, default='')
    licencia = models.CharField(max_length=55, default='')
    copiaLicencia = models.FileField(upload_to='pendientes-copias', null=True)
    ano_experiencia = models.PositiveIntegerField(default=0)
    banco= models.CharField(max_length=255,default='')
    numero_cuenta= models.CharField(max_length=25, default='')
    tipo_cuenta=models.CharField(max_length=50,default='')
    documentsPendientes = models.ManyToManyField(PendienteDocuments, null=False)
    foto = models.ImageField(upload_to='foto_proveedor', null=True, blank=True)

    def __str__(self):
        return self.email + " | " + self.nombres + " | "  + self.apellidos + " | " + self.profesion + " | " + str(self.ano_experiencia)


class Tipo_Cuenta(models.Model): #debito credito
    nombre = models.CharField(max_length = 255)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Ciudad_Disponible(models.Model):
    ciudad: models.CharField(max_length=255)
    def __str__(self):
        return self.ciudad

class Banco(models.Model):
    nombre = models.CharField(max_length = 255)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Cuenta(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE,null=True)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE,null=True)
    tipo_cuenta = models.ForeignKey(Tipo_Cuenta, on_delete=models.CASCADE,null=True)
    estado = models.BooleanField(default=True)
    numero_cuenta = models.CharField(max_length= 25, default="0999999999")
    def __str__(self):
        return self.proveedor.user_datos.nombres + " | " + self.banco.nombre + " | " + self.tipo_cuenta.nombre + " | "+ self.numero_cuenta



class Solicitante(models.Model):
    user_datos = models.OneToOneField(Datos, on_delete=models.CASCADE, null=True)
    bool_registro_completo=models.BooleanField(default=False)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.user_datos.nombres + " | " +self.user_datos.user.email

class Administrador(models.Model):
    user_datos = models.OneToOneField(Datos, on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.user_datos.nombres + " | " +self.user_datos.user.email

class Tipo_Pago(models.Model):
    nombre = models.CharField(max_length=100, null =True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return str(self.nombre)

class Ubicacion(models.Model):
    latitud= models.DecimalField(null =False,max_digits=30, decimal_places=15)
    altitud= models.DecimalField(null =False,max_digits=30, decimal_places=15)
    direccion=models.CharField(max_length=300, null =True)
    referencia = models.CharField(max_length=300, null =True, blank=True)
    foto_ubicacion = models.ImageField(upload_to='foto_solicitud/foto_ubicacion', null=True, blank=True)

    def __str__(self):
        return str(self.latitud) + " | " + str(self.altitud)

class Solicitud(models.Model):
    solicitante = models.ForeignKey(Solicitante, on_delete=models.CASCADE)
    ubicacion= models.OneToOneField(Ubicacion, on_delete=models.CASCADE)
    tipo_pago = models.ForeignKey(Tipo_Pago, on_delete=models.CASCADE)
    servicio= models.ForeignKey(Servicio, on_delete=models.CASCADE)
    proveedor= models.ForeignKey(Proveedor,on_delete= models.PROTECT, null=True, blank=True)
    descripcion = models.CharField(max_length=500)
    foto_descripcion = models.ImageField(upload_to='foto_solicitud/foto_descripcion', null=True, blank=True)
    fecha_expiracion = models.CharField(max_length=200)
    adjudicar = models.BooleanField(default=False)
    pagada = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)
    termino= models.CharField(max_length=50, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    descripcion_rating= models.CharField(max_length=100, default=" ",null=True, blank=True)
    rating = models.FloatField(default=4.0)
    def __str__(self):
        return self.solicitante.user_datos.user.email + " | " + str(self.descripcion)


class Envio_Interesados(models.Model): #proveedores que estan interesados en la solicitud, guarda la oferta.
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True)
    solicitud = models.ForeignKey(Solicitud, on_delete= models.PROTECT, null=True)
    interesado= models.BooleanField(default=False)
    oferta=models.DecimalField(null =True,blank=True,max_digits=30, decimal_places=15)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.proveedor.user_datos.nombres + " | " + str(self.oferta)

class Tarjeta(models.Model):
    solicitante = models.ForeignKey(Solicitante, on_delete=models.CASCADE, null=False)
    tipo = models.CharField(max_length=400, default= "")
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    cvv= models.CharField(max_length=100, null=False)
    estado= models.BooleanField(default=True)
    titular = models.CharField(max_length=400, null=False)
    fecha_vencimiento = models.DateTimeField(auto_now_add=False, null=False)
    numero = models.BigIntegerField(null=False)
    brand = models.CharField(max_length=200, null=True)
    code = models.CharField(max_length=20, null=True)
    token = models.CharField(max_length=400, null=True)

    def __str__(self):
        return self.solicitante.user_datos.nombres + "|" + str(self.fecha_vencimiento) + "|" + self.titular

class Cupon_Aplicado(models.Model):
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE)
    user = models.CharField(max_length=300, null=False)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.cupon.codigo + " | " + str(self.user)

class Notificacion(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    titulo = models.CharField(max_length=255, null =True)
    descripcion = models.CharField(max_length=255, null = True)
    ruta = models.CharField(max_length=100, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    imagen = models.ImageField(upload_to='notificaciones', null=True,blank=True)

    def __str__(self):
        return str(self.titulo) + " | " + str(self.descripcion)+ " | " + str(self.ruta)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        super().delete(*args, **kwargs)

class NotificacionMasiva(models.Model):

    titulo = models.CharField(max_length=255, null =True)
    mensaje = models.CharField(max_length=255, null = True)
    descripcion = models.TextField()
    ruta = models.CharField(max_length=100, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    imagen = models.ImageField(upload_to='notificaciones-masivas', null=True,blank=True)

    def delete(self, *args, **kwargs):
        self.imagen.delete(save=False)
        super().delete(*args, **kwargs)


class Promocion(models.Model):
    codigo = models.CharField(max_length=25, null =True,  unique=True)
    cantidad = models.IntegerField(default = 1)
    titulo = models.CharField(max_length=255, null =True)
    descripcion = models.CharField(max_length=255, null = True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_iniciacion = models.DateTimeField(null= True)
    fecha_expiracion = models.DateTimeField(null=False)
    porcentaje = models.IntegerField(null=False)
    participantes = models.CharField(max_length=255, null = True)
    estado = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='promociones', null=True,blank=True)
    tipo_categoria = models.CharField(max_length=25, null =True)
    def __str__(self):
        return self.titulo
    def delete(self, *args, **kwargs):
        self.foto.delete(save=False)
        super().delete(*args, **kwargs)

class PromocionCategoria(models.Model):
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, null=False)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)



class CuponCategoria(models.Model):
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, null=False)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)


class PagoTarjeta(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE, null=True)
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, null=True, blank=True)
    valor = models.FloatField(default=0.0)
    descripcion = models.CharField(max_length=255, null = True)
    impuesto = models.IntegerField(null=False)
    referencia = models.CharField(max_length=255, null = True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    carrier_id =models.CharField(max_length=255, null = True)
    concepto = models.CharField(max_length=255, null=True, default="Solicitud")
    carrier_code = models.CharField(max_length=255, null = True)
    estado = models.BooleanField(default=True)
    pago_proveedor = models.BooleanField(default=False)
    cargo_paymentez = models.FloatField(default=0.0)
    cargo_banco = models.FloatField(default=0.0)
    cargo_sistema = models.FloatField(default=0.0)
    proveedor = models.CharField(max_length=255, default="")
    prov_correo = models.CharField(max_length=255, default="")
    prov_telefono = models.CharField(max_length=15,default="0999999999")
    servicio = models.CharField(max_length=255, default="")
    usuario = models.CharField(max_length=255, default="")


class PagoEfectivo(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, null=True,  blank=True)
    valor = models.FloatField(default=0.0)
    descripcion = models.CharField(max_length=255, null = True)
    concepto = models.CharField(max_length=255, null=True, default="Solicitud")
    referencia = models.CharField(max_length=255, null = True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)
    proveedor = models.CharField(max_length=255, default="")
    servicio = models.CharField(max_length=255, default="")
    usuario = models.CharField(max_length=255, default="")
    prov_correo = models.CharField(max_length=255, default="")
    prov_telefono = models.CharField(max_length=15,default="0999999999")
    user_telefono = models.CharField(max_length=15,default="0999999999")


class PagoSolicitud(models.Model):
    pago_tarjeta= models.ForeignKey(PagoTarjeta, on_delete= models.CASCADE, null=True, blank=True)
    pago_efectivo= models.ForeignKey(PagoEfectivo, on_delete= models.CASCADE, null=True, blank=True)
    solicitud = models.ForeignKey(Solicitud, on_delete= models.CASCADE, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=True)


class Suggestion(models.Model):
    descripcion = models.TextField()
    foto = models.ImageField(upload_to='suggestion')
    usuario = models.CharField(max_length=255, default="")
    correo =  models.CharField(max_length=255, default="")
    estado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    def __str__(self):
        return self.descripcion

class Politicas(models.Model):
    identifier=models.TextField()
    terminos = models.TextField()
    def __str__(self):
        return self.terminos


@receiver(post_save, sender='auth.User')
def create_auth_token(sender, instance= None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Ciudad(models.Model):
    nombre = models.CharField(max_length=200)


class Cargo(models.Model):

    nombre = models.CharField(max_length=200)
    porcentaje = models.FloatField(default=0.0)
    titulo = models.CharField(max_length=200,default = " ")

    def __str__(self):
         return self.nombre + "|" +  self.porcentaje


class SolicitudProfesion(models.Model):

    proveedor = models.ForeignKey(Proveedor, on_delete= models.CASCADE, null=True)
    profesion = models.CharField(max_length=150)
    anio_experiencia = models.PositiveIntegerField(default=0)
    fecha_solicitud = models.DateTimeField(auto_now_add=True, null=True)
    estado = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True)
    documento = models.FileField(upload_to='solicitudes', null=True)

    def __str__(self):
        return self.proveedor.user_datos.nombres + "|" + self.profesion + "|" + self.anio_experiencia






