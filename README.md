# Proyecto Final — Auditoría Transaccional para Prevención de Pérdidas en Retail

Este proyecto consiste en una solución analítica completa (Business Intelligence) orientada a la identificación de anomalías, velocidad de compra y patrones de riesgo en transacciones de retail utilizando un esquema estrella implementado en AWS Aurora PostgreSQL, un pipeline ETL en Python y consultas analíticas avanzadas.

## 📊 Resumen ejecutivo

| Campo | Valor |
|---|---|
| **Pregunta analítica** | ¿Cuáles son los patrones de comportamiento temporal, geográfico y de uso de cuentas que permiten identificar anomalías transaccionales y mitigar el riesgo de fraude en puntos de venta? |
| **Dataset** | Financial Fraud Detection Dataset — público (~100k registros en múltiples archivos relacionales) |
| **Fuente** | Kaggle (Aditya Goyal) |
| **Modelo** | Esquema estrella con 1 tabla de hechos y 3 dimensiones (Clientes, Comercios, Tiempo) |
| **Infraestructura** | Aurora PostgreSQL en AWS |
| **ETL** | `etl_pipeline.py` ejecutado de extremo a extremo con pandas + SQLAlchemy |
| **SQL avanzado** | Window functions (LAG para velocidad de compra, RANK para top fraude), CTEs para segmentación de riesgo, y agregaciones condicionales |
| **Dashboard** | Reporte interactivo con visualizaciones de métricas de riesgo y comportamiento anómalo |

## 🎯 Problema y motivación

En el sector retail, la prevención de pérdidas (Loss Prevention) y la mitigación de fraudes transaccionales en puntos de venta (POS) son críticas para proteger el margen operativo de las compañías. A diferencia de los enfoques tradicionales que evalúan transacciones de manera aislada, este proyecto implementa un enfoque de analítica de datos para identificar patrones complejos de comportamiento de riesgo, tales como:

- **Velocidad de compra extrema (Time-Delta):** Clientes o cuentas ejecutando transacciones sospechosamente rápidas en cortos periodos de tiempo.
- **Card Hopping / Multi-cuentas:** Un mismo identificador de "Guest" intentando asociar múltiples métodos de pago distintos en ventanas de tiempo críticas.
- **Concentración de anomalías:** Identificación de sucursales o categorías de comercio que desvían significativamente su comportamiento respecto al promedio de la cadena.

Este proyecto responde a tres preguntas de negocio concretas:
1. ¿Qué comercios o sucursales presentan los mayores niveles y montos de transacciones anómalas?
2. ¿Existen patrones horarios o estacionales donde la velocidad de compra o el riesgo transaccional se dispare?
3. ¿Cómo se distribuye el riesgo transaccional según el comportamiento y el saldo de las cuentas de los clientes?

## 🏗️ Arquitectura y Decisiones de Diseño

### 📈 Simulación de Escala mediante Data Augmentation (Generación Sintética)
Dado que el dataset original de Kaggle proveía una muestra limitada a 1,000 registros transaccionales (volumen insuficiente para evaluar el rendimiento real de un Data Warehouse en AWS Aurora), se implementó un algoritmo de **Data Augmentation** dentro de la fase de transformación del pipeline ETL. 

A través de un bucle multiplicador con desfase controlado (*Time-shifting* y *ID-scaling*), se expandió el volumen a **15,000 transacciones únicas**. Esta técnica se justifica bajo tres pilares de ingeniería:

1. **Stress Testing de la Infraestructura:** Permite validar el comportamiento de los índices creados en PostgreSQL y el tiempo de respuesta de las consultas bajo una carga volumétrica real.
2. **Realismo y Variabilidad Numérica:** El algoritmo aplica un factor de oscilación pseudoaleatoria a los montos (`TransactionAmount`) y propaga los timestamps a lo largo de 15 días consecutivos, simulando un histórico operativo real sin corromper los perfiles de los clientes existentes.
3. **Preservación de la Integridad Referencial:** La expansión ocurre de manera controlada garantizando que todas las llaves foráneas sigan apuntando correctamente a las dimensiones base (`Dim_Clientes` y `Dim_Comercios`).

## 📊 Capa de Visualización (Dashboard Interactivo)

El sistema analítico fue desarrollado utilizando **Streamlit** y **Plotly Express**, lo que permite una explotación dinámica de las 15,000 transacciones alojadas en AWS Aurora en lugar de reportes estáticos tradicionales.

### Evidencia de la Interfaz Analítica
![Monitoreo de Fraude en Retail](dashboard/dashboard_view.jpg)

### 🧠 Hallazgos Principales del Negocio
Tras la ejecución de las consultas de SQL avanzado y la exploración interactiva del portal de control, se identificaron los siguientes patrones críticos de riesgo operativo:

1. **Comercios Críticos (Vulnerabilidad POS):** El establecimiento denominado **Merchant 2583** se consolidó de manera aislada como el punto de venta más vulnerable de la cadena, encabezando las pérdidas financieras acumuladas por fraude con un impacto superior a los $1,450 USD. Las sucursales `Merchant 2328` y `Merchant 2022` completan el podio de riesgo transaccional, requiriendo auditorías urgentes sobre sus terminales físicas.
2. **Vectores de Ataque por Categoría:** La distribución de alertas de riesgo demostró que el fraude electrónico o digital (**Online**) representa la mayor amenaza activa con un **22.7%** de los incidentes totales. No obstante, el canal convencional físico (**Retail**) se mantiene peligrosamente cerca con un **20.8%**, lo que justifica plenamente la implementación de reglas automáticas de control por velocidad y multi-tarjeta en los puntos de cobro.