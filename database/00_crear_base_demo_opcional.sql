-- OPCIONAL. Ejecutar conectado a postgres, fuera de una transacción explícita.
-- Luego abrir Query Tool en avecesar_demo y ejecutar 01, 02, 05, 06 y 07.
-- No se borra ni sustituye la base avecesar_produccion.
CREATE DATABASE avecesar_demo WITH ENCODING='UTF8' TEMPLATE=template0;
