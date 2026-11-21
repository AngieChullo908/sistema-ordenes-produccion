-- A. Comprobar base y versión.
SELECT current_database() AS base, current_user AS usuario, version() AS version;

-- B. Deben aparecer las once tablas del proyecto.
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;

-- C. Recuento exacto de los datos de prueba.
SELECT 'empleado' AS tabla, count(*) AS registros FROM empleado
UNION ALL SELECT 'unidad_medida',count(*) FROM unidad_medida
UNION ALL SELECT 'categoria',count(*) FROM categoria
UNION ALL SELECT 'receta',count(*) FROM receta
UNION ALL SELECT 'ingrediente',count(*) FROM ingrediente
UNION ALL SELECT 'producto',count(*) FROM producto
UNION ALL SELECT 'produccion',count(*) FROM produccion
UNION ALL SELECT 'detalle_orden_produccion',count(*) FROM detalle_orden_produccion
UNION ALL SELECT 'registro_final',count(*) FROM registro_final
UNION ALL SELECT 'detalle_receta',count(*) FROM detalle_receta
UNION ALL SELECT 'detalle_registro_final',count(*) FROM detalle_registro_final
ORDER BY tabla;

-- D. Tamaño real de esta instalación, en bytes y formato legible.
SELECT current_database() AS base,
       pg_database_size(current_database()) AS bytes,
       pg_size_pretty(pg_database_size(current_database())) AS tamano;

-- E. Rutas relativas y tamaños. El total ya incluye los índices.
SELECT relname AS tabla, pg_relation_filepath(relid) AS ruta_relativa,
       pg_size_pretty(pg_table_size(relid)) AS datos_y_auxiliares,
       pg_size_pretty(pg_indexes_size(relid)) AS indices,
       pg_size_pretty(pg_total_relation_size(relid)) AS total
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY relname;

-- F. Índices, tanto automáticos como adicionales.
SELECT tablename,indexname,indexdef FROM pg_indexes
WHERE schemaname='public' ORDER BY tablename,indexname;

-- G. Proyección propuesta, no un tamaño de uso real.
SELECT 1 AS anos, 1365000 AS crecimiento_estimado_bytes,
       pg_database_size(current_database()) + 1365000 AS tamano_proyectado_bytes
UNION ALL
SELECT 2, 2730000, pg_database_size(current_database()) + 2730000
UNION ALL
SELECT 3, 4095000, pg_database_size(current_database()) + 4095000;
