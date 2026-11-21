"""Metadatos de reportes. El SELECT de negocio reside en PostgreSQL.

Tupla: título, nombre fijo del procedimiento, requiere parámetro.
"""
REPORTS = [('Órdenes y responsables', 'sp_reporte_ordenes', False), ('Órdenes pendientes y en curso', 'sp_reporte_ordenes_activas', False), ('Productos programados en una orden', 'sp_reporte_productos_orden', True), ('Inventario y precio de productos', 'sp_reporte_inventario_productos', False), ('Existencias de ingredientes', 'sp_reporte_existencias_ingredientes', False), ('Ingredientes de una receta', 'sp_reporte_ingredientes_receta', True), ('Producción acumulada por producto', 'sp_reporte_produccion_acumulada', False), ('Comparación de programación y resultados', 'sp_reporte_programacion_resultados', False), ('Pérdidas y sus motivos', 'sp_reporte_perdidas', False), ('Historial de órdenes y cierres', 'sp_reporte_historial_cierres', False)]
