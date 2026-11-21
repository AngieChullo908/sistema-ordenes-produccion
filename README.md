# Gestión de Órdenes de Producción

Cliente de escritorio desarrollado para Gestión de Datos e Información de la Universidad Católica de Santa María. Implementa la funcionalidad de órdenes de producción del caso Panadería AVECESAR. Versión del aplicativo: 1.1.1.

## Qué permite hacer

Crear, buscar y consultar órdenes; modificar, cancelar o eliminar pendientes; iniciar una orden y registrar su cierre con cantidades producidas y pérdidas. También permite consultar recetas, existencias de insumos y diez reportes, y exportar resultados a CSV.

Los catálogos se consultan desde la interfaz. El cierre suma el producto terminado al stock, pero no calcula ni descuenta automáticamente ingredientes.

## Herramientas

Python 3.12, Tkinter y ttk, Psycopg 3.3.8 y PostgreSQL 14 o superior. No utiliza un framework de aplicación ni ORM.

## Preparar una base nueva

1. Instalar PostgreSQL y pgAdmin y conservar los datos de conexión.
2. Sobre la base `postgres`, ejecutar `database/00_crear_base.sql` fuera de un bloque `BEGIN`.
3. Abrir la herramienta de consultas sobre `avecesar_produccion` y ejecutar los archivos completos en este orden:
   - `01_crear_tablas.sql`
   - `02_insertar_datos.sql`, una sola vez
   - `05_aplicativo.sql`
   - `06_consultas_procedimientos.sql`

Los archivos 03 y 04 son consultas y verificaciones. El archivo 07 es opcional y está reservado para `avecesar_demo`; no debe ejecutarse sobre la base normal.

La carga inicial contiene 275 registros. Este script corrige el dato de prueba de OP000001/P001 a 270 producidas y 0 perdidas, para que coincida con las 270 programadas. No vuelva a ejecutar la carga inicial sobre una base con información existente.

## Ejecutar desde el código

Con Python y Tkinter instalados, abrir una terminal en esta carpeta:

```console
python -m pip install -r requirements.txt
python main.py
```

Al abrir el sistema, indicar servidor, puerto, base, usuario, contraseña y SSL. Para una instalación local habitual: `localhost`, `5432`, `avecesar_produccion` y `prefer`. El usuario y la contraseña son los de PostgreSQL en el equipo utilizado; no existe una contraseña predeterminada del aplicativo.

Para utilizar el instalador Windows entregado al docente no se necesita abrir el entorno de programación. El instalador y el manual se presentan por separado; PostgreSQL sigue siendo un requisito externo.

## Organización del código

- `main.py`: inicio del programa.
- `app/views`: ventanas y formularios.
- `app/controllers`: coordinación de las acciones.
- `app/models`: reglas y validaciones.
- `app/infrastructure`: configuración y acceso a PostgreSQL.
- `database`: creación, datos de prueba, procedimientos, funciones y triggers.
- `requirements.txt`: dependencia del conector.

Las operaciones de negocio utilizan procedimientos almacenados. Los scripts incluyen 21 procedimientos, cuatro triggers y diez reportes con JOIN.

## Entrega académica

El informe, el manual de usuario, la memoria descriptiva y el instalador acompañan la entrega al docente. Los DNI y las cesiones de derechos se conservan en DOCUMENTOS y no se publican en este repositorio.

## Verificación

Se incluyen 35 pruebas en `tests` y el registro y las instrucciones para repetirlas en `docs/VALIDACION.md`. Se ejecutan en una base de ensayo; no utilice la base de trabajo para probar eliminaciones y cierres.

## Instalador de Windows

El archivo `Gestion_Ordenes_Produccion_Instalador.exe` se entrega por separado y puede publicarse en Releases de GitHub. Incluye Python y las dependencias; PostgreSQL se prepara por separado. El ZIP del código fuente no incluye esos binarios.

Para reconstruirlo en Windows: instalar Python 3.12 de 64 bits con Tcl/Tk y NSIS 3 con `makensis` en PATH; ejecutar `packaging/RECONSTRUIR_WINDOWS.bat`. Los archivos de empaquetado están en `packaging`. Las licencias de las dependencias se conservan en el instalador.

El formulario de cierre ajusta las columnas al ancho de la ventana y muestra la barra de desplazamiento cuando hay más filas de las que caben. El botón de confirmación permanece fuera del área desplazable. Esta corrección mantiene la funcionalidad y los scripts SQL de la versión 1.1.1.
