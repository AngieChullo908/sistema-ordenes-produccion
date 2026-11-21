# Gestión de Órdenes de Producción

Aplicación de escritorio para gestionar órdenes de producción en una panadería. Desarrollada para el curso de Gestión de Datos e Información de la Universidad Católica de Santa María.

**Versión:** 1.1.1.

## Funcionalidades

- Registro, búsqueda y consulta de órdenes de producción.
- Modificación, cancelación y eliminación de órdenes pendientes.
- Inicio de producción y registro del cierre con cantidades producidas, pérdidas y motivos de merma.
- Consulta de recetas y existencias de insumos.
- Diez reportes con consultas JOIN y exportación de resultados a CSV.

El cierre incrementa el stock de productos terminados. El aplicativo no calcula ni descuenta automáticamente los ingredientes utilizados.

## Tecnologías

Python 3.12, Tkinter y ttk, Psycopg 3.3.8 y PostgreSQL 14 o superior. La aplicación no utiliza frameworks ni ORM. El acceso a los datos se realiza mediante procedimientos almacenados; las validaciones y actualizaciones automáticas de la base se complementan con triggers.

## Instalación en Windows

Los archivos de distribución se descargan desde [Releases](https://github.com/AngieChullo908/sistema-ordenes-produccion/releases).

1. Descargar y descomprimir `Gestion_Ordenes_Produccion_Windows.zip`.
2. Ejecutar `Gestion_Ordenes_Produccion_Instalador.exe` y seguir el asistente.
3. Preparar la base de datos según el apartado siguiente.
4. Abrir el acceso directo **Gestión de Órdenes de Producción** del escritorio e ingresar los datos de conexión.

El instalador incluye Python, Tcl/Tk y el conector PostgreSQL. Requiere Windows 10 u 11 de 64 bits. PostgreSQL se instala y configura por separado, en el equipo local o en un servidor accesible.

## Preparación de la base de datos

Para una base nueva, ejecutar los scripts desde pgAdmin en este orden:

1. Sobre la base `postgres`, ejecutar `database/00_crear_base.sql` fuera de una transacción.
2. Abrir la herramienta de consultas sobre `avecesar_produccion` y ejecutar:

| Orden | Archivo | Contenido |
| --- | --- | --- |
| 1 | `01_crear_tablas.sql` | Tablas y restricciones |
| 2 | `02_insertar_datos.sql` | Datos de prueba |
| 3 | `05_aplicativo.sql` | Operaciones y reglas del aplicativo |
| 4 | `06_consultas_procedimientos.sql` | Procedimientos de consulta y reportes |

La carga inicial contiene 275 registros y se ejecuta una sola vez. Si la base ya contiene información de trabajo, la aplicación se conecta a ella sin repetir los scripts de creación ni la carga de prueba.

Los archivos 03 y 04 contienen consultas y comprobaciones. El archivo 07 es una ampliación opcional exclusiva para la base `avecesar_demo`.

En el paquete de Windows, los scripts se encuentran en `Scripts_SQL`; después de la instalación también están en la carpeta `database` del aplicativo.

## Conexión a PostgreSQL

La pantalla de acceso solicita servidor, puerto, base de datos, usuario, contraseña y modo SSL.

| Campo | Valor habitual para una instalación local |
| --- | --- |
| Servidor | `localhost` |
| Puerto | `5432` |
| Base de datos | `avecesar_produccion` |
| Usuario | Cuenta configurada en PostgreSQL |
| Contraseña | Contraseña de esa cuenta de PostgreSQL |
| SSL | `prefer`, salvo una configuración distinta del servidor |

El aplicativo no incluye una contraseña predeterminada ni requiere una cuenta propia. La contraseña de PostgreSQL es independiente de la contraseña del dispositivo y de la contraseña maestra de pgAdmin.

## Ejecución desde el código fuente

Con Python 3.12 y Tkinter instalados, ejecutar desde la carpeta principal:

```bash
python -m pip install -r requirements.txt
python main.py
```

En macOS o Linux, el comando puede llamarse `python3`. La base de datos debe estar preparada y disponible antes de conectarse.

## Estructura del proyecto

| Ruta | Descripción |
| --- | --- |
| `main.py` | Inicio del aplicativo |
| `app/views/` | Ventanas y formularios |
| `app/controllers/` | Coordinación de las acciones de la interfaz |
| `app/models/` | Reglas y validaciones |
| `app/infrastructure/` | Configuración y acceso a PostgreSQL |
| `database/` | Scripts de creación, datos y objetos de la base |
| `packaging/` | Construcción del instalador de Windows |
| `verificar_entorno.py` | Diagnóstico del entorno incluido en Windows |
| `VERIFICAR_WINDOWS.bat` | Ejecución del diagnóstico en Windows |
| `requirements.txt` | Dependencia del conector |

## Construcción del instalador

La construcción requiere Windows, Python 3.12 de 64 bits con Tcl/Tk y NSIS 3 con `makensis` disponible en PATH. Se realiza mediante `packaging/RECONSTRUIR_WINDOWS.bat`.

Las carpetas `runtime` y `vendor` y los archivos `.exe` se generan durante el empaquetado y no forman parte del código versionado. La distribución del instalador se realiza mediante Releases.
