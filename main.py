# -*- coding: utf-8 -*-
"""
Sistema Integral de Gestion de Clientes, Servicios y Reservas - Software FJ
Curso: Programacion 213023 - UNAD
Fase 4 - Componente practico - Practicas simuladas

El sistema trabaja solo con objetos y listas (sin base de datos).
El unico archivo que se usa es el log, donde quedan los eventos y errores.
"""

# =====================================================================
# PARTE 1 - Importaciones, archivo de logs y excepciones personalizadas
# =====================================================================

from abc import ABC, abstractmethod          # ABC y abstractmethod sirven para crear clases abstractas
from datetime import datetime                # datetime se usa para la fecha de creacion de cada entidad
from functools import singledispatchmethod   # permite "sobrecargar" un metodo segun el tipo del argumento
import logging                               # modulo estandar de Python para escribir el archivo de logs
import re                                    # expresiones regulares para validar nombre, correo y telefono

ARCHIVO_LOG = "software_fj.log"              # nombre del archivo donde se registran eventos y errores

logger = logging.getLogger("SoftwareFJ")     # se crea un logger propio del sistema
logger.setLevel(logging.INFO)                # se guardan mensajes de nivel INFO, WARNING, ERROR y CRITICAL
logger.propagate = False                     # evita que los mensajes tambien salgan repetidos por consola
if not logger.handlers:                      # solo se agrega el manejador una vez (por si se ejecuta varias veces)
    manejador = logging.FileHandler(ARCHIVO_LOG, mode="a", encoding="utf-8")   # el log se escribe en un archivo, agregando al final
    formato = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",   # formato: fecha | nivel | mensaje
                                "%Y-%m-%d %H:%M:%S")                             # formato de la fecha y hora
    manejador.setFormatter(formato)          # se le asigna el formato al manejador
    logger.addHandler(manejador)             # se conecta el archivo al logger


class SoftwareFJError(Exception):   # clase base de los errores del sistema, hereda de Exception
    """Excepcion base del sistema, todas las demas heredan de esta."""
    codigo = "FJ-000"                        # codigo interno para identificar el tipo de error en el log

    def __init__(self, mensaje):             # constructor que recibe el mensaje del error
        super().__init__(mensaje)            # se le pasa el mensaje a la clase Exception

    def __str__(self):                       # define como se muestra el error cuando se imprime
        return f"[{self.codigo}] {self.args[0]}"   # ejemplo: [FJ-110] El nombre no es valido


class DatoInvalidoError(SoftwareFJError):    # datos con formato o valor incorrecto
    codigo = "FJ-100"                        # codigo general de datos invalidos


class ParametroFaltanteError(SoftwareFJError):   # cuando no llega un dato obligatorio
    codigo = "FJ-101"                        # codigo para parametros faltantes


class ClienteInvalidoError(DatoInvalidoError):   # datos del cliente que no pasan la validacion
    codigo = "FJ-110"                        # codigo para errores de clientes


class ServicioInvalidoError(DatoInvalidoError):  # parametros malos al crear o usar un servicio
    codigo = "FJ-120"                        # codigo para errores de servicios


class ServicioNoDisponibleError(SoftwareFJError):    # el servicio existe pero no se puede usar
    codigo = "FJ-200"                        # codigo para servicios no disponibles


class ReservaInvalidaError(SoftwareFJError):     # intentos de reserva incorrectos
    codigo = "FJ-300"                        # codigo para errores de reservas


class OperacionNoPermitidaError(SoftwareFJError):    # acciones que no se permiten en el estado actual
    codigo = "FJ-400"                        # codigo para operaciones no permitidas


class CalculoInconsistenteError(SoftwareFJError):    # resultados de costos que no tienen sentido
    codigo = "FJ-500"                        # codigo para calculos inconsistentes


# =====================================================================
# PARTE 2 - Clase abstracta Entidad y clase Cliente
# =====================================================================

class Entidad(ABC):   # clase abstracta, hereda de ABC y no se puede instanciar
    """Clase abstracta que representa cualquier entidad del sistema (cliente, servicio, reserva)."""
    _contadores = {}                         # diccionario compartido con un contador por cada prefijo (CLI, SRV, RES)

    def __init__(self, prefijo):             # el prefijo indica el tipo de entidad
        Entidad._contadores[prefijo] = Entidad._contadores.get(prefijo, 0) + 1   # aumenta el contador de ese prefijo
        self._id = f"{prefijo}-{Entidad._contadores[prefijo]:03d}"           # genera un id unico, ej: CLI-001
        self._fecha_creacion = datetime.now()    # guarda la fecha y hora en que se creo

    @property   # decorador: el metodo se usa como atributo (getter)
    def id(self):                            # propiedad de solo lectura para el id
        return self._id                      # devuelve el id (no tiene setter, no se puede cambiar)

    @property   # decorador: el metodo se usa como atributo (getter)
    def fecha_creacion(self):                # propiedad de solo lectura para la fecha
        return self._fecha_creacion          # devuelve la fecha de creacion

    @abstractmethod   # decorador: las clases hijas deben implementar este metodo
    def describir(self):                     # cada hija debe decir como se describe
        """Devuelve un texto que describe la entidad."""

    @abstractmethod   # decorador: las clases hijas deben implementar este metodo
    def validar(self):                       # cada hija debe decir como se valida
        """Comprueba que la entidad este en un estado correcto."""

    def __str__(self):                       # al imprimir cualquier entidad se usa su descripcion
        return self.describir()              # reutiliza el metodo polimorfico describir()


class Cliente(Entidad):   # Cliente hereda de Entidad (herencia)
    """Cliente de Software FJ con sus datos personales encapsulados y validados."""
    PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{3,60}$")    # solo letras y espacios, de 3 a 60 caracteres
    PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")          # formato basico de correo usuario@dominio.algo
    PATRON_TELEFONO = re.compile(r"^\d{7,10}$")                        # telefono de 7 a 10 digitos

    # constructor, los datos llegan opcionales para poder detectar si falta alguno
    def __init__(self, nombre=None, documento=None, correo=None, telefono=None):
        datos_obligatorios = {"nombre": nombre, "documento": documento, "correo": correo}   # campos que no pueden faltar
        for campo, valor in datos_obligatorios.items():                # se revisa cada campo obligatorio
            if valor is None or str(valor).strip() == "":              # si viene vacio o no viene
                raise ParametroFaltanteError(f"Falta el dato obligatorio '{campo}' del cliente")   # se lanza el error
        self.nombre = nombre                 # se asigna por el setter, que valida el nombre
        self.documento = documento           # se asigna por el setter, que valida el documento
        self.correo = correo                 # se asigna por el setter, que valida el correo
        self.telefono = telefono             # se asigna por el setter, el telefono es opcional
        super().__init__("CLI")              # solo si todo es valido se genera el id del cliente

    @property   # decorador: el metodo se usa como atributo (getter)
    def nombre(self):                        # getter del nombre
        return self.__nombre                 # atributo privado (encapsulado con doble guion bajo)

    @nombre.setter   # decorador: define el setter con validacion
    def nombre(self, valor):                 # setter del nombre con validacion
        if not isinstance(valor, str):       # el nombre debe ser texto
            # se lanza la excepcion ClienteInvalidoError
            raise ClienteInvalidoError(f"El nombre debe ser texto, se recibio {type(valor).__name__}")
        valor = " ".join(valor.split())      # quita espacios repetidos o al inicio y al final
        if not self.PATRON_NOMBRE.match(valor):  # revisa que solo tenga letras y espacios
            # se lanza la excepcion ClienteInvalidoError
            raise ClienteInvalidoError(f"El nombre '{valor}' no es valido (solo letras, minimo 3)")
        self.__nombre = valor.title()        # se guarda con mayuscula inicial en cada palabra

    @property   # decorador: el metodo se usa como atributo (getter)
    def documento(self):                     # getter del documento
        return self.__documento              # devuelve el documento completo (uso interno)

    @documento.setter   # decorador: define el setter con validacion
    def documento(self, valor):              # setter del documento con validacion
        valor = str(valor).strip()           # se acepta numero o texto y se pasa a texto
        if not valor.isdigit() or not 6 <= len(valor) <= 10:   # solo digitos y entre 6 y 10 caracteres
            # se lanza la excepcion ClienteInvalidoError
            raise ClienteInvalidoError(f"El documento '{valor}' debe tener entre 6 y 10 digitos")
        self.__documento = valor             # se guarda el documento validado

    @property   # decorador: el metodo se usa como atributo (getter)
    def documento_oculto(self):              # version protegida del documento para mostrar en pantalla
        return "*" * (len(self.__documento) - 4) + self.__documento[-4:]   # solo deja ver los ultimos 4 digitos

    @property   # decorador: el metodo se usa como atributo (getter)
    def correo(self):                        # getter del correo
        return self.__correo                 # devuelve el correo

    @correo.setter   # decorador: define el setter con validacion
    def correo(self, valor):                 # setter del correo con validacion
        valor = str(valor).strip().lower()   # se pasa a minusculas y sin espacios
        if not self.PATRON_CORREO.match(valor):  # revisa el formato del correo
            # se lanza la excepcion ClienteInvalidoError
            raise ClienteInvalidoError(f"El correo '{valor}' no tiene un formato valido")
        self.__correo = valor                # se guarda el correo validado

    @property   # decorador: el metodo se usa como atributo (getter)
    def telefono(self):                      # getter del telefono
        return self.__telefono               # puede ser None si no se dio telefono

    @telefono.setter   # decorador: define el setter con validacion
    def telefono(self, valor):               # setter del telefono (opcional)
        if valor is None:                    # si no se envio telefono
            self.__telefono = None           # se deja vacio y no hay error
            return                           # se sale del metodo
        valor = str(valor).strip()           # se convierte a texto
        if not self.PATRON_TELEFONO.match(valor):    # debe tener de 7 a 10 digitos
            # se lanza la excepcion ClienteInvalidoError
            raise ClienteInvalidoError(f"El telefono '{valor}' debe tener entre 7 y 10 digitos")
        self.__telefono = valor              # se guarda el telefono validado

    def describir(self):                     # implementacion del metodo abstracto
        # devuelve el texto armado
        return f"Cliente {self.id}: {self.nombre} | doc {self.documento_oculto} | {self.correo}"

    def validar(self):                       # implementacion del metodo abstracto
        return all([self.nombre, self.documento, self.correo])   # True si los datos obligatorios existen


# =====================================================================
# PARTE 3 - Clase abstracta Servicio y los tres servicios especializados
# =====================================================================

class Servicio(Entidad):   # Servicio tambien hereda de Entidad y sigue siendo abstracta
    """Clase abstracta para los servicios que ofrece Software FJ."""
    IVA = 0.19                               # impuesto por defecto (19 %)

    def __init__(self, nombre, tarifa_base, disponible=True):   # constructor comun de todos los servicios
        if nombre is None or str(nombre).strip() == "":     # el nombre del servicio es obligatorio
            # se lanza la excepcion ParametroFaltanteError
            raise ParametroFaltanteError("Falta el nombre del servicio")
        if isinstance(tarifa_base, bool) or not isinstance(tarifa_base, (int, float)):   # la tarifa debe ser numero
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"La tarifa debe ser numerica, se recibio '{tarifa_base}'")
        if tarifa_base <= 0:                 # la tarifa debe ser positiva
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"La tarifa {tarifa_base} debe ser mayor que cero")
        self._nombre = str(nombre).strip()   # se guarda el nombre limpio
        self._tarifa_base = float(tarifa_base)   # se guarda la tarifa como decimal
        self._disponible = bool(disponible)  # indica si el servicio se puede reservar
        super().__init__("SRV")              # se genera el id del servicio, ej: SRV-001

    @property   # decorador: el metodo se usa como atributo (getter)
    def nombre(self):                        # getter del nombre del servicio
        return self._nombre   # devuelve el valor del atributo protegido

    @property   # decorador: el metodo se usa como atributo (getter)
    def tarifa_base(self):                   # getter de la tarifa base
        return self._tarifa_base   # devuelve el valor del atributo protegido

    @property   # decorador: el metodo se usa como atributo (getter)
    def disponible(self):                    # getter de la disponibilidad
        return self._disponible   # devuelve el valor del atributo protegido

    @disponible.setter   # decorador: define el setter con validacion
    def disponible(self, valor):             # setter para activar o desactivar el servicio
        if not isinstance(valor, bool):      # solo se acepta True o False
            # se lanza la excepcion DatoInvalidoError
            raise DatoInvalidoError("La disponibilidad debe ser True o False")
        self._disponible = valor             # se actualiza el estado
        logger.info(f"Servicio {self.id} ahora {'disponible' if valor else 'NO disponible'}")   # se registra el cambio

    def verificar_disponibilidad(self):      # revisa si el servicio se puede usar
        if not self._disponible:             # si esta desactivado
            # se lanza la excepcion ServicioNoDisponibleError
            raise ServicioNoDisponibleError(f"El servicio '{self.nombre}' no esta disponible en este momento")

    @abstractmethod   # decorador: las clases hijas deben implementar este metodo
    def validar_parametros(self, duracion):  # cada servicio valida la duracion a su manera
        """Lanza ServicioInvalidoError si la duracion no sirve para este servicio."""

    @abstractmethod   # decorador: las clases hijas deben implementar este metodo
    def calcular_costo_base(self, duracion):     # cada servicio calcula su costo a su manera (polimorfismo)
        """Costo sin impuestos ni descuentos."""

    # metodo con parametros opcionales (simula la sobrecarga)
    def calcular_costo(self, duracion, impuesto=None, descuento=0.0):
        """
        Metodo "sobrecargado" con parametros opcionales. Se puede llamar asi:
          calcular_costo(duracion)                    -> costo base
          calcular_costo(duracion, True)              -> costo con IVA del 19 %
          calcular_costo(duracion, 0.05)              -> costo con un impuesto distinto
          calcular_costo(duracion, True, 0.10)        -> con IVA y 10 % de descuento
        """
        self.validar_parametros(duracion)    # primero se valida la duracion (puede lanzar excepcion)
        costo = self.calcular_costo_base(duracion)   # se calcula el costo propio de cada servicio
        # el descuento debe ser un numero entre 0 y 0.99 (no puede ser texto ni True/False)
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)) or not 0 <= descuento < 1:
            raise CalculoInconsistenteError(f"El descuento {descuento} debe estar entre 0 y 0.99")   # descuento imposible
        costo = costo * (1 - descuento)      # se aplica el descuento
        if impuesto is True:                 # si se pide impuesto sin decir cuanto
            impuesto = self.IVA              # se usa el IVA por defecto
        if impuesto not in (None, False):    # si se pidio algun impuesto
            # el impuesto debe ser un numero entre 0 y 1
            if isinstance(impuesto, bool) or not isinstance(impuesto, (int, float)) or not 0 <= impuesto <= 1:
                raise CalculoInconsistenteError(f"El impuesto {impuesto} no es valido")   # impuesto fuera de rango
            costo = costo * (1 + impuesto)   # se suma el impuesto
        costo = round(costo, 2)              # se redondea a 2 decimales
        if costo <= 0:                       # un costo en cero o negativo no tiene sentido
            # se lanza la excepcion CalculoInconsistenteError
            raise CalculoInconsistenteError(f"El costo calculado ({costo}) no es valido")
        return costo                         # se devuelve el costo final

    def validar(self):                       # implementacion del metodo abstracto de Entidad
        return self._tarifa_base > 0         # un servicio es valido si su tarifa es positiva

    @staticmethod   # decorador: metodo que no necesita self
    def _validar_numero(valor, minimo, maximo, unidad):   # ayuda comun para validar duraciones
        if valor is None:                    # si no se envio la duracion
            # se lanza la excepcion ParametroFaltanteError
            raise ParametroFaltanteError(f"Falta la duracion en {unidad}")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):   # debe ser numero
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"La duracion debe ser numerica, se recibio '{valor}'")
        if not minimo <= valor <= maximo:    # debe estar dentro del rango permitido
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"La duracion {valor} {unidad} esta fuera del rango ({minimo} a {maximo})")


class ReservaSala(Servicio):   # primer servicio especializado, hereda de Servicio
    """Reserva de salas de reuniones, se cobra por hora."""

    # constructor de la sala, agrega la capacidad
    def __init__(self, nombre, tarifa_hora, capacidad, disponible=True):
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:   # capacidad entera positiva
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"La capacidad '{capacidad}' debe ser un entero mayor que cero")
        self.capacidad = capacidad           # numero de personas que caben en la sala
        super().__init__(nombre, tarifa_hora, disponible)   # el resto lo valida la clase padre

    def validar_parametros(self, duracion):  # una sala se reserva de 1 a 12 horas
        self._validar_numero(duracion, 1, 12, "horas")   # rango permitido: de 1 a 12 horas

    def calcular_costo_base(self, duracion): # costo = tarifa por hora * horas
        recargo = 1.10 if self.capacidad > 20 else 1.0     # las salas grandes tienen 10 % de recargo
        return self.tarifa_base * duracion * recargo   # costo base de la sala

    def describir(self):                     # descripcion propia de la sala (metodo sobrescrito)
        # texto segun la disponibilidad del servicio
        estado = "disponible" if self.disponible else "NO disponible"
        # devuelve el texto armado
        return f"Sala {self.id}: {self.nombre} ({self.capacidad} personas) ${self.tarifa_base:,.0f}/hora - {estado}"


class AlquilerEquipo(Servicio):   # segundo servicio especializado, hereda de Servicio
    """Alquiler de equipos (portatiles, videobeam, etc.), se cobra por dia y por unidad."""

    # constructor del alquiler, agrega tipo y unidades
    def __init__(self, nombre, tarifa_dia, tipo_equipo, unidades=1, disponible=True):
        if not tipo_equipo or not str(tipo_equipo).strip():     # el tipo de equipo es obligatorio
            # se lanza la excepcion ParametroFaltanteError
            raise ParametroFaltanteError("Falta el tipo de equipo")
        if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades <= 0:   # unidades enteras positivas
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"Las unidades '{unidades}' deben ser un entero mayor que cero")
        self.tipo_equipo = str(tipo_equipo).strip()   # ej: portatil, videobeam
        self.unidades = unidades             # cantidad de equipos que se alquilan
        super().__init__(nombre, tarifa_dia, disponible)   # el resto lo valida el constructor de Servicio

    def validar_parametros(self, duracion):  # un equipo se alquila de 1 a 30 dias, en dias completos
        self._validar_numero(duracion, 1, 30, "dias")   # rango permitido: de 1 a 30 dias
        if duracion != int(duracion):        # no se permiten dias con decimales
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"El alquiler es por dias completos, se recibio {duracion}")

    def calcular_costo_base(self, duracion): # costo = tarifa por dia * dias * unidades
        return self.tarifa_base * duracion * self.unidades   # costo base del alquiler

    def describir(self):                     # descripcion propia del alquiler (metodo sobrescrito)
        # texto segun la disponibilidad del servicio
        estado = "disponible" if self.disponible else "NO disponible"
        # devuelve el texto armado
        return (f"Equipo {self.id}: {self.nombre} ({self.unidades} x {self.tipo_equipo}) "
                f"${self.tarifa_base:,.0f}/dia - {estado}")


class Asesoria(Servicio):   # tercer servicio especializado, hereda de Servicio
    """Asesorias especializadas, se cobra por hora segun el nivel del asesor."""
    NIVELES = {"basico": 1.0, "intermedio": 1.25, "experto": 1.5}   # multiplicador de la tarifa segun el nivel

    # constructor de la asesoria, agrega especialidad y nivel
    def __init__(self, nombre, tarifa_hora, especialidad, nivel="basico", disponible=True):
        if not especialidad or not str(especialidad).strip():   # la especialidad es obligatoria
            # se lanza la excepcion ParametroFaltanteError
            raise ParametroFaltanteError("Falta la especialidad de la asesoria")
        if nivel not in self.NIVELES:        # el nivel debe ser uno de los permitidos
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError(f"El nivel '{nivel}' no existe, use: {', '.join(self.NIVELES)}")
        self.especialidad = str(especialidad).strip()   # se guarda la especialidad sin espacios sobrantes
        self.nivel = nivel   # se guarda el nivel ya validado
        super().__init__(nombre, tarifa_hora, disponible)   # el resto lo valida el constructor de Servicio

    def validar_parametros(self, duracion):  # una asesoria dura de media hora a 8 horas
        self._validar_numero(duracion, 0.5, 8, "horas")   # rango permitido: de 0.5 a 8 horas

    def calcular_costo_base(self, duracion): # costo = tarifa * horas * multiplicador del nivel
        return self.tarifa_base * duracion * self.NIVELES[self.nivel]   # costo base de la asesoria

    def describir(self):                     # descripcion propia de la asesoria (metodo sobrescrito)
        # texto segun la disponibilidad del servicio
        estado = "disponible" if self.disponible else "NO disponible"
        # devuelve el texto armado
        return (f"Asesoria {self.id}: {self.nombre} - {self.especialidad} (nivel {self.nivel}) "
                f"${self.tarifa_base:,.0f}/hora - {estado}")


# =====================================================================
# PARTE 4 - Clase Reserva y gestor del sistema
# =====================================================================

class Reserva(Entidad):   # Reserva hereda de Entidad y une cliente + servicio
    """Une un cliente, un servicio y una duracion, y maneja su estado."""
    ESTADOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA", "PROCESADA")   # estados posibles de una reserva

    def __init__(self, cliente, servicio, duracion):   # constructor de la reserva
        if cliente is None or servicio is None or duracion is None:   # los tres datos son obligatorios
            # se lanza la excepcion ParametroFaltanteError
            raise ParametroFaltanteError("La reserva necesita cliente, servicio y duracion")
        if not isinstance(cliente, Cliente):     # el cliente debe ser un objeto Cliente
            # se lanza la excepcion ReservaInvalidaError
            raise ReservaInvalidaError(f"'{cliente}' no es un cliente registrado")
        if not isinstance(servicio, Servicio):   # el servicio debe ser un objeto Servicio
            # se lanza la excepcion ReservaInvalidaError
            raise ReservaInvalidaError(f"'{servicio}' no es un servicio valido")
        try:   # bloque que puede generar errores
            servicio.validar_parametros(duracion)    # se valida la duracion segun el tipo de servicio
        except (ServicioInvalidoError, ParametroFaltanteError) as error:   # si la duracion no sirve
            raise ReservaInvalidaError(                              # se lanza un error de reserva...
                f"Duracion no valida para '{servicio.nombre}'") from error   # ...encadenado con la causa original
        self._cliente = cliente              # cliente de la reserva
        self._servicio = servicio            # servicio reservado
        self._duracion = duracion            # horas o dias segun el servicio
        self._estado = "PENDIENTE"           # toda reserva nace pendiente
        self._costo = None                   # el costo se calcula al confirmar
        super().__init__("RES")              # id de la reserva, ej: RES-001
        # se registra el evento en el log
        logger.info(f"Reserva {self.id} creada para {cliente.id} en {servicio.id} ({duracion})")

    @property   # decorador: el metodo se usa como atributo (getter)
    def estado(self):                        # estado actual (solo lectura desde afuera)
        return self._estado   # devuelve el valor del atributo protegido

    @property   # decorador: el metodo se usa como atributo (getter)
    def costo(self):                         # costo final (solo lectura)
        return self._costo   # devuelve el valor del atributo protegido

    def confirmar(self, impuesto=True, descuento=0.0):   # confirma la reserva, por defecto con IVA y sin descuento
        """Confirma la reserva y calcula el costo. Usa try / except / else."""
        if self._estado != "PENDIENTE":      # solo se confirman reservas pendientes
            # se lanza la excepcion OperacionNoPermitidaError
            raise OperacionNoPermitidaError(f"No se puede confirmar {self.id} porque esta {self._estado}")
        try:   # bloque que puede generar errores
            self._servicio.verificar_disponibilidad()    # puede lanzar ServicioNoDisponibleError
            costo = self._servicio.calcular_costo(self._duracion, impuesto, descuento)   # puede lanzar CalculoInconsistenteError
        except (ServicioNoDisponibleError, CalculoInconsistenteError) as error:   # si algo fallo
            logger.warning(f"Fallo la confirmacion de {self.id}: {error}")       # se deja registro
            raise ReservaInvalidaError(f"No se pudo confirmar la reserva {self.id}") from error   # encadenamiento
        else:                                # solo entra aqui si no hubo ningun error
            self._costo = costo              # se guarda el costo calculado
            self._estado = "CONFIRMADA"      # se cambia el estado
            logger.info(f"Reserva {self.id} confirmada por ${costo:,.2f}")   # se registra el evento en el log
            return costo                     # se devuelve el costo

    def cancelar(self, motivo="sin motivo"):   # cancela la reserva, el motivo es opcional
        """Cancela la reserva si todavia no se ha procesado."""
        if self._estado in ("CANCELADA", "PROCESADA"):   # no se puede cancelar algo ya cerrado
            # se lanza la excepcion OperacionNoPermitidaError
            raise OperacionNoPermitidaError(f"La reserva {self.id} ya esta {self._estado}, no se puede cancelar")
        self._estado = "CANCELADA"           # se cambia el estado
        logger.info(f"Reserva {self.id} cancelada. Motivo: {motivo}")   # se registra el evento en el log
        return f"Reserva {self.id} cancelada ({motivo})"   # devuelve el texto armado

    def procesar(self, pago):   # procesa el pago de la reserva
        """Registra el pago de una reserva confirmada. Usa try / except / finally."""
        if self._estado != "CONFIRMADA":     # solo se procesan reservas confirmadas
            # se lanza la excepcion OperacionNoPermitidaError
            raise OperacionNoPermitidaError(f"La reserva {self.id} esta {self._estado}, primero debe confirmarse")
        try:   # bloque que puede generar errores
            pago = float(pago)               # se intenta convertir el pago a numero
        except (TypeError, ValueError) as error:     # si el pago no es un numero
            raise DatoInvalidoError(f"El pago '{pago}' no es un valor numerico") from error   # encadenamiento
        finally:                             # se ejecuta siempre, haya error o no
            logger.info(f"Intento de pago registrado para {self.id}")   # se registra el evento en el log
        if pago < self._costo:               # si el pago no alcanza
            # se lanza la excepcion CalculoInconsistenteError
            raise CalculoInconsistenteError(f"Pago insuficiente: se pago ${pago:,.2f} y el costo es ${self._costo:,.2f}")
        self._estado = "PROCESADA"           # la reserva queda pagada
        cambio = round(pago - self._costo, 2)    # se calcula el cambio
        logger.info(f"Reserva {self.id} procesada. Cambio: ${cambio:,.2f}")   # se registra el evento en el log
        return f"Reserva {self.id} pagada, cambio ${cambio:,.2f}"   # devuelve el texto armado

    def describir(self):                     # implementacion del metodo abstracto
        # texto del costo o aviso si aun no se calcula
        costo = f"${self._costo:,.2f}" if self._costo else "sin calcular"
        # devuelve el texto armado
        return (f"Reserva {self.id}: {self._cliente.nombre} -> {self._servicio.nombre} "
                f"({self._duracion}) | {self._estado} | costo {costo}")

    def validar(self):                       # implementacion del metodo abstracto
        return self._estado in self.ESTADOS  # la reserva es valida si su estado es uno de los permitidos


class SistemaSoftwareFJ:   # clase que administra todo el sistema
    """Gestor principal: guarda clientes, servicios y reservas en listas (sin base de datos)."""

    def __init__(self):   # constructor del sistema, arranca con las listas vacias
        self.clientes = []                   # lista de objetos Cliente
        self.servicios = []                  # lista de objetos Servicio
        self.reservas = []                   # lista de objetos Reserva
        self.operaciones = 0                 # total de operaciones ejecutadas
        self.exitosas = 0                    # operaciones que terminaron bien
        self.fallidas = 0                    # operaciones que tuvieron error controlado
        logger.info("===== Sistema Software FJ iniciado =====")   # se registra el evento en el log

    def registrar_cliente(self, **datos):    # recibe los datos con nombre (nombre=..., correo=...)
        cliente = Cliente(**datos)           # crear el cliente ya valida los datos
        if any(c.documento == cliente.documento for c in self.clientes):   # no se permiten documentos repetidos
            # se lanza la excepcion OperacionNoPermitidaError
            raise OperacionNoPermitidaError(f"Ya existe un cliente con el documento {cliente.documento_oculto}")
        self.clientes.append(cliente)        # se agrega a la lista
        logger.info(f"Cliente registrado: {cliente.id} - {cliente.nombre}")   # se registra el evento en el log
        return cliente   # devuelve el cliente encontrado

    def agregar_servicio(self, servicio):    # agrega un servicio ya creado
        if not isinstance(servicio, Servicio):   # solo se aceptan objetos Servicio
            # se lanza la excepcion ServicioInvalidoError
            raise ServicioInvalidoError("Solo se pueden agregar objetos de tipo Servicio")
        self.servicios.append(servicio)      # se agrega a la lista
        logger.info(f"Servicio agregado: {servicio.id} - {servicio.nombre}")   # se registra el evento en el log
        return servicio   # devuelve el servicio agregado

    @singledispatchmethod   # decorador: el metodo cambia segun el tipo del argumento (sobrecarga)
    def buscar_cliente(self, criterio):      # version general: tipo de dato no soportado
        # se lanza la excepcion DatoInvalidoError
        raise DatoInvalidoError(f"No se puede buscar un cliente con un dato de tipo {type(criterio).__name__}")

    @buscar_cliente.register   # registra otra version del metodo para un tipo de dato distinto
    def _(self, criterio: str):              # "sobrecarga" 1: si llega texto se busca por id (CLI-001)
        for cliente in self.clientes:   # se recorre la lista de clientes
            if cliente.id == criterio.strip().upper():   # compara el id sin importar mayusculas
                return cliente   # devuelve el cliente encontrado
        # se lanza la excepcion DatoInvalidoError
        raise DatoInvalidoError(f"No hay ningun cliente con id '{criterio}'")

    @buscar_cliente.register   # registra otra version del metodo para un tipo de dato distinto
    def _(self, criterio: int):              # "sobrecarga" 2: si llega un numero se busca por documento
        for cliente in self.clientes:   # se recorre la lista de clientes
            if cliente.documento == str(criterio):   # compara el documento como texto
                return cliente   # devuelve el cliente encontrado
        # se lanza la excepcion DatoInvalidoError
        raise DatoInvalidoError(f"No hay ningun cliente con documento terminado en {str(criterio)[-4:]}")

    # crea y confirma una reserva en un solo paso
    def crear_reserva(self, cliente, servicio, duracion, confirmar=True, impuesto=True, descuento=0.0):
        """Crea la reserva y, si se pide, la confirma. Usa el bloque completo try/except/else/finally."""
        reserva = Reserva(cliente, servicio, duracion)   # puede lanzar ReservaInvalidaError o ParametroFaltanteError
        if not confirmar:                    # si solo se quiere dejar pendiente
            self.reservas.append(reserva)   # se guarda la reserva en la lista del sistema
            return reserva   # devuelve la reserva creada
        try:   # bloque que puede generar errores
            reserva.confirmar(impuesto, descuento)       # se intenta confirmar
        except ReservaInvalidaError:         # si la confirmacion falla
            reserva.cancelar("fallo en la confirmacion")     # la reserva no queda colgada, se cancela
            raise                            # se vuelve a lanzar el mismo error hacia arriba
        else:   # solo se ejecuta si el try no tuvo errores
            logger.info(f"Reserva {reserva.id} lista para pago")     # solo si se confirmo bien
        finally:   # se ejecuta siempre, haya error o no
            self.reservas.append(reserva)    # siempre queda en el historial, confirmada o cancelada
        return reserva   # devuelve la reserva creada

    def ejecutar(self, descripcion, operacion, *args, **kwargs):   # envoltorio que protege cualquier operacion
        """Ejecuta cualquier operacion. Si falla, registra el error y el sistema sigue funcionando."""
        self.operaciones += 1                # se cuenta la operacion
        numero = self.operaciones            # numero de esta operacion
        print(f"\nOperacion {numero:02d}: {descripcion}")   # se muestra el mensaje en pantalla
        try:   # bloque que puede generar errores
            resultado = operacion(*args, **kwargs)   # se ejecuta la operacion que llego como parametro
        except SoftwareFJError as error:     # errores conocidos del sistema
            self.fallidas += 1   # se cuenta como operacion fallida
            causa = error.__cause__          # excepcion original si hubo encadenamiento (raise ... from)
            # texto extra con la causa original
            detalle = f"\n   causa original -> {type(causa).__name__}: {causa}" if causa else ""
            # se muestra el mensaje en pantalla
            print(f"   ERROR CONTROLADO -> {type(error).__name__}: {error}{detalle}")
            # se registra el error en el log
            logger.error(f"Op {numero:02d} '{descripcion}' -> {type(error).__name__}: {error}"
                         + (f" | causa: {type(causa).__name__}: {causa}" if causa else ""))
            return None                      # la operacion falla pero el programa NO se detiene
        except Exception as error:           # cualquier error que no se esperaba
            self.fallidas += 1   # se cuenta como operacion fallida
            print(f"   ERROR INESPERADO -> {type(error).__name__}: {error}")   # se muestra el mensaje en pantalla
            # se registra el error en el log
            logger.critical(f"Op {numero:02d} '{descripcion}' -> error no previsto {type(error).__name__}: {error}")
            return None                      # tampoco se detiene el programa
        else:   # solo se ejecuta si el try no tuvo errores
            self.exitosas += 1               # solo si no hubo errores
            print(f"   OK -> {resultado}")   # se muestra el mensaje en pantalla
            logger.info(f"Op {numero:02d} '{descripcion}' completada")   # se registra el evento en el log
            return resultado   # devuelve lo que produjo la operacion
        finally:   # se ejecuta siempre, haya error o no
            # se registra el evento en el log
            logger.info(f"Op {numero:02d} finalizada (exitosas: {self.exitosas}, fallidas: {self.fallidas})")

    def resumen(self):                       # muestra el estado final del sistema
        print("\n" + "=" * 70)   # linea separadora
        print("RESUMEN DEL SISTEMA SOFTWARE FJ")   # titulo del resumen
        print("=" * 70)   # linea separadora
        # se muestra el mensaje en pantalla
        print(f"Operaciones: {self.operaciones} | exitosas: {self.exitosas} | con error controlado: {self.fallidas}")
        print(f"\nClientes ({len(self.clientes)}):")   # se muestra el mensaje en pantalla
        for cliente in self.clientes:   # se recorre la lista de clientes
            print("  ", cliente)             # usa describir() de Cliente
        print(f"\nServicios ({len(self.servicios)}):")   # se muestra el mensaje en pantalla
        for servicio in self.servicios:   # se recorre la lista de servicios
            print("  ", servicio)            # polimorfismo: cada servicio se describe distinto
        print(f"\nReservas ({len(self.reservas)}):")   # se muestra el mensaje en pantalla
        for reserva in self.reservas:   # se recorre la lista de reservas
            print("  ", reserva)   # imprime cada reserva con su describir()
        ingresos = sum(r.costo for r in self.reservas if r.estado == "PROCESADA")   # solo cuenta las pagadas
        print(f"\nIngresos de reservas pagadas: ${ingresos:,.2f}")   # se muestra el mensaje en pantalla
        # se registra el evento en el log
        logger.info(f"===== Fin de la simulacion: {self.exitosas} exitosas, {self.fallidas} fallidas =====")


# =====================================================================
# PARTE 5 - Simulacion de operaciones (casos validos e invalidos)
# =====================================================================

def simular():                               # funcion que corre todas las pruebas del sistema
    """Simula mas de 10 operaciones completas mezclando casos correctos y con error."""
    sistema = SistemaSoftwareFJ()            # se crea el sistema vacio

    # ---------- Clientes ----------
    # Op 01 (valida): cliente con todos los datos correctos, el nombre se corrige a mayusculas
    ana = sistema.ejecutar("Registrar cliente valido (Ana)", sistema.registrar_cliente,
                           nombre="ana maria torres", documento="1045678912",
                           correo="ana.torres@correo.com", telefono="3004567890")
    # Op 02 (valida): el documento llega como numero y el setter lo convierte a texto
    carlos = sistema.ejecutar("Registrar cliente valido (Carlos)", sistema.registrar_cliente,
                              nombre="Carlos Pertuz", documento=72345678, correo="cpertuz@correo.com")
    # Op 03 (invalida): el nombre tiene numeros -> ClienteInvalidoError
    sistema.ejecutar("Registrar cliente con numeros en el nombre", sistema.registrar_cliente,
                     nombre="Luis 123", documento="1122334455", correo="luis@correo.com")
    # Op 04 (invalida): no se envia el correo -> ParametroFaltanteError
    sistema.ejecutar("Registrar cliente sin correo", sistema.registrar_cliente,
                     nombre="Marta Gil", documento="99887766")
    # Op 05 (invalida): correo sin @ -> ClienteInvalidoError
    sistema.ejecutar("Registrar cliente con correo mal escrito", sistema.registrar_cliente,
                     nombre="Pedro Rios", documento="55443322", correo="pedro.correo.com")
    # Op 06 (invalida): documento que ya existe -> OperacionNoPermitidaError
    sistema.ejecutar("Registrar cliente con documento repetido", sistema.registrar_cliente,
                     nombre="Ana Copia", documento="1045678912", correo="copia@correo.com")

    # ---------- Servicios ----------
    # Op 07 (valida): sala para 25 personas (tiene recargo por ser grande)
    sala = sistema.ejecutar("Crear servicio de sala", lambda: sistema.agregar_servicio(
        ReservaSala("Sala Caribe", 45000, capacidad=25)))
    # Op 08 (valida): alquiler de 3 portatiles
    equipo = sistema.ejecutar("Crear servicio de alquiler de equipos", lambda: sistema.agregar_servicio(
        AlquilerEquipo("Portatiles Core i7", 60000, "portatil", unidades=3)))
    # Op 09 (valida): asesoria de nivel experto (tarifa x 1.5)
    asesoria = sistema.ejecutar("Crear servicio de asesoria", lambda: sistema.agregar_servicio(
        Asesoria("Asesoria en ciberseguridad", 120000, "Seguridad informatica", nivel="experto")))
    # Op 10 (invalida): tarifa negativa -> ServicioInvalidoError
    sistema.ejecutar("Crear servicio con tarifa negativa", lambda: sistema.agregar_servicio(
        ReservaSala("Sala Norte", -30000, capacidad=10)))
    # Op 11 (invalida): nivel que no existe -> ServicioInvalidoError
    sistema.ejecutar("Crear asesoria con nivel inexistente", lambda: sistema.agregar_servicio(
        Asesoria("Asesoria contable", 80000, "Contabilidad", nivel="master")))
    # Op 12 (invalida): tarifa escrita en letras -> ServicioInvalidoError
    sistema.ejecutar("Crear alquiler con tarifa en texto", lambda: sistema.agregar_servicio(
        AlquilerEquipo("Videobeam", "cincuenta mil", "videobeam")))

    # ---------- Polimorfismo y sobrecarga ----------
    def cotizar():                           # funcion auxiliar para la prueba de polimorfismo
        # cada servicio llama su propio calcular_costo_base, aunque la llamada sea la misma
        return " | ".join(f"{s.nombre}: ${s.calcular_costo(2):,.0f}" for s in sistema.servicios)
    # Op 13 (valida): misma llamada, resultado distinto en cada servicio
    sistema.ejecutar("Cotizar 2 unidades de cada servicio (polimorfismo)", cotizar)
    # Op 14 (valida): el mismo metodo llamado con 1, 2 y 3 parametros
    sistema.ejecutar("Calcular costo de asesoria con 3 variantes (sobrecarga)", lambda: (
        f"base ${asesoria.calcular_costo(2):,.0f} | con IVA ${asesoria.calcular_costo(2, True):,.0f} | "
        f"con IVA y 10% desc ${asesoria.calcular_costo(2, True, 0.10):,.0f}"))

    # ---------- Reservas ----------
    # Op 15 (valida): reserva de sala por 3 horas con IVA
    r1 = sistema.ejecutar("Reserva exitosa de sala (3 horas, con IVA)",
                          sistema.crear_reserva, ana, sala, 3)
    # Op 16 (valida): reserva de equipos por 7 dias con IVA y 10 % de descuento
    r2 = sistema.ejecutar("Reserva exitosa de equipos (7 dias, IVA y 10% de descuento)",
                          sistema.crear_reserva, carlos, equipo, 7, descuento=0.10)
    # Op 17 (invalida): 20 horas de asesoria -> ReservaInvalidaError encadenada con ServicioInvalidoError
    sistema.ejecutar("Reserva de asesoria por 20 horas (fuera de rango)",
                     sistema.crear_reserva, ana, asesoria, 20)
    # Op 18 (invalida): 2.5 dias de alquiler -> ReservaInvalidaError encadenada
    sistema.ejecutar("Reserva de equipos por 2.5 dias (no son dias completos)",
                     sistema.crear_reserva, carlos, equipo, 2.5)
    # Op 19 (invalida): se manda un texto en vez de un objeto Cliente -> ReservaInvalidaError
    sistema.ejecutar("Reserva con un cliente que no esta registrado",
                     sistema.crear_reserva, "Cliente Fantasma", sala, 2)
    # Op 20 (invalida): duracion vacia -> ParametroFaltanteError
    sistema.ejecutar("Reserva sin indicar la duracion",
                     sistema.crear_reserva, ana, sala, None)
    # Op 21 (invalida): descuento de 150 % -> CalculoInconsistenteError, la reserva queda cancelada
    sistema.ejecutar("Reserva con descuento del 150% (calculo inconsistente)",
                     sistema.crear_reserva, carlos, asesoria, 2, descuento=1.5)

    def cambiar_disponibilidad(servicio, valor):     # funcion auxiliar para activar o desactivar un servicio
        servicio.disponible = valor          # usa el setter, que valida y deja registro en el log
        return servicio.describir()          # devuelve como quedo el servicio
    # Op 22 (valida): la sala entra en mantenimiento
    sistema.ejecutar("Poner la sala fuera de servicio", cambiar_disponibilidad, sala, False)
    # Op 23 (invalida): reservar la sala en mantenimiento -> ServicioNoDisponibleError encadenada
    sistema.ejecutar("Reservar la sala que no esta disponible",
                     sistema.crear_reserva, carlos, sala, 2)
    # Op 24 (valida): la sala vuelve a estar disponible
    sistema.ejecutar("Volver a habilitar la sala", cambiar_disponibilidad, sala, True)

    # ---------- Procesamiento de pagos ----------
    # Op 25 (invalida): pago en letras -> DatoInvalidoError encadenada con ValueError
    sistema.ejecutar("Pagar reserva con texto en vez de numero", r1.procesar, "doscientos mil")
    # Op 26 (invalida): el pago no alcanza -> CalculoInconsistenteError
    sistema.ejecutar("Pagar reserva con dinero insuficiente", r1.procesar, 50000)
    # Op 27 (valida): pago correcto, se calcula el cambio
    sistema.ejecutar("Pagar reserva con el valor correcto", r1.procesar, 200000)
    # Op 28 (invalida): no se puede cancelar algo ya pagado -> OperacionNoPermitidaError
    sistema.ejecutar("Cancelar una reserva que ya fue pagada", r1.cancelar, "cliente se arrepintio")
    # Op 29 (valida): pago exacto de la reserva de equipos
    sistema.ejecutar("Pagar reserva de equipos", r2.procesar, r2.costo)

    # Op 30 (valida): reserva que se deja pendiente sin confirmar
    r3 = sistema.ejecutar("Dejar una reserva de asesoria pendiente",
                          sistema.crear_reserva, ana, asesoria, 1.5, confirmar=False)
    # Op 31 (invalida): pagar sin confirmar -> OperacionNoPermitidaError
    sistema.ejecutar("Pagar una reserva que no esta confirmada", r3.procesar, 300000)
    # Op 32 (valida): cancelacion normal de una reserva pendiente
    sistema.ejecutar("Cancelar la reserva pendiente", r3.cancelar, "cambio de fecha")
    # Op 33 (invalida): confirmar algo cancelado -> OperacionNoPermitidaError
    sistema.ejecutar("Confirmar una reserva que ya fue cancelada", r3.confirmar)

    # ---------- Busquedas (sobrecarga por tipo de dato) ----------
    # Op 34 (valida): si llega un entero se busca por documento
    sistema.ejecutar("Buscar cliente por documento (numero)", sistema.buscar_cliente, 72345678)
    # Op 35 (valida): si llega texto se busca por id
    sistema.ejecutar("Buscar cliente por id (texto)", sistema.buscar_cliente, "cli-001")
    # Op 36 (invalida): un decimal no es un tipo soportado -> DatoInvalidoError
    sistema.ejecutar("Buscar cliente con un dato decimal", sistema.buscar_cliente, 3.14)

    # ---------- Error no previsto ----------
    # Op 37 (invalida): IndexError de Python, lo atrapa el except Exception y el sistema sigue
    sistema.ejecutar("Consultar una posicion que no existe en la lista", lambda: sistema.clientes[50])

    sistema.resumen()                        # al final se muestra el estado del sistema
    return sistema                           # se devuelve por si se quiere seguir usando


if __name__ == "__main__":                   # solo se ejecuta si se corre este archivo directamente
    simular()                                # se ejecuta la simulacion completa
    print(f"\nRevise el archivo '{ARCHIVO_LOG}' para ver todos los eventos y errores registrados.")   # aviso final
