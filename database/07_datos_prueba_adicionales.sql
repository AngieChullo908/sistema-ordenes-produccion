-- OPCIONAL. SOLO para una base de demostración llamada avecesar_demo o avecesar_test.
-- No ejecutar sobre la base real avecesar_produccion.
-- Requiere 01, 02, 05 y 06. Agrega 61 registros a los 275 originales: total 336.
-- Los cambios se realizan mediante los procedimientos del aplicativo.
-- La segunda ejecución no duplica la carga.
BEGIN;
DO $demo$
DECLARE
    responsable text;
    numero text;
    i integer;
BEGIN
    IF current_database() NOT IN ('avecesar_demo','avecesar_test') THEN
        RAISE EXCEPTION 'Este script es solo para avecesar_demo o avecesar_test. No cambia la base real.';
    END IF;
    PERFORM pg_advisory_xact_lock(108118, 5);
    IF NOT EXISTS(SELECT 1 FROM producto WHERE cod_producto='P001')
       OR NOT EXISTS(SELECT 1 FROM producto WHERE cod_producto='P002') THEN
        RAISE EXCEPTION 'Cargue primero los datos originales del archivo 02 en esta base de prueba.';
    END IF;
    SELECT codigo_empleado INTO responsable FROM empleado
      WHERE nombre_empleado='Pruebas Entrega 5' AND cargo_empleado='Demostracion'
      ORDER BY codigo_empleado LIMIT 1;
    IF responsable IS NOT NULL AND EXISTS(
        SELECT 1 FROM produccion WHERE codigo_empleado=responsable
    ) THEN
        RAISE NOTICE 'La ampliación de demostración ya está cargada. No se duplicaron registros.';
        RETURN;
    END IF;
    IF responsable IS NULL THEN
        INSERT INTO empleado(nombre_empleado,cargo_empleado)
          VALUES('Pruebas Entrega 5','Demostracion') RETURNING codigo_empleado INTO responsable;
    END IF;
    FOR i IN 1..20 LOOP
        numero:=NULL;
        CALL sp_guardar_orden(numero, current_date+(i%5), responsable,
            jsonb_build_array(
                jsonb_build_object('product','P001','quantity',(i%5)+1),
                jsonb_build_object('product','P002','quantity',(i%3)+1)
            ));
        IF i<=5 THEN
            CALL sp_cambiar_estado(numero,'En curso');
        ELSIF i<=10 THEN
            CALL sp_cambiar_estado(numero,'Cancelado');
        END IF;
    END LOOP;
END;
$demo$;
COMMIT;
