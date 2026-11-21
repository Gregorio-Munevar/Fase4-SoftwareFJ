# Fase 4 - Sistema Integral de Gestión de Clientes, Servicios y Reservas - Software FJ

Curso **Programación 213023 - UNAD** · Fase 4 - Componente práctico - Prácticas simuladas

Sistema en Python orientado a objetos que gestiona clientes, servicios (reserva de salas, alquiler de equipos y asesorías) y reservas para la empresa ficticia Software FJ. No usa base de datos: todo se maneja con objetos y listas, y el único archivo es el log de eventos y errores.

## Cómo ejecutarlo

```bash
python main.py
```

No requiere instalar nada: solo usa módulos estándar de Python 3 (`abc`, `datetime`, `functools`, `logging`, `re`). Al ejecutarlo se crea o actualiza el archivo `software_fj.log`.

También se puede abrir `Fase4_SoftwareFJ.ipynb` en Jupyter o VS Code y ejecutar las celdas en orden.

## Qué incluye

| Requisito del Anexo 3 | Dónde está |
|---|---|
| Clase abstracta de entidades | `Entidad` |
| Cliente con validaciones y encapsulación | `Cliente` (atributos privados + properties) |
| Clase abstracta Servicio + 3 servicios | `Servicio` → `ReservaSala`, `AlquilerEquipo`, `Asesoria` |
| Polimorfismo y métodos sobrescritos | `calcular_costo_base`, `validar_parametros`, `describir` |
| Reserva con confirmación, cancelación y procesamiento | `Reserva.confirmar / cancelar / procesar` |
| Métodos sobrecargados | `calcular_costo(duracion, impuesto, descuento)` y `buscar_cliente` con `singledispatchmethod` |
| Excepciones personalizadas | 9 clases que heredan de `SoftwareFJError` |
| try/except, try/except/else, try/except/finally | `confirmar`, `procesar`, `crear_reserva`, `ejecutar` |
| Encadenamiento de excepciones | `raise ... from error` en `Reserva` |
| Archivo de logs | `software_fj.log` |
| Mínimo 10 operaciones | 37 operaciones (17 válidas, 20 con error controlado) |

## Estructura del código (`main.py`)

1. Importaciones, log y excepciones personalizadas
2. Clase abstracta `Entidad` y clase `Cliente`
3. Clase abstracta `Servicio` y servicios especializados
4. Clase `Reserva` y gestor `SistemaSoftwareFJ`
5. Simulación de operaciones
