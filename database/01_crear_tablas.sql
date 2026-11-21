CREATE SEQUENCE empleado_codigo_seq
    START WITH 1 MINVALUE 1 MAXVALUE 99 NO CYCLE;

CREATE SEQUENCE unidad_medida_codigo_seq
    START WITH 1 MINVALUE 1 MAXVALUE 9 NO CYCLE;

CREATE SEQUENCE categoria_codigo_seq
    START WITH 1 MINVALUE 1 MAXVALUE 9 NO CYCLE;

CREATE SEQUENCE receta_codigo_seq
    START WITH 1 MINVALUE 1 MAXVALUE 99 NO CYCLE;

CREATE SEQUENCE ingrediente_codigo_seq
    START WITH 1 MINVALUE 1 MAXVALUE 99 NO CYCLE;

CREATE SEQUENCE producto_codigo_seq
    START WITH 1 MINVALUE 1 MAXVALUE 99 NO CYCLE;

CREATE SEQUENCE produccion_numero_seq
    START WITH 1 MINVALUE 1 MAXVALUE 999999 NO CYCLE;

CREATE TABLE empleado (
    codigo_empleado VARCHAR(4) PRIMARY KEY
        DEFAULT ('E' || LPAD(nextval('empleado_codigo_seq')::TEXT, 3, '0'))
        CHECK (codigo_empleado SIMILAR TO 'E[0-9]{3}' AND codigo_empleado <> 'E000'),
    nombre_empleado VARCHAR(30) NOT NULL CHECK (TRIM(nombre_empleado) <> ''),
    cargo_empleado VARCHAR(15) NOT NULL CHECK (TRIM(cargo_empleado) <> '')
);

CREATE TABLE unidad_medida (
    cod_unidad VARCHAR(4) PRIMARY KEY
        DEFAULT ('U' || LPAD(nextval('unidad_medida_codigo_seq')::TEXT, 3, '0'))
        CHECK (cod_unidad SIMILAR TO 'U[0-9]{3}' AND cod_unidad <> 'U000'),
    nombre_unidad VARCHAR(9) NOT NULL UNIQUE CHECK (TRIM(nombre_unidad) <> ''),
    simbolo VARCHAR(2) NOT NULL UNIQUE CHECK (TRIM(simbolo) <> '')
);

CREATE TABLE categoria (
    cod_categoria VARCHAR(4) PRIMARY KEY
        DEFAULT ('C' || LPAD(nextval('categoria_codigo_seq')::TEXT, 3, '0'))
        CHECK (cod_categoria SIMILAR TO 'C[0-9]{3}' AND cod_categoria <> 'C000'),
    nombre_categoria VARCHAR(15) NOT NULL UNIQUE CHECK (TRIM(nombre_categoria) <> '')
);

CREATE TABLE receta (
    cod_receta VARCHAR(4) PRIMARY KEY
        DEFAULT ('R' || LPAD(nextval('receta_codigo_seq')::TEXT, 3, '0'))
        CHECK (cod_receta SIMILAR TO 'R[0-9]{3}' AND cod_receta <> 'R000'),
    nombre_receta VARCHAR(50) NOT NULL CHECK (TRIM(nombre_receta) <> ''),
    preparacion VARCHAR(2000) NOT NULL CHECK (TRIM(preparacion) <> '')
);

CREATE TABLE ingrediente (
    cod_ingrediente VARCHAR(4) PRIMARY KEY
        DEFAULT ('I' || LPAD(nextval('ingrediente_codigo_seq')::TEXT, 3, '0'))
        CHECK (cod_ingrediente SIMILAR TO 'I[0-9]{3}' AND cod_ingrediente <> 'I000'),
    nombre_ingredientes VARCHAR(30) NOT NULL CHECK (TRIM(nombre_ingredientes) <> ''),
    cod_unidad_medida_ingrediente VARCHAR(4) NOT NULL,
    stock_ingrediente NUMERIC(6,3) NOT NULL DEFAULT 0 CHECK (stock_ingrediente BETWEEN 0 AND 999.999),
    FOREIGN KEY (cod_unidad_medida_ingrediente) REFERENCES unidad_medida(cod_unidad)
);

CREATE TABLE producto (
    cod_producto VARCHAR(4) PRIMARY KEY
        DEFAULT ('P' || LPAD(nextval('producto_codigo_seq')::TEXT, 3, '0'))
        CHECK (cod_producto SIMILAR TO 'P[0-9]{3}' AND cod_producto <> 'P000'),
    nombre_producto VARCHAR(30) NOT NULL CHECK (TRIM(nombre_producto) <> ''),
    cod_unidad_medida VARCHAR(4) NOT NULL,
    stock SMALLINT NOT NULL DEFAULT 0 CHECK (stock BETWEEN 0 AND 999),
    cod_categoria VARCHAR(4) NOT NULL,
    precio NUMERIC(5,2) NOT NULL CHECK (precio BETWEEN 0.01 AND 999.99),
    cod_receta VARCHAR(4) NOT NULL UNIQUE,
    FOREIGN KEY (cod_unidad_medida) REFERENCES unidad_medida(cod_unidad),
    FOREIGN KEY (cod_categoria) REFERENCES categoria(cod_categoria),
    FOREIGN KEY (cod_receta) REFERENCES receta(cod_receta)
);

CREATE TABLE produccion (
    numero_orden VARCHAR(8) PRIMARY KEY
        DEFAULT ('OP' || LPAD(nextval('produccion_numero_seq')::TEXT, 6, '0'))
        CHECK (numero_orden SIMILAR TO 'OP[0-9]{6}' AND numero_orden <> 'OP000000'),
    fecha_prog DATE NOT NULL,
    codigo_empleado VARCHAR(4) NOT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado IN ('Pendiente', 'En curso', 'Finalizado', 'Cancelado')),
    FOREIGN KEY (codigo_empleado) REFERENCES empleado(codigo_empleado)
);

CREATE TABLE detalle_orden_produccion (
    numero_orden VARCHAR(8),
    cod_producto VARCHAR(4),
    cant_programada SMALLINT NOT NULL CHECK (cant_programada BETWEEN 1 AND 999),
    PRIMARY KEY (numero_orden, cod_producto),
    FOREIGN KEY (numero_orden) REFERENCES produccion(numero_orden),
    FOREIGN KEY (cod_producto) REFERENCES producto(cod_producto)
);

CREATE TABLE registro_final (
    numero_orden VARCHAR(8) PRIMARY KEY,
    estado VARCHAR(11) NOT NULL CHECK (estado IN ('Conforme', 'Con merma')),
    FOREIGN KEY (numero_orden) REFERENCES produccion(numero_orden)
);

CREATE TABLE detalle_receta (
    cod_receta VARCHAR(4),
    cod_ingrediente VARCHAR(4),
    cant_requerida NUMERIC(5,2) NOT NULL CHECK (cant_requerida BETWEEN 0.01 AND 999.99),
    cod_unidad_medida_receta VARCHAR(4) NOT NULL,
    PRIMARY KEY (cod_receta, cod_ingrediente),
    FOREIGN KEY (cod_receta) REFERENCES receta(cod_receta),
    FOREIGN KEY (cod_ingrediente) REFERENCES ingrediente(cod_ingrediente),
    FOREIGN KEY (cod_unidad_medida_receta) REFERENCES unidad_medida(cod_unidad)
);

CREATE TABLE detalle_registro_final (
    numero_orden VARCHAR(8),
    cod_producto VARCHAR(4),
    descripcion_perdida VARCHAR(80),
    cant_producida SMALLINT NOT NULL CHECK (cant_producida BETWEEN 0 AND 999),
    cant_perdida SMALLINT NOT NULL DEFAULT 0 CHECK (cant_perdida BETWEEN 0 AND 999),
    PRIMARY KEY (numero_orden, cod_producto),
    FOREIGN KEY (numero_orden) REFERENCES registro_final(numero_orden),
    FOREIGN KEY (cod_producto) REFERENCES producto(cod_producto),
    FOREIGN KEY (numero_orden, cod_producto)
        REFERENCES detalle_orden_produccion(numero_orden, cod_producto),
    CHECK (
        (cant_perdida = 0 AND descripcion_perdida IS NULL)
        OR (cant_perdida > 0 AND descripcion_perdida IS NOT NULL
            AND TRIM(descripcion_perdida) <> '')
    )
);


CREATE INDEX idx_producto_nombre ON producto(nombre_producto);
CREATE INDEX idx_produccion_empleado ON produccion(codigo_empleado);
CREATE INDEX idx_receta_nombre ON receta(nombre_receta);
CREATE INDEX Idx_ingrediente_nombre ON ingrediente(nombre_ingredientes);
