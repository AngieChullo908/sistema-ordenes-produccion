"""Persistencia MVC sin ORM: CALL para negocio y FETCH para sus resultados."""
from dataclasses import asdict
import re
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from app.models.order import BusinessError, validate_close


class ConnectionFactory:
    def __init__(self, settings):
        self.settings = settings.copy()

    def connect(self):
        return psycopg.connect(
            **self.settings, connect_timeout=5, row_factory=dict_row,
            options='-c statement_timeout=10000 -c lock_timeout=4000 -c search_path=public'
        )


class PostgresRepository:
    """Los procedimientos de lectura entregan un cursor dentro de la transacción.

    Sus nombres provienen del código y se componen como identificadores SQL.
    Los valores del usuario siempre se envían como parámetros enlazados.
    """
    REQUIRED_PROCEDURES = ['sp_listar_empleados', 'sp_listar_productos', 'sp_listar_ingredientes', 'sp_listar_ordenes', 'sp_consultar_orden', 'sp_consultar_detalle_orden', 'sp_consultar_receta', 'sp_reporte_ordenes', 'sp_reporte_ordenes_activas', 'sp_reporte_productos_orden', 'sp_reporte_inventario_productos', 'sp_reporte_existencias_ingredientes', 'sp_reporte_ingredientes_receta', 'sp_reporte_produccion_acumulada', 'sp_reporte_programacion_resultados', 'sp_reporte_perdidas', 'sp_reporte_historial_cierres', 'sp_guardar_orden', 'sp_cambiar_estado', 'sp_eliminar_orden', 'sp_cerrar_orden']

    def __init__(self, factory):
        self.factory = factory

    @staticmethod
    def _call(connection, procedure, parameters=()):
        placeholders = [sql.Placeholder() for _ in parameters]
        statement = sql.SQL('CALL public.{}({})').format(
            sql.Identifier(procedure), sql.SQL(', ').join(placeholders)
        )
        try:
            return connection.execute(statement, parameters)
        except psycopg.errors.RaiseException as exc:
            # Mensajes controlados de las reglas PL/pgSQL, sin SQL ni credenciales.
            raise BusinessError(exc.diag.message_primary or 'Operación rechazada.') from exc

    @classmethod
    def _read(cls, connection, procedure, parameters=()):
        cursor_name = 'avecesar_resultado'
        # El último argumento se tipa refcursor. El mismo nombre puede reutilizarse
        # después de CLOSE; cada operación posee su propia conexión.
        placeholders = [sql.Placeholder() for _ in parameters] + [sql.SQL('%s::refcursor')]
        statement = sql.SQL('CALL public.{}({})').format(
            sql.Identifier(procedure), sql.SQL(', ').join(placeholders)
        )
        connection.execute(statement, tuple(parameters) + (cursor_name,))
        result = connection.execute(
            sql.SQL('FETCH ALL FROM {}').format(sql.Identifier(cursor_name))
        )
        columns = [column.name for column in result.description]
        rows = result.fetchall()
        connection.execute(sql.SQL('CLOSE {}').format(sql.Identifier(cursor_name)))
        return columns, rows

    def check(self):
        with self.factory.connect() as connection:
            # Introspección técnica; no consulta datos de negocio.
            rows = connection.execute(
                "SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='public' AND p.prokind='p' AND p.proname=ANY(%s)",
                (self.REQUIRED_PROCEDURES,)
            ).fetchall()
            missing = set(self.REQUIRED_PROCEDURES) - {row['proname'] for row in rows}
            if missing:
                script = '05_aplicativo.sql y 06_consultas_procedimientos.sql' if 'sp_guardar_orden' in missing else '06_consultas_procedimientos.sql'
                raise BusinessError('Faltan procedimientos. Ejecute database/' + script + ' en la base seleccionada. No repita la carga de datos.')

    def catalog(self):
        with self.factory.connect() as connection:
            return {
                'employees': self._read(connection, 'sp_listar_empleados')[1],
                'products': self._read(connection, 'sp_listar_productos')[1],
                'ingredients': self._read(connection, 'sp_listar_ingredientes')[1]
            }

    def orders(self, search='', state='Todos'):
        with self.factory.connect() as connection:
            return self._read(connection, 'sp_listar_ordenes', (search, state))[1]

    def detail(self, number):
        with self.factory.connect() as connection:
            headers = self._read(connection, 'sp_consultar_orden', (number,))[1]
            if not headers:
                raise BusinessError('La orden ya no existe. Actualice la lista.')
            lines = self._read(connection, 'sp_consultar_detalle_orden', (number,))[1]
            return headers[0], lines

    def recipe(self, recipe):
        with self.factory.connect() as connection:
            return self._read(connection, 'sp_consultar_receta', (recipe,))[1]

    def save(self, number, day, employee, lines):
        with self.factory.connect() as connection:
            row = self._call(connection, 'sp_guardar_orden',
                (number, day, employee, Jsonb([asdict(line) for line in lines]))).fetchone()
            return row['p_numero']

    def start(self, number):
        with self.factory.connect() as connection:
            self._call(connection, 'sp_cambiar_estado', (number, 'En curso'))

    def cancel(self, number):
        with self.factory.connect() as connection:
            self._call(connection, 'sp_cambiar_estado', (number, 'Cancelado'))

    def delete(self, number):
        with self.factory.connect() as connection:
            self._call(connection, 'sp_eliminar_orden', (number,))

    def close(self, number, results):
        with self.factory.connect() as connection:
            lines = self._read(connection, 'sp_consultar_detalle_orden', (number,))[1]
            validate_close({line['cod_producto']: line['cant_programada'] for line in lines}, results)
            # El procedimiento controla estado, bloqueos, cantidades y stock de
            # forma atómica. También vuelve a validar tras adquirir los bloqueos.
            self._call(connection, 'sp_cerrar_orden',
                       (number, Jsonb([asdict(line) for line in results])))

    def report(self, index, parameter=''):
        from app.infrastructure.reports import REPORTS
        if not isinstance(index, int) or not 0 <= index < len(REPORTS):
            raise BusinessError('Seleccione un reporte válido.')
        title, procedure, needs_parameter = REPORTS[index]
        value = parameter.strip().upper()
        if needs_parameter:
            pattern = r'OP[0-9]{6}' if index == 2 else r'R[0-9]{3}'
            if not re.fullmatch(pattern, value):
                example = 'OP000010' if index == 2 else 'R001'
                raise BusinessError('Ingrese un código válido, por ejemplo ' + example + '.')
        with self.factory.connect() as connection:
            return self._read(connection, procedure, (value,) if needs_parameter else ())
