from accounts.models import Proveedor
from content.models import Cargo, Insignia, Medalla, Politicas, Publicidad, Suggestion, clientexmedalla
from api.serializers import CargoSerializer, InsigniaSerializer, MedallaSerializer, PublicidadSerializer, SuggestionSerializer


def list_politicas():
    return Politicas.objects.all().filter()


def crear_o_actualizar_politica(identifier, terminos):
    """Sin consumidor real confirmado en ningún frontend."""
    return Politicas.objects.update_or_create(identifier=identifier, defaults={'terminos': terminos})


def actualizar_politica(identifier, terminos):
    """ViveFacil_Admin2022 (`politicas.component.ts::saveChanges`) edita
    los términos y condiciones desde acá."""
    politica = Politicas.objects.get(identifier=identifier)
    politica.terminos = terminos
    politica.save()
    return politica


def list_insignias_proveedor():
    return Insignia.objects.all().filter(tipo_usuario="Proveedor")


def crear_insignia(data, files):
    insignia = Insignia.objects.create(
        nombre=data.get("nombre"), imagen=files.get("imagen"), servicio=data.get("servicio"),
        pedidos=data.get("pedidos"), descripcion=data.get("descripcion"), tipo=data.get("tipo"),
        tipo_usuario=data.get("tipoUsuario"),
    )
    return {"insignia": InsigniaSerializer(insignia).data}


def actualizar_insignia(id, data):
    insignia = Insignia.objects.get(id=id)
    serializer = InsigniaSerializer(insignia, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_insignia(id):
    Insignia.objects.get(id=id).delete()


def obtener_insignia(pk):
    return Insignia.objects.get(id=pk)


def actualizar_estado_insignia(id, estado):
    insignia = Insignia.objects.get(id=id)
    insignia.estado = estado
    insignia.save()


def list_medallas():
    return Medalla.objects.filter(estado=True)


def crear_medalla(data, files):
    medalla = Medalla.objects.create(
        nombre=data.get("nombre"), imagen=files.get("imagen"), descripcion=data.get("descripcion"),
        tiempo=int(data.get("tiempo")), valor=int(data.get("valor")), cantidad=int(data.get("cantidad")),
    )
    return {"medalla": MedallaSerializer(medalla).data}


def actualizar_medalla(id, data):
    medalla = Medalla.objects.get(id=id)
    serializer = MedallaSerializer(medalla, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_medalla(id):
    """Bug real encontrado y corregido al mover el código: el original hacía
    `Insignia.objects.get(id=id)` y borraba esa Insignia en vez de la
    Medalla pedida (copy-paste de Insignias.delete) — en el caso común
    (ningún Insignia comparte el mismo id) esto lanzaba un 500
    (`Insignia.DoesNotExist`); si por coincidencia sí existía una Insignia
    con ese id, la borraba en silencio en vez de la Medalla, corrompiendo
    datos. No es una decisión de producto ambigua (es un typo de una línea),
    así que se corrige acá."""
    Medalla.objects.get(id=id).delete()


def actualizar_estado_medalla(id):
    """Invierte el estado (toggle), tal cual el original."""
    medalla = Medalla.objects.get(id=id)
    medalla.estado = not medalla.estado
    medalla.save()


def list_cargos():
    return Cargo.objects.all().filter()


def crear_cargo(nombre, titulo, porcentaje, tipo=None):
    cargo = Cargo.objects.create(nombre=nombre, porcentaje=porcentaje, titulo=titulo, tipo=tipo or None)
    return {"cargo": CargoSerializer(cargo).data}


def actualizar_cargo(id, data):
    cargo = Cargo.objects.get(id=id)
    serializer = CargoSerializer(cargo, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_cargo(id):
    Cargo.objects.get(id=id).delete()


def obtener_cargo(pk):
    return Cargo.objects.get(id=pk)


def list_publicidades():
    return Publicidad.objects.all()


def crear_publicidad(data):
    serializer = PublicidadSerializer(data=data)
    if not serializer.is_valid():
        return serializer.errors, False
    publicidad = serializer.save()
    return PublicidadSerializer(publicidad).data, True


def actualizar_publicidad(id, data):
    """El
    `id` viene del body (`request.data.get('id')`), no de la URL, tal cual
    el original."""
    publicidad = Publicidad.objects.get(id=id)
    serializer = PublicidadSerializer(publicidad, data=data, partial=True)
    if not serializer.is_valid():
        return serializer.errors, False
    serializer.save()
    return serializer.data, True


def eliminar_publicidad(id):
    publicidad = Publicidad.objects.get(id=id)
    data = PublicidadSerializer(publicidad).data
    publicidad.delete()
    return data


def list_sugerencias():
    """Sin consumidor real confirmado en ningún frontend."""
    return Suggestion.objects.all().filter()


def list_sugerencias_leidas():
    return Suggestion.objects.all().filter(estado=True)


def list_sugerencias_no_leidas():
    return Suggestion.objects.all().filter(estado=False)


def obtener_sugerencia(pk):
    return Suggestion.objects.get(id=pk)


def actualizar_estado_sugerencia(id, estado):
    """Bug real corregido al mover el código. El original tomaba `pk` de
    la URL (`def put(self, request, pk, format=None)`), pero la única ruta
    que lo sirve en producción (`suggestion_estado/`) nunca captura ningún
    `pk` en el patrón de URL — cada llamada real (confirmado en
    `ViveFacil_Admin2022`, que manda el id por query string:
    `PUT suggestion_estado/?id=...`) lanzaba `TypeError: put() missing 1
    required positional argument: 'pk'`, un 500 garantizado. Se corrige acá
    leyendo el id de donde realmente lo manda el frontend (query param),
    igual que ya hacían `Insignia_Details.put`/`Medalla_Details.put`/
    `Notificaciones_Details.put` en el mismo archivo. Devuelve (ok: bool,
    sugerencia_o_None)."""
    if not estado:
        return False, None
    sugerencia = Suggestion.objects.get(id=id)
    sugerencia.estado = estado
    sugerencia.save()
    return True, sugerencia


def insignias_personales(id):
    """Preserva el efecto secundario original: si la
    profesión del proveedor no tiene ninguna Insignia asociada, crea una
    "Insignia de Bienvenida" de una sola vez."""
    prov = Proveedor.objects.get(user_datos_id=id)
    profesion = prov.profesion
    cant_servicios = prov.servicios

    insignias_profesion = Insignia.objects.filter(servicio=profesion)
    if not insignias_profesion.exists():
        insignia_nueva = Insignia.objects.create(
            nombre="Insignia de Bienvenida", imagen="insignias/01.png", servicio=profesion,
            pedidos=0, descripcion="Bienvenidos a Vive Facil", tipo="Oficio", tipo_usuario="Proveedor",
        )
        list_of_ids = [insignia_nueva.id]
    else:
        list_of_ids = []

    for i in insignias_profesion:
        if cant_servicios >= i.pedidos and i.estado and profesion in i.servicio:
            list_of_ids.append(i.id)

    return Insignia.objects.filter(id__in=list_of_ids)


def medallas_personales(user):
    """Preserva el efecto secundario original: otorga
    (y persiste) cada medalla que el usuario ya califica y todavía no
    tiene, sumando sus puntos a `Datos.puntos`."""
    import datetime
    from datetime import timedelta

    import pytz

    utc = pytz.UTC
    medallas_tot = Medalla.objects.all().filter()
    dato = user.datos_set.all().first()
    if not dato:
        return Medalla.objects.none()

    fecha_dato = dato.fecha_creacion
    list_of_ids = []
    for a in medallas_tot:
        nuevo_tiempo = datetime.datetime.today() - timedelta(days=a.tiempo)
        if fecha_dato < utc.localize(nuevo_tiempo) and dato.tramites >= a.cantidad and a.estado and dato.dinero_invertido >= a.valor:
            list_of_ids.append(a.id)
            medalla_tiene = clientexmedalla.objects.filter(medalla=a, user=dato.user)
            if not medalla_tiene:
                clientexmedalla.objects.create(medalla=a, user=dato.user)
                dato.puntos = dato.puntos + a.puntos
                dato.save()

    return Medalla.objects.filter(id__in=list_of_ids)


def list_insignias_solicitante():
    return Insignia.objects.all().filter(tipo_usuario="Solicitante")


def crear_sugerencia(data, files):
    """Devuelve el dict de respuesta tal cual el
    original (incluye 'sugerencia' o 'error')."""
    result = {}
    sugerencia = Suggestion.objects.create(
        descripcion=data.get('descripcion'), foto=files.get('foto'),
        usuario=data.get('usuario'), correo=data.get('correo'),
    )
    result['sugerencia'] = SuggestionSerializer(sugerencia).data
    if not sugerencia:
        result['error'] = "Error al crear!."
    return result


def buscar_publicidades(buscar):
    """Devuelve el queryset filtrado, sin paginar (la vista pagina)."""
    from django.db.models import Q

    return Publicidad.objects.all().filter(Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar))


_TERMINOS_CONDICIONES_TEXTO = 'TÉRMINOS Y CONDICIONES PARA USO DE LA APLICACIÓN “VIVEFÁCIL” Reglamento de Uso de la Aplicación Móvil El presente documento establece las condiciones mediante las cuales se regirá el uso de la aplicación móvil “VIVEFÁCIL”, la cual es operada por DIANA ALEJANDRA PEÑA HERRERA domiciliada en Ecuador, Provincia del Guayas Cantón Daule, con RUC No. 0932562812001 La aplicación funcionará como un nuevo canal para la realización de diversas actividades descritas más adelante con el objeto de facilitar el acceso a los usuarios. El usuario se compromete a leer los términos y condiciones aquí establecidos, previamente a la descarga de la aplicación, por tanto, en caso de realizar la instalación se entiende que cuenta con el conocimiento integral de este documento y la consecuente aceptación de la totalidad de sus estipulaciones. El usuario reconoce que el ingreso de su información personal, y los datos que contiene la aplicación a su disposición respecto a los productos y/o servicios activos registrados dentro de la aplicación, la realizan de manera voluntaria, quienes optan por acceder a esta aplicación en Ecuador o desde fuera del territorio nacional, lo hacen por iniciativa propia y son responsables del cumplimiento de las leyes locales, en la medida en que dichas leyes sean aplicables en su correspondiente país. En caso de que se acceda por parte de menores de edad, deben contar con la supervisión de un adulto en todo momento desde la descarga y durante el uso de la aplicación, en el evento en que no se cumpla esta condición, le agradecemos no hacer uso de la aplicación. Alcance y Uso El usuario de la aplicación entiende y acepta que la información contenida en la misma es operada por DIANA ALEJANDRA PEÑA HERRERA, la misma que será la referente a su vínculo comercial o contractual con cada usuario, por tanto, las funcionalidades ofrecidas por la aplicación serán entregadas con el objetivo vinculado a las necesidades del beneficiario. En la aplicación se pondrá a disposición del CLIENTE información y/o permitirá la realización de las transacciones determinadas o habilitadas por VIVEFÁCIL para cada producto y/o servicio en particular. VIVEFÁCIL podrá adicionar, modificar o eliminar las funcionalidades en cualquier momento, lo cual acepta el usuario mediante la instalación de la aplicación. En todo caso, al momento de realizar dichas modificaciones se notificarán al usuario a través de la misma aplicación móvil una vez inicie sesión. Los tiempos de respuesta, trámites y demás solicitudes efectuadas por el usuario mediante la aplicación serán procesadas de conformidad con las especificaciones de cada producto y/o servicio activo con VIVEFÁCIL. El usuario acepta y autoriza que los registros electrónicos de las actividades mencionadas, que realice en la aplicación constituyen plena prueba de los mismos. Requisitos para uso El usuario deberá contar con un dispositivo móvil inteligente (Smartphone) o Tableta con sistema operativo Android o IOS, cualquiera de estos con acceso a internet, ambos seguros y confiables. VIVEFÁCIL no será responsable por la seguridad de los equipos Smartphone propiedad de los usuarios utilizados para el acceso al canal, ni por la disponibilidad del servicio en los dispositivos en los cuales se descargue la aplicación. En la forma permitida por la ley, los materiales de la aplicación se suministran sin garantía de ningún género, expresa o implícita, incluyendo sin limitación las garantías de calidad satisfactoria, comerciabilidad, adecuación para un fin particular o no infracción, por tanto, VIVEFÁCIL no garantiza el funcionamiento adecuado en los distintos sistemas operativos o dispositivos en los cuales se haga uso de la aplicación. Para acceder al portal, EL CLIENTE contará con Usuario y Clave, que lo identifica en su relación con VIVEFÁCIL. Obligaciones de los usuarios El usuario se obliga a usar la aplicación y los contenidos encontrados en ella de una manera diligente, correcta, lícita y en especial, se compromete a NO realizar las conductas descritas a continuación: • Utilizar los contenidos de forma, con fines o efectos contrarios a la ley, a la moral y a las buenas costumbres generalmente aceptadas o al orden público; • Reproducir, copiar, representar, utilizar, distribuir, transformar o modificar los contenidos de la aplicación, por cualquier procedimiento o sobre cualquier soporte, total o parcial, o permitir el acceso del público a través de cualquier modalidad de comunicación pública; • Utilizar los contenidos de cualquier manera que entrañen un riesgo de daño o inutilización de la aplicación o de los contenidos o de terceros; • Suprimir, eludir o manipular el derecho de autor y demás datos identificativos de los derechos de autor incorporados a los contenidos, así como los dispositivos técnicos de protección, o cualesquiera mecanismos de información que pudieren tener los contenidos; • Emplear los contenidos y, en particular, la información de cualquier clase obtenida a través de la aplicación para distribuir, transmitir, remitir, modificar, rehusar o reportar la publicidad o los contenidos de esta con fines de venta directa o con cualquier otra clase de finalidad comercial, mensajes no solicitados dirigidos a una pluralidad de personas con independencia de su finalidad, así como comercializar o divulgar de cualquier modo dicha información; • No permitir que terceros ajenos a usted usen la aplicación móvil con su clave; • Utilizar la aplicación y los contenidos con fines lícitos y/o ilícitos, contrarios a lo establecido en estos Términos y Condiciones, o al uso mismo de la aplicación, que sean lesivos de los derechos e intereses de terceros, o que de cualquier forma puedan dañar, inutilizar, sobrecargar o deteriorar la aplicación y los contenidos o impedir la normal utilización o disfrute de esta y de los contenidos por parte de los usuarios. Condiciones de Pago y Facturación Las tarifas aplicables al Servicio serán recaudadas por VIVEFÁCIL de forma automática, a través de los datos de la tarjeta de crédito / débito facilitado por el usuario, o efectivo u otros métodos acordados con el proveedor. Tras la petición del Servicio, VIVEFÁCIL se reserva el derecho a solicitar la pre-autorización del cobro a la entidad de crédito vinculada a la tarjeta de crédito/débito que el usuario hubiera introducido en la Aplicación. Tras la petición del Servicio, VIVEFÁCIL realizará el cobro efectivo del total del Servicio que vaya a requerirse. Las tarifas cobradas podrán, previo análisis, ser reembolsables en los siguientes casos: a) VIVEFÁCIL hará por medio de acreditación bancaria al no darse el servicio en un plazo de 72 horas hábiles después de haber recibido y verificado la queja y que sea válido el reclamo; b) En caso de requerir el servicio y pago con tarjeta de crédito y se desiste al día siguiente por 4 horas antes del servicio se cobrará una penalidad del 25%, si es pasado de las 24 horas antes del servicio se reintegra el valor total del mismo descontada la tarifa bancaria; c) En caso de que el usuario no reciba el servicio por no encontrarse en el lugar indicado por casos de eventualidad o fuerza mayor y se pasó de la fecha y hora del servicio se realizará la devolución con una penalidad del 50%; d) En caso de cobros duplicados se devolverá en plazo máximo de 72 horas hábiles toda vez que se verifique la duplicidad. Las tarifas y los gastos de cancelación y compensación, así como sus actualizaciones, están disponibles en todo momento en la y están sujetas a modificaciones. Se recomienda al Usuario y al Proveedor de los servicios que acceda periódicamente a la Aplicación para conocer las tarifas aplicables en cada momento. Los valores recaudados serán acreditados a los Proveedores de los Servicios, descontando el porcentaje establecido por el uso de los botones de pago y de la plataforma en caso de que aplique. El Proveedor de los servicios entregará a los clientes, una vez cumplido el servicio, la nota de venta o factura física o electrónica correspondiente, dependiendo de si el Proveedor tiene RISE o RUC. Los recibos de las transacciones realizadas estarán a disposición de los usuarios en el respectivo correo electrónico, sin perjuicio de que puedan consultarlas a través de la Aplicación. Los cargos realizados en tarjetas de crédito o débito se realizarán en todos los casos en dólares americanos (USD) o en la moneda de curso legal dentro de la República del Ecuador. VIVEFÁCIL no es responsable frente al usuario por cargos adicionales provenientes de bancos, emisores de tarjetas de crédito/débito, impuestos o en general cualquier cargo que no esté directamente realizado por VIVEFÁCIL y que se relacione con el uso del servicio. VIVEFÁCIL en ningún momento será responsable por cargos realizados en una tarjeta de crédito o débito que no cuenten con la autorización expresa del titular de la tarjeta. Para efectos del uso de la presente aplicación, VIVEFÁCIL presume que todos los cargos son realizados únicamente por los titulares y/o tarjetahabientes autorizados. El usuario declara conocer que los pagos realizados por objeto del servicio se realizan en el Ecuador pero podrían realizarse en el extranjero, en tal virtud los pagos realizados desde el Ecuador, con tarjetas de crédito/débito emitidas por bancos locales estarán sujetas al pago de cualquier valor adicional que la legislación vigente establezca. En ningún momento VIVEFÁCIL será responsable de asumir estos costos o será responsable por los tributos que correspondan a cada usuario. Licencia para copiar para uso personal Usted podrá leer, visualizar, imprimir y descargar el material de sus productos y/o servicios. Ninguna parte de la aplicación podrá ser reproducida o transmitida o almacenada en otro sitio web o en otra forma de sistema de recuperación electrónico. Ya sea que se reconozca específicamente o no, las marcas comerciales, las marcas de servicio y los logos visualizados en esta aplicación pertenecen a DIANA ALEJANDRA PEÑA HERRERA, sus socios promocionales u otros terceros. VIVEFÁCIL no interfiere, no toma decisiones, ni garantiza las relaciones que los usuarios lleguen a sostener o las vinculaciones con terceros que pauten y/o promocionen sus productos y servicios. Estas marcas de terceros se utilizan solamente para identificar los productos y servicios de sus respectivos propietarios y el patrocinio o el aval por parte de VIVEFÁCIL no se deben inferir con el uso de estas marcas comerciales. Integración con otras aplicaciones Los links de Facebook®, Instagram®, Twitter® en esta aplicación pueden mostrar contenido que no están bajo el control de VIVEFÁCIL. Aunque esta aplicación de VIVEFÁCIL trata de suministrar links solamente a sitios y aplicaciones de terceros que cumplan con las leyes y regulaciones aplicables y las normas de VIVEFÁCIL, el usuario debe entender que VIVEFÁCIL no tiene control sobre la naturaleza y el contenido de esos sitios y no está recomendando estos sitios, la información que contienen ni los productos o servicios de terceros. VIVEFÁCIL no acepta responsabilidad por el contenido del sitio de un tercero con el cual existe un link de hipertexto y no ofrece garantía (explícita o implícita) en cuanto al contenido de la información en esos sitios, ya que no recomienda estos sitios. Usted debe verificar las secciones de términos y condiciones, política legal y de privacidad de algunos otros sitios de VIVEFÁCIL o de un tercero con los cuales se enlaza. VIVEFÁCIL no asume ninguna responsabilidad por pérdida directa, indirecta o consecuencial por el uso de un sitio de un tercero. Uso de información y privacidad Con la descarga de la APP usted acepta y autoriza que DIANA ALEJANDRA PEÑA HERRERA, utilice sus datos en calidad de responsable del tratamiento para fines derivados de la ejecución de la APP. DIANA ALEJANDRA PEÑA HERRERA informa que podrá ejercer sus derechos a conocer, actualizar, rectificar y suprimir su información personal; así como el derecho a revocar el consentimiento otorgado para el tratamiento de datos personales previstos en la Ley Orgánica De Protección De Datos Personales, siendo voluntario responder preguntas sobre información sensible o de menores de edad. DIANA ALEJANDRA PEÑA HERRERA podrá dar a conocer, transferir y/o trasmitir sus datos personales dentro y fuera del país a cualquier empresa vinculada con DIANA ALEJANDRA PEÑA HERRERA, así como a terceros a consecuencia de un contrato, ley o vínculo lícito que así lo requiera, para todo lo anterior otorgo mi autorización expresa e inequívoca. De conformidad a lo anterior autoriza el tratamiento de su información en los términos señalados, y transfiere a VIVEFÁCIL de manera total, y sin limitación mis derechos de imagen y patrimoniales de autor, de manera voluntaria, previa, explícita, informada e inequívoca. Responsabilidad de VIVEFÁCIL VIVEFÁCIL procurará garantizar disponibilidad, continuidad o buen funcionamiento de la aplicación. VIVEFÁCIL podrá bloquear, interrumpir o restringir el acceso a esta cuando lo considere necesario para el mejoramiento de la aplicación o por dada de baja de la misma. Se recomienda al usuario tomar medidas adecuadas y actuar diligentemente al momento de acceder a la aplicación, como por ejemplo, contar con programas de protección, antivirus, para manejo de malware, spyware y herramientas similares. VIVEFÁCIL no será responsable por: a) Fuerza mayor o caso fortuito; b) Por la pérdida, extravío o hurto de su dispositivo móvil que implique el acceso de terceros a la aplicación móvil; c) Por errores en la digitación o accesos por parte del cliente; d) Por los perjuicios, lucro cesante, daño emergente, morales, y en general sumas a cargo de VIVEFÁCIL, por los retrasos, no procesamiento de información o suspensión del servicio del operador móvil o daños en los dispositivos móviles. e) no será vinculada a ningún proceso legal tanto civil como penal ya que la obligación recae en quien ofrece el servicio o proveedor ya que la aplicación es solo un medio de contacto con el proveedor. Denegación y Retirada del Acceso a la Aplicación En el evento en que un usuario incumpla estos Términos y Condiciones, o cualesquiera otras disposiciones que resulten de aplicación, VIVEFÁCIL podrá suspender su acceso a la aplicación. Términos y Condiciones El usuario acepta expresamente los Términos y Condiciones, siendo condición esencial para la utilización de la aplicación. En el evento en que se encuentre en desacuerdo con estos Términos y Condiciones, solicitamos abandonar la aplicación inmediatamente. VIVEFÁCIL podrá modificar los presentes términos y condiciones, avisando a los usuarios de la aplicación mediante la difusión de las modificaciones por algún medio electrónico, redes sociales, SMS y/o correo electrónico, lo cual se entenderá aceptado por el usuario si éste continua con el uso de la aplicación. Jurisdicción Estos términos y condiciones y todo lo que tenga que ver con esta aplicación, se rigen por las leyes ecuatorianas. Uso de información no personal VIVEFÁCIL también recolecta información no personal en forma agregada para seguimiento de datos como el número total de descargas de la aplicación. Utilizamos esta información, que permanece en forma agregada, para entender el comportamiento de la aplicación. Uso de Direcciones IP Una dirección de Protocolo de Internet (IP) es un conjunto de números que se asigna automáticamente a su o dispositivo móvil cuando usted accede a su proveedor de servicios de internet, o a través de la red de área local (LAN) de su organización o la red de área amplia (WAN). Los servidores web automáticamente identifican su dispositivo móvil por la dirección IP asignada a él durante su sesión en línea. VIVEFÁCIL podrá recolectar direcciones IP para propósitos de administración de sistemas y para auditar el uso de nuestro sitio, todo lo anterior de acuerdo con la autorización de protección de datos que se suscribe para tal efecto. Normalmente no vinculamos la dirección IP de un usuario con la información personal de ese usuario, lo que significa que cada sesión de usuario se registra, pero el usuario sigue siendo anónimo para nosotros. Sin embargo, podemos usar las direcciones IP para identificar a los usuarios de nuestro sitio cuando sea necesario con el objeto de exigir el cumplimiento de los términos de uso del sitio, o para proteger nuestro servicio, sitio u otros usuarios. Seguridad VIVEFÁCIL está comprometido en la protección de la seguridad de su información personal. VIVEFÁCIL tiene implementados mecanismos de seguridad que aseguran la protección de la información personal, así como los accesos únicamente al personal y sistemas autorizados, también contra la pérdida, uso indebido y alteración de sus datos de usuario bajo nuestro control. Excepto como se indica a continuación, sólo personal autorizado tiene acceso a la información que nos proporciona. Además, hemos impuesto reglas estrictas a los colaboradores de VIVEFÁCIL con acceso a las bases de datos que almacenan información del usuario o a los servidores que hospedan nuestros servicios'


def terminos_condiciones_texto():
    """Texto plano
    estatico, no depende de la base de datos."""
    return _TERMINOS_CONDICIONES_TEXTO
