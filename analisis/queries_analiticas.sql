-- =====================================================================
-- CONSULTAS DE SQL AVANZADO (PREVENCIÓN DE FRAUDES)
-- =====================================================================

-- 1. VELOCIDAD DE COMPRA (Técnica: Función de Ventana LAG)
SELECT 
    f.transaction_id,
    c.customer_id,
    m.nombre_comercio,
    t.fecha_completa, 
    f.monto,
    -- Traemos la fecha de la transacción anterior del mismo cliente
    LAG(t.fecha_completa) OVER(PARTITION BY c.customer_id ORDER BY t.fecha_completa) as fecha_transaccion_anterior,
    -- Calculamos la diferencia en minutos
    EXTRACT(EPOCH FROM (t.fecha_completa - LAG(t.fecha_completa) OVER(PARTITION BY c.customer_id ORDER BY t.fecha_completa))) / 60 as minutos_desde_ultima_compra
FROM loss_prevention_dwh.fact_transacciones f
JOIN loss_prevention_dwh.dim_clientes c ON f.cliente_key = c.cliente_key
JOIN loss_prevention_dwh.dim_comercios m ON f.comercio_key = m.comercio_key
JOIN loss_prevention_dwh.dim_tiempo t ON f.tiempo_key = t.tiempo_key 
ORDER BY c.customer_id, t.fecha_completa
LIMIT 100;

-- 2. TOP 5 COMERCIOS VULNERABLES (Técnicas: CTE + Función de Ventana RANK)
WITH PerdidasPorComercio AS (
    SELECT 
        c.nombre_comercio,
        c.ubicacion,
        SUM(f.monto) FILTER (WHERE f.es_fraude = 1) as total_perdido_fraude,
        COUNT(f.transaccion_key) as transacciones_totales
    FROM loss_prevention_dwh.fact_transacciones f
    JOIN loss_prevention_dwh.dim_comercios c ON f.comercio_key = c.comercio_key
    GROUP BY c.nombre_comercio, c.ubicacion
)
SELECT 
    nombre_comercio,
    ubicacion,
    total_perdido_fraude,
    transacciones_totales,
    RANK() OVER (ORDER BY total_perdido_fraude DESC) as ranking_riesgo
FROM PerdidasPorComercio
WHERE total_perdido_fraude IS NOT NULL
LIMIT 5;

-- 3. IMPACTO DE FRAUDE POR CATEGORÍA (Técnica: Agregación Condicional COUNT FILTER)
SELECT 
    categoria,
    COUNT(transaccion_key) as transacciones_totales,
    COUNT(transaccion_key) FILTER (WHERE es_fraude = 1) as fraudes_detectados,
    ROUND(
        (COUNT(transaccion_key) FILTER (WHERE es_fraude = 1)::NUMERIC / COUNT(transaccion_key)) * 100, 
        2
    ) as porcentaje_efectivo_fraude
FROM loss_prevention_dwh.fact_transacciones
GROUP BY categoria
ORDER BY porcentaje_efectivo_fraude DESC;