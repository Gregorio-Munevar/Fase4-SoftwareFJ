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
