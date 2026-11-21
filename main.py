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
