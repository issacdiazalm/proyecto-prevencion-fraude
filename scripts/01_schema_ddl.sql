-- ============================================================================
-- SCRIPT 01: CREACIÓN DEL MODELO DIMENSIONAL (STAR SCHEMA)
-- Proyecto: Prevención de Fraudes y Pérdidas en Retail
-- ============================================================================

-- 1. Crear el esquema del Data Warehouse
CREATE SCHEMA IF NOT EXISTS loss_prevention_dwh;

-- 2. Eliminar tablas si ya existen (Garantiza Idempotencia al recrear el esquema)
DROP TABLE IF EXISTS loss_prevention_dwh.fact_transacciones CASCADE;
DROP TABLE IF EXISTS loss_prevention_dwh.dim_clientes CASCADE;
DROP TABLE IF EXISTS loss_prevention_dwh.dim_comercios CASCADE;
DROP TABLE IF EXISTS loss_prevention_dwh.dim_tiempo CASCADE;

-- 3. Crear Dimensión de Clientes
-- Consolida: customer_data + account_activity + suspicious_activity
CREATE TABLE loss_prevention_dwh.dim_clientes (
    cliente_key SERIAL PRIMARY KEY,              -- Surrogate Key
    customer_id VARCHAR(50) NOT NULL UNIQUE,     -- Natural Key
    nombre VARCHAR(100),
    edad INT,
    direccion TEXT,
    saldo_cuenta NUMERIC(12, 2),
    ultimo_login TIMESTAMP,
    es_sospechoso INT                            -- 0 o 1 (Suspiciousflag)
);

-- 4. Crear Dimensión de Comercios (Merchants)
-- Consolida: merchant_data
CREATE TABLE loss_prevention_dwh.dim_comercios (
    comercio_key SERIAL PRIMARY KEY,             -- Surrogate Key
    merchant_id VARCHAR(50) NOT NULL UNIQUE,     -- Natural Key
    nombre_comercio VARCHAR(150),
    ubicacion VARCHAR(150)
);

-- 5. Crear Dimensión de Tiempo
-- Se genera en el ETL abstrayendo el Timestamp de transaction_metadata
CREATE TABLE loss_prevention_dwh.dim_tiempo (
    tiempo_key SERIAL PRIMARY KEY,               -- Surrogate Key
    fecha_completa TIMESTAMP NOT NULL,
    año INT NOT NULL,
    mes INT NOT NULL,
    dia INT NOT NULL,
    hora INT NOT NULL,
    minuto INT NOT NULL,
    dia_semana INT NOT NULL,                     -- 1 (Lunes) a 7 (Domingo)
    es_fin_de_semana BOOLEAN NOT NULL
);

-- 6. Crear Tabla de Hechos (Fact_Transacciones)
-- Consolida el átomo transaccional y sus métricas de riesgo:
-- transaction_records + transaction_metadata + amount_data + anomaly_scores + fraud_indicators + category_labels
CREATE TABLE loss_prevention_dwh.fact_transacciones (
    transaccion_key SERIAL PRIMARY KEY,          -- Llave primaria de la Fact
    transaction_id VARCHAR(50) NOT NULL,         -- ID de transacción de origen
    cliente_key INT NOT NULL,                    -- FK a Dim_Clientes
    comercio_key INT NOT NULL,                   -- FK a Dim_Comercios
    tiempo_key INT NOT NULL,                     -- FK a Dim_Tiempo
    monto NUMERIC(12, 2) NOT NULL,               -- Métricas financieras
    anomaly_score NUMERIC(6, 4),                 -- Métrica de riesgo (0.0000 a 1.0000)
    categoria VARCHAR(100),                      -- Atributo degenerado de la transacción
    es_fraude INT,                               -- Flag de fraude (0 o 1 de fraud_indicators)
    tarjeta_simulada_hash VARCHAR(64),           -- Campo calculado en Python para velocidad
    
    -- Restricciones de Llaves Foráneas (Integridad Referencial)
    CONSTRAINT fk_fact_clientes FOREIGN KEY (cliente_key) 
        REFERENCES loss_prevention_dwh.dim_clientes (cliente_key),
    CONSTRAINT fk_fact_comercios FOREIGN KEY (comercio_key) 
        REFERENCES loss_prevention_dwh.dim_comercios (comercio_key),
    CONSTRAINT fk_fact_tiempo FOREIGN KEY (tiempo_key) 
        REFERENCES loss_prevention_dwh.dim_tiempo (tiempo_key)
);

-- 7. Crear índices básicos para acelerar las consultas analíticas del Dashboard
CREATE INDEX idx_fact_cliente ON loss_prevention_dwh.fact_transacciones(cliente_key);
CREATE INDEX idx_fact_comercio ON loss_prevention_dwh.fact_transacciones(comercio_key);
CREATE INDEX idx_fact_tiempo ON loss_prevention_dwh.fact_transacciones(tiempo_key);