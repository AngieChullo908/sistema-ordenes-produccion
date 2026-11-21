-- AVECESAR 1.1.0. Ejecutar TODO sobre la base existente después de 05.
-- Solo crea o reemplaza procedimientos de consulta. No cambia datos ni secuencias.
-- Cada procedimiento abre un refcursor; CALL y FETCH deben compartir transacción.
BEGIN;

CREATE OR REPLACE PROCEDURE public.sp_listar_empleados(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT * FROM empleado ORDER BY nombre_empleado;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_listar_productos(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.*, u.simbolo, c.nombre_categoria, r.nombre_receta, r.preparacion
                    FROM producto p JOIN unidad_medida u ON u.cod_unidad=p.cod_unidad_medida
                    JOIN categoria c USING(cod_categoria) JOIN receta r USING(cod_receta)
                    ORDER BY p.nombre_producto;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_listar_ingredientes(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT i.*, u.simbolo FROM ingrediente i
                    JOIN unidad_medida u ON u.cod_unidad=i.cod_unidad_medida_ingrediente
                    ORDER BY i.nombre_ingredientes;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_listar_ordenes(IN p_busqueda text, IN p_estado text, INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.numero_orden,p.fecha_prog,e.nombre_empleado,p.estado,
                count(d.cod_producto) AS productos,coalesce(sum(d.cant_programada),0) AS unidades
                FROM produccion p JOIN empleado e USING(codigo_empleado)
                LEFT JOIN detalle_orden_produccion d USING(numero_orden)
                WHERE (p_estado='Todos' OR p.estado=p_estado) AND
                (p.numero_orden ILIKE '%' || p_busqueda || '%' OR e.nombre_empleado ILIKE '%' || p_busqueda || '%')
                GROUP BY p.numero_orden,e.nombre_empleado ORDER BY p.fecha_prog DESC,p.numero_orden DESC;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_consultar_orden(IN p_numero text, INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.*,e.nombre_empleado,e.cargo_empleado,r.estado AS resultado
                FROM produccion p JOIN empleado e USING(codigo_empleado)
                LEFT JOIN registro_final r USING(numero_orden) WHERE numero_orden=p_numero;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_consultar_detalle_orden(IN p_numero text, INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT d.*,p.nombre_producto,f.cant_producida,f.cant_perdida,f.descripcion_perdida
                FROM detalle_orden_produccion d JOIN producto p USING(cod_producto)
                LEFT JOIN detalle_registro_final f USING(numero_orden,cod_producto)
                WHERE numero_orden=p_numero ORDER BY cod_producto;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_consultar_receta(IN p_receta text, INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT i.nombre_ingredientes,d.cant_requerida,u.simbolo,
                i.stock_ingrediente,s.simbolo AS unidad_stock
                FROM detalle_receta d JOIN ingrediente i USING(cod_ingrediente)
                JOIN unidad_medida u ON u.cod_unidad=d.cod_unidad_medida_receta
                JOIN unidad_medida s ON s.cod_unidad=i.cod_unidad_medida_ingrediente
                WHERE cod_receta=p_receta ORDER BY i.cod_ingrediente;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_ordenes(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.numero_orden, p.fecha_prog, e.nombre_empleado, p.estado
FROM produccion p
INNER JOIN empleado e ON p.codigo_empleado = e.codigo_empleado
ORDER BY p.fecha_prog;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_ordenes_activas(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.numero_orden, p.fecha_prog, e.nombre_empleado, p.estado
FROM produccion p
INNER JOIN empleado e ON p.codigo_empleado = e.codigo_empleado
WHERE p.estado IN ('Pendiente', 'En curso')
ORDER BY p.fecha_prog;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_productos_orden(IN p_numero text, INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT d.numero_orden, p.nombre_producto, d.cant_programada
FROM detalle_orden_produccion d
INNER JOIN producto p ON d.cod_producto = p.cod_producto
WHERE d.numero_orden = p_numero
ORDER BY p.nombre_producto;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_inventario_productos(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.cod_producto, p.nombre_producto, c.nombre_categoria,
       p.stock, u.simbolo, p.precio
FROM producto p
INNER JOIN categoria c ON p.cod_categoria = c.cod_categoria
INNER JOIN unidad_medida u ON p.cod_unidad_medida = u.cod_unidad
ORDER BY c.nombre_categoria, p.nombre_producto;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_existencias_ingredientes(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT i.cod_ingrediente, i.nombre_ingredientes,
       i.stock_ingrediente, u.nombre_unidad, u.simbolo
FROM ingrediente i
INNER JOIN unidad_medida u ON i.cod_unidad_medida_ingrediente = u.cod_unidad
ORDER BY i.nombre_ingredientes;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_ingredientes_receta(IN p_receta text, INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT d.cod_receta, i.nombre_ingredientes, d.cant_requerida, u.simbolo
FROM detalle_receta d
INNER JOIN ingrediente i ON d.cod_ingrediente = i.cod_ingrediente
INNER JOIN unidad_medida u ON d.cod_unidad_medida_receta = u.cod_unidad
WHERE d.cod_receta = p_receta
ORDER BY i.nombre_ingredientes;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_produccion_acumulada(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.cod_producto, p.nombre_producto,
       SUM(d.cant_producida) AS total_producido
FROM detalle_registro_final d
INNER JOIN producto p ON d.cod_producto = p.cod_producto
GROUP BY p.cod_producto, p.nombre_producto
ORDER BY total_producido DESC;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_programacion_resultados(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT o.numero_orden, p.nombre_producto, o.cant_programada,
       r.cant_producida, r.cant_perdida
FROM detalle_orden_produccion o
INNER JOIN detalle_registro_final r
    ON o.numero_orden = r.numero_orden AND o.cod_producto = r.cod_producto
INNER JOIN producto p ON o.cod_producto = p.cod_producto
ORDER BY o.numero_orden, p.nombre_producto;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_perdidas(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT o.numero_orden, o.fecha_prog, p.nombre_producto,
       d.cant_perdida, d.descripcion_perdida
FROM detalle_registro_final d
INNER JOIN produccion o ON d.numero_orden = o.numero_orden
INNER JOIN producto p ON d.cod_producto = p.cod_producto
WHERE d.cant_perdida > 0
ORDER BY o.fecha_prog, p.nombre_producto;
END;
$procedure$;

CREATE OR REPLACE PROCEDURE public.sp_reporte_historial_cierres(INOUT p_cursor refcursor)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $procedure$
BEGIN
    OPEN p_cursor FOR
    SELECT p.numero_orden, p.fecha_prog, e.nombre_empleado,
       p.estado AS estado_orden, r.estado AS resultado_cierre
FROM produccion p
INNER JOIN empleado e ON p.codigo_empleado = e.codigo_empleado
LEFT JOIN registro_final r ON p.numero_orden = r.numero_orden
ORDER BY p.fecha_prog;
END;
$procedure$;

COMMIT;

-- Ejemplo para ejecutar por separado después de instalar:
-- BEGIN;
-- CALL public.sp_reporte_productos_orden('OP000010','reporte_demo');
-- FETCH ALL FROM reporte_demo;
-- COMMIT;
