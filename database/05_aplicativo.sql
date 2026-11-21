-- Ejecutar UNA VEZ en la base existente, después de 01 y (opcionalmente) 02.
-- No borra ni modifica los registros históricos. PostgreSQL 14 o superior.
BEGIN;
CREATE OR REPLACE FUNCTION fn_proteger_produccion() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.estado <> 'Pendiente' THEN RAISE EXCEPTION 'Solo se elimina una orden pendiente'; END IF;
    RETURN OLD;
  END IF;
  IF OLD.estado IN ('Finalizado','Cancelado') THEN
    RAISE EXCEPTION 'Una orden terminal es inmutable';
  END IF;
  IF NEW.estado <> OLD.estado AND NOT (
    (OLD.estado='Pendiente' AND NEW.estado IN ('En curso','Cancelado')) OR
    (OLD.estado='En curso' AND NEW.estado='Finalizado')) THEN
    RAISE EXCEPTION 'Transicion de estado no permitida';
  END IF;
  IF NEW.estado='Finalizado' AND (
    NOT EXISTS(SELECT 1 FROM registro_final WHERE numero_orden=NEW.numero_orden) OR
    EXISTS(SELECT 1 FROM detalle_orden_produccion d LEFT JOIN detalle_registro_final f
      USING(numero_orden,cod_producto) WHERE d.numero_orden=NEW.numero_orden AND f.cod_producto IS NULL)
  ) THEN RAISE EXCEPTION 'El cierre debe contener todos los productos'; END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS tr_proteger_produccion ON produccion;
CREATE TRIGGER tr_proteger_produccion BEFORE UPDATE OR DELETE ON produccion
FOR EACH ROW EXECUTE FUNCTION fn_proteger_produccion();

CREATE OR REPLACE FUNCTION fn_validar_resultado() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE plan integer; actual integer; state text;
BEGIN
  SELECT estado INTO state FROM produccion WHERE numero_orden=NEW.numero_orden FOR UPDATE;
  IF state <> 'En curso' THEN RAISE EXCEPTION 'El cierre requiere una orden en curso'; END IF;
  SELECT cant_programada INTO plan FROM detalle_orden_produccion
    WHERE numero_orden=NEW.numero_orden AND cod_producto=NEW.cod_producto;
  IF plan IS NULL OR NEW.cant_producida+NEW.cant_perdida <> plan THEN
    RAISE EXCEPTION 'Producida mas perdida debe ser igual a programada';
  END IF;
  SELECT stock INTO actual FROM producto WHERE cod_producto=NEW.cod_producto FOR UPDATE;
  IF actual+NEW.cant_producida > 999 THEN RAISE EXCEPTION 'Stock supera 999'; END IF;
  UPDATE producto SET stock=stock+NEW.cant_producida WHERE cod_producto=NEW.cod_producto;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS tr_validar_resultado ON detalle_registro_final;
CREATE TRIGGER tr_validar_resultado BEFORE INSERT ON detalle_registro_final
FOR EACH ROW EXECUTE FUNCTION fn_validar_resultado();

CREATE OR REPLACE FUNCTION fn_resultado_inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Un cierre registrado no puede modificarse ni eliminarse'; END $$;
DROP TRIGGER IF EXISTS tr_resultado_inmutable ON detalle_registro_final;
CREATE TRIGGER tr_resultado_inmutable BEFORE UPDATE OR DELETE ON detalle_registro_final
FOR EACH ROW EXECUTE FUNCTION fn_resultado_inmutable();
DROP TRIGGER IF EXISTS tr_cabecera_inmutable ON registro_final;
CREATE TRIGGER tr_cabecera_inmutable BEFORE UPDATE OR DELETE ON registro_final
FOR EACH ROW EXECUTE FUNCTION fn_resultado_inmutable();

CREATE OR REPLACE PROCEDURE sp_guardar_orden(INOUT p_numero text, IN p_fecha date,
  IN p_empleado text, IN p_lineas jsonb) LANGUAGE plpgsql AS $$
DECLARE state text;
BEGIN
  IF jsonb_typeof(p_lineas) <> 'array' OR jsonb_array_length(p_lineas)=0 THEN
    RAISE EXCEPTION 'Debe existir al menos un producto'; END IF;
  IF p_numero IS NULL THEN
    INSERT INTO produccion(fecha_prog,codigo_empleado) VALUES(p_fecha,p_empleado)
      RETURNING numero_orden INTO p_numero;
  ELSE
    SELECT estado INTO state FROM produccion WHERE numero_orden=p_numero FOR UPDATE;
    IF state IS DISTINCT FROM 'Pendiente' THEN RAISE EXCEPTION 'Solo se edita pendiente'; END IF;
    UPDATE produccion SET fecha_prog=p_fecha,codigo_empleado=p_empleado WHERE numero_orden=p_numero;
    DELETE FROM detalle_orden_produccion WHERE numero_orden=p_numero;
  END IF;
  INSERT INTO detalle_orden_produccion(numero_orden,cod_producto,cant_programada)
    SELECT p_numero,x->>'product',(x->>'quantity')::smallint FROM jsonb_array_elements(p_lineas) x;
END $$;

CREATE OR REPLACE PROCEDURE sp_cambiar_estado(IN p_numero text, IN p_destino text)
LANGUAGE plpgsql AS $$
DECLARE state text;
BEGIN
  SELECT estado INTO state FROM produccion WHERE numero_orden=p_numero FOR UPDATE;
  IF state IS DISTINCT FROM 'Pendiente' OR p_destino NOT IN ('En curso','Cancelado') THEN
    RAISE EXCEPTION 'Cambio de estado no permitido'; END IF;
  IF NOT EXISTS(SELECT 1 FROM detalle_orden_produccion WHERE numero_orden=p_numero) THEN
    RAISE EXCEPTION 'Orden vacia'; END IF;
  UPDATE produccion SET estado=p_destino WHERE numero_orden=p_numero;
END $$;

CREATE OR REPLACE PROCEDURE sp_eliminar_orden(IN p_numero text) LANGUAGE plpgsql AS $$
DECLARE state text;
BEGIN
  SELECT estado INTO state FROM produccion WHERE numero_orden=p_numero FOR UPDATE;
  IF state IS DISTINCT FROM 'Pendiente' THEN RAISE EXCEPTION 'Solo se elimina pendiente'; END IF;
  DELETE FROM detalle_orden_produccion WHERE numero_orden=p_numero;
  DELETE FROM produccion WHERE numero_orden=p_numero;
END $$;

CREATE OR REPLACE PROCEDURE sp_cerrar_orden(IN p_numero text, IN p_lineas jsonb)
LANGUAGE plpgsql AS $$
DECLARE state text; expected integer; received integer;
BEGIN
  SELECT estado INTO state FROM produccion WHERE numero_orden=p_numero FOR UPDATE;
  IF state IS DISTINCT FROM 'En curso' THEN RAISE EXCEPTION 'Solo se cierra en curso'; END IF;
  SELECT count(*) INTO expected FROM detalle_orden_produccion WHERE numero_orden=p_numero;
  SELECT count(DISTINCT x->>'product') INTO received FROM jsonb_array_elements(p_lineas) x;
  IF expected=0 OR received<>expected OR jsonb_array_length(p_lineas)<>expected THEN
    RAISE EXCEPTION 'El cierre debe contener todos los productos sin duplicados'; END IF;
  -- Bloqueo estable de inventario antes de ejecutar los triggers.
  PERFORM 1 FROM producto p JOIN detalle_orden_produccion d USING(cod_producto)
    WHERE d.numero_orden=p_numero ORDER BY p.cod_producto FOR UPDATE OF p;
  INSERT INTO registro_final(numero_orden,estado) VALUES(p_numero,
    CASE WHEN EXISTS(SELECT 1 FROM jsonb_array_elements(p_lineas) x WHERE (x->>'lost')::int>0)
      THEN 'Con merma' ELSE 'Conforme' END);
  INSERT INTO detalle_registro_final(numero_orden,cod_producto,cant_producida,cant_perdida,descripcion_perdida)
    SELECT p_numero,x->>'product',(x->>'produced')::smallint,(x->>'lost')::smallint,
      nullif(trim(x->>'reason'),'') FROM jsonb_array_elements(p_lineas) x ORDER BY x->>'product';
  UPDATE produccion SET estado='Finalizado' WHERE numero_orden=p_numero;
END $$;
COMMIT;
