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
