-- CONSULTA 1. Órdenes y responsables
SELECT p.numero_orden, p.fecha_prog, e.nombre_empleado, p.estado
FROM produccion p
INNER JOIN empleado e ON p.codigo_empleado = e.codigo_empleado
ORDER BY p.fecha_prog;

-- CONSULTA 2. Órdenes pendientes y en curso
SELECT p.numero_orden, p.fecha_prog, e.nombre_empleado, p.estado
FROM produccion p
INNER JOIN empleado e ON p.codigo_empleado = e.codigo_empleado
WHERE p.estado IN ('Pendiente', 'En curso')
ORDER BY p.fecha_prog;

-- CONSULTA 3. Productos programados en una orden
SELECT d.numero_orden, p.nombre_producto, d.cant_programada
FROM detalle_orden_produccion d
INNER JOIN producto p ON d.cod_producto = p.cod_producto
WHERE d.numero_orden = 'OP000010'
ORDER BY p.nombre_producto;

-- CONSULTA 4. Inventario y precio de productos
SELECT p.cod_producto, p.nombre_producto, c.nombre_categoria,
       p.stock, u.simbolo, p.precio
FROM producto p
INNER JOIN categoria c ON p.cod_categoria = c.cod_categoria
INNER JOIN unidad_medida u ON p.cod_unidad_medida = u.cod_unidad
ORDER BY c.nombre_categoria, p.nombre_producto;

-- CONSULTA 5. Existencias de ingredientes
SELECT i.cod_ingrediente, i.nombre_ingredientes,
       i.stock_ingrediente, u.nombre_unidad, u.simbolo
FROM ingrediente i
INNER JOIN unidad_medida u ON i.cod_unidad_medida_ingrediente = u.cod_unidad
ORDER BY i.nombre_ingredientes;

-- CONSULTA 6. Ingredientes de una receta
SELECT d.cod_receta, i.nombre_ingredientes, d.cant_requerida, u.simbolo
FROM detalle_receta d
INNER JOIN ingrediente i ON d.cod_ingrediente = i.cod_ingrediente
INNER JOIN unidad_medida u ON d.cod_unidad_medida_receta = u.cod_unidad
WHERE d.cod_receta = 'R001'
ORDER BY i.nombre_ingredientes;

-- CONSULTA 7. Producción acumulada por producto
SELECT p.cod_producto, p.nombre_producto,
       SUM(d.cant_producida) AS total_producido
FROM detalle_registro_final d
INNER JOIN producto p ON d.cod_producto = p.cod_producto
GROUP BY p.cod_producto, p.nombre_producto
ORDER BY total_producido DESC;

-- CONSULTA 8. Comparación de programación y resultados
SELECT o.numero_orden, p.nombre_producto, o.cant_programada,
       r.cant_producida, r.cant_perdida
FROM detalle_orden_produccion o
INNER JOIN detalle_registro_final r
    ON o.numero_orden = r.numero_orden AND o.cod_producto = r.cod_producto
INNER JOIN producto p ON o.cod_producto = p.cod_producto
ORDER BY o.numero_orden, p.nombre_producto;

-- CONSULTA 9. Pérdidas y sus motivos
SELECT o.numero_orden, o.fecha_prog, p.nombre_producto,
       d.cant_perdida, d.descripcion_perdida
FROM detalle_registro_final d
INNER JOIN produccion o ON d.numero_orden = o.numero_orden
INNER JOIN producto p ON d.cod_producto = p.cod_producto
WHERE d.cant_perdida > 0
ORDER BY o.fecha_prog, p.nombre_producto;

-- CONSULTA 10. Historial de órdenes y cierres
SELECT p.numero_orden, p.fecha_prog, e.nombre_empleado,
       p.estado AS estado_orden, r.estado AS resultado_cierre
FROM produccion p
INNER JOIN empleado e ON p.codigo_empleado = e.codigo_empleado
LEFT JOIN registro_final r ON p.numero_orden = r.numero_orden
ORDER BY p.fecha_prog;
