# Verificación de la versión 1.1.1

Fecha: 21 de noviembre de 2026.

Se utilizó el código Python que coincide con el instalador entregado y el script de carga inicial corregido. La base temporal se creó desde cero con 01, 02, 05 y 06, sin utilizar una base de producción.

Entorno: Linux x86_64, Python 3.12.14, PostgreSQL 17.12 y Psycopg 3.3.8.

Resultado: 35 pruebas aprobadas, 0 errores, 0 fallos y 0 omitidas. Comprende 12 pruebas del modelo y 23 de integración: creación, consulta, edición y eliminación, cancelación, cierre y stock, reversión de cambios, cierre concurrente, filtros, cursores y los diez reportes. También se comprobó que la ampliación opcional agrega 61 registros sin duplicarlos al repetirse.

La carga inicial contiene 275 registros. Todas las líneas de cierre históricas de la carga corregida cumplen producida + perdida = programada.

Además se comprobó el formulario de cierre en Tk sobre Linux: seis productos a 1060 × 550, ampliación a 1480 × 900, reducción a 840 × 380, 30 productos con nombres largos y entrega intacta de valores al controlador. Se verificó que el ancho del contenido coincida con el área visible, que aparezca el desplazamiento cuando corresponde y que el botón permanezca accesible.

El instalador de Windows x64 se reconstruyó con NSIS y conserva el entorno Python y las dependencias del instalador anterior. Se extrajo el paquete generado para verificar que el código y los scripts coincidan con este repositorio.

Estas comprobaciones no sustituyen una instalación y ejecución nativas en Windows. Antes de entregar, instalar en un segundo equipo Windows, conectarse a PostgreSQL y comprobar registro, consulta, modificación, eliminación y cierre. Las capturas del manual son evidencia de uso aportada por el equipo.

## Repetir las pruebas

Crear una base desechable llamada `avecesar_test` y ejecutar sobre ella los archivos 01, 02, 05 y 06 completos. Instalar requirements.txt. Las pruebas modifican información y deben ejecutarse únicamente sobre esa base de ensayo.

En PowerShell, reemplazar los datos de conexión por los de esa instalación:

```powershell
$env:TEST_DSN = 'host=localhost port=5432 dbname=avecesar_test user=postgres password=REEMPLAZAR'
python -m unittest discover -s tests -v
```

Si TEST_DSN no está definido, se omiten las pruebas de integración. El nombre de la base debe terminar en `_test`; el caso de ampliación opcional utiliza específicamente `avecesar_test`.
