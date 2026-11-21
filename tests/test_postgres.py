"""Requiere BD desechable terminada en _test y TEST_DSN. Nunca usar producción."""
import os
import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
import psycopg
from psycopg.conninfo import conninfo_to_dict
from app.infrastructure.postgres import ConnectionFactory,PostgresRepository
from app.models.order import OrderLine,FinalLine,BusinessError,ProductionService

@unittest.skipUnless(os.environ.get('TEST_DSN'),'Defina TEST_DSN con una BD de pruebas')
class PostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        values=conninfo_to_dict(os.environ['TEST_DSN'])
        if not values.get('dbname','').endswith('_test'): raise RuntimeError('Solo bases terminadas en _test')
        cls.repo=PostgresRepository(ConnectionFactory(values)); cls.service=ProductionService(cls.repo)
    def create(self,qty=4,product='P001'):
        return self.service.save(None,'2026-11-10','E001',[OrderLine(product,qty)])
    def test_connection_and_seed(self):
        self.repo.check(); self.assertEqual(len(self.repo.catalog()['products']),10)
    def test_create_edit_delete(self):
        number=self.create(); self.service.save(number,'2026-11-11','E002',[OrderLine('P002',8)])
        header,lines=self.repo.detail(number); self.assertEqual(header['codigo_empleado'],'E002'); self.assertEqual(lines[0]['cant_programada'],8)
        self.repo.delete(number)
        with self.assertRaises(BusinessError): self.repo.detail(number)
    def test_foreign_key_rollback(self):
        number=self.create()
        with self.assertRaises(psycopg.errors.ForeignKeyViolation): self.service.save(number,'2026-11-11','E001',[OrderLine('P999',8)])
        self.assertEqual(self.repo.detail(number)[1][0]['cod_producto'],'P001')
    def test_cancel_and_prevent_edits(self):
        number=self.create(); self.service.cancel(number)
        with self.assertRaises(BusinessError): self.service.save(number,'2026-11-11','E001',[OrderLine('P001',1)])
        with self.assertRaises(BusinessError): self.repo.delete(number)
    def test_close_and_stock_once(self):
        number=self.create(); self.service.start(number)
        before=next(p['stock'] for p in self.repo.catalog()['products'] if p['cod_producto']=='P001')
        self.service.close(number,[FinalLine('P001',3,1,'Quemado')])
        header,lines=self.repo.detail(number); self.assertEqual(header['estado'],'Finalizado'); self.assertEqual(header['resultado'],'Con merma')
        self.assertEqual(lines[0]['cant_perdida'],1)
        with self.assertRaises(BusinessError): self.service.close(number,[FinalLine('P001',3,1,'Quemado')])
        after=next(p['stock'] for p in self.repo.catalog()['products'] if p['cod_producto']=='P001')
        self.assertEqual(after,before+3)
    def test_invalid_close_rolls_back(self):
        number=self.create(); self.service.start(number)
        with self.assertRaises(BusinessError): self.service.close(number,[FinalLine('P001',2,0)])
        header,_=self.repo.detail(number); self.assertEqual(header['estado'],'En curso'); self.assertIsNone(header['resultado'])
    def test_stock_overflow_rollback(self):
        number=self.create(999); self.service.start(number)
        with self.assertRaises(BusinessError): self.service.close(number,[FinalLine('P001',999,0)])
        self.assertIsNone(self.repo.detail(number)[0]['resultado'])
    def test_concurrent_close(self):
        number=self.create(); self.service.start(number); barrier=threading.Barrier(2)
        def close():
            barrier.wait()
            try: self.service.close(number,[FinalLine('P001',4,0)]); return True
            except BusinessError: return False
        with ThreadPoolExecutor(2) as pool:
            a=pool.submit(close); b=pool.submit(close); self.assertEqual(sorted([a.result(),b.result()]),[False,True])
    def test_ten_reports(self):
        for index in range(10):
            cols,rows=self.repo.report(index,'R001' if index==5 else 'OP000010')
            self.assertTrue(cols); self.assertTrue(rows)
    def test_trigger_direct_invalid_transition(self):
        number=self.create()
        with self.assertRaises(psycopg.Error):
            with self.repo.factory.connect() as c: c.execute("UPDATE produccion SET estado='Finalizado' WHERE numero_orden=%s",(number,))
        self.assertEqual(self.repo.detail(number)[0]['estado'],'Pendiente')
    def test_database_close_late_failure_rolls_back_everything(self):
        from psycopg.types.json import Jsonb
        number=self.service.save(None,'2026-11-10','E001',[OrderLine('P001',4),OrderLine('P002',4)])
        self.service.start(number)
        before={p['cod_producto']:p['stock'] for p in self.repo.catalog()['products']}
        payload=[dict(product='P001',produced=4,lost=0,reason=''),dict(product='P002',produced=1,lost=0,reason='')]
        with self.assertRaises(psycopg.Error):
            with self.repo.factory.connect() as c: c.execute('CALL sp_cerrar_orden(%s,%s)',(number,Jsonb(payload)))
        header,lines=self.repo.detail(number)
        self.assertEqual(header['estado'],'En curso'); self.assertIsNone(header['resultado'])
        self.assertTrue(all(line['cant_producida'] is None for line in lines))
        after={p['cod_producto']:p['stock'] for p in self.repo.catalog()['products']}
        self.assertEqual(before,after)

    def test_terminal_header_immutable_in_database(self):
        number=self.create(); self.service.start(number)
        self.service.close(number,[FinalLine('P001',4,0)])
        with self.assertRaises(psycopg.Error):
            with self.repo.factory.connect() as c:
                c.execute("UPDATE produccion SET fecha_prog='2026-12-01' WHERE numero_orden=%s",(number,))
        self.assertEqual(str(self.repo.detail(number)[0]['fecha_prog']),'2026-11-10')

    def test_recipe_units_preserved(self):
        rows=self.repo.recipe('R001'); self.assertTrue(any(r['simbolo']=='g' and r['unidad_stock']=='kg' for r in rows))

    def test_report_filter_by_order_and_recipe(self):
        for number in ('OP000001','OP000010'):
            columns,rows=self.repo.report(2,number.lower())
            self.assertTrue(rows)
            self.assertEqual({r['numero_orden'] for r in rows},{number})
        columns,rows=self.repo.report(5,'r001')
        self.assertEqual({r['cod_receta'] for r in rows},{'R001'})

    def test_empty_report_preserves_columns(self):
        columns,rows=self.repo.report(2,'OP999999')
        self.assertEqual(columns,['numero_orden','nombre_producto','cant_programada'])
        self.assertEqual(rows,[])

    def test_bad_report_selection_and_parameter(self):
        for index in (-1,10,'1',None):
            with self.subTest(index=index),self.assertRaises(BusinessError): self.repo.report(index,'')
        for index,param in [(2,''),(5,''),(2,"OP000010'; DROP TABLE empleado; --"),(5,'OP000010')]:
            with self.subTest(index=index,param=param),self.assertRaises(BusinessError): self.repo.report(index,param)

    def test_reports_match_original_queries(self):
        import re
        from pathlib import Path
        original=(Path(__file__).resolve().parents[1]/'database/03_consultas.sql').read_text()
        queries=[part.split('\n',1)[1].strip() for part in re.split(r'-- CONSULTA \d+\. ',original)[1:]]
        self.assertEqual(len(queries),10)
        for index,query in enumerate(queries):
            self.assertIn('JOIN',query)
            with self.repo.factory.connect() as c:
                cursor=c.execute(query)
                expected_columns=[x.name for x in cursor.description]
                expected=cursor.fetchall()
            columns,rows=self.repo.report(index,'R001' if index==5 else 'OP000010')
            self.assertEqual(columns,expected_columns)
            normalize=lambda records: sorted([tuple(str(r[k]) for k in columns) for r in records])
            self.assertEqual(normalize(rows),normalize(expected))

    def test_reports_use_call_fetch_and_close(self):
        events=[];factory=self.repo.factory
        class TracedConnection:
            def __init__(self): self.connection=factory.connect()
            def __enter__(self): self.connection.__enter__();return self
            def __exit__(self,*args): return self.connection.__exit__(*args)
            def execute(self,statement,parameters=None):
                text=statement if isinstance(statement,str) else statement.as_string(self.connection)
                events.append(text)
                return self.connection.execute(statement,parameters)
        class TracedFactory:
            def connect(self): return TracedConnection()
        repo=PostgresRepository(TracedFactory())
        for index in range(10): repo.report(index,'R001' if index==5 else 'OP000010')
        self.assertEqual(len(events),30)
        for i in range(0,len(events),3):
            self.assertTrue(events[i].startswith('CALL public.'))
            self.assertTrue(events[i+1].startswith('FETCH ALL'))
            self.assertTrue(events[i+2].startswith('CLOSE'))
        self.assertFalse(any(e.startswith('SELECT') for e in events))

    def test_cursor_closed_after_read(self):
        with self.repo.factory.connect() as c:
            self.repo._read(c,'sp_reporte_ordenes')
            self.assertIsNone(c.execute("SELECT name FROM pg_cursors WHERE name='avecesar_resultado'").fetchone())

    def test_missing_read_migration_detected(self):
        with self.repo.factory.connect() as c:
            with c.transaction(force_rollback=True):
                c.execute('DROP PROCEDURE public.sp_reporte_ordenes(refcursor)')
                # Comprobar en la misma conexión evita esperar un bloqueo DDL externo.
                class SharedConnection:
                    def __enter__(self):return c
                    def __exit__(self,*args):return False
                class SharedFactory:
                    def connect(self):return SharedConnection()
                with self.assertRaisesRegex(BusinessError,'06_consultas'):
                    PostgresRepository(SharedFactory()).check()
        self.repo.check()

    def test_migration_reexecution_preserves_data(self):
        from pathlib import Path
        script=(Path(__file__).resolve().parents[1]/'database/06_consultas_procedimientos.sql').read_text()
        before=self.repo.orders()
        stocks=[(r['cod_producto'],r['stock']) for r in self.repo.catalog()['products']]
        for _ in range(2):
            with self.repo.factory.connect() as c:c.execute(script)
        self.assertEqual(before,self.repo.orders())
        self.assertEqual(stocks,[(r['cod_producto'],r['stock']) for r in self.repo.catalog()['products']])

    def test_order_search_is_parameterized(self):
        self.assertEqual(self.repo.orders("' OR 1=1 --"),[])
        self.assertTrue(self.repo.orders('Richard'))

    def test_optional_demo_adds_61_records_once(self):
        from pathlib import Path
        script=(Path(__file__).resolve().parents[1]/'database/07_datos_prueba_adicionales.sql').read_text()
        tables=['empleado','unidad_medida','categoria','receta','ingrediente','producto','detalle_receta','produccion','detalle_orden_produccion','registro_final','detalle_registro_final']
        def count():
            with self.repo.factory.connect() as c:return sum(c.execute('SELECT count(*) AS n FROM '+table).fetchone()['n'] for table in tables)
        before=count(); stocks=self.repo.catalog()['products']
        with self.repo.factory.connect() as c:c.execute(script)
        self.assertEqual(count(),before+61)
        with self.repo.factory.connect() as c:c.execute(script)
        self.assertEqual(count(),before+61)
        self.assertEqual(self.repo.catalog()['products'],stocks)

if __name__=='__main__': unittest.main()
