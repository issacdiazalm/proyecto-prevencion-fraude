# 🛡️ Data Warehouse & Analytics para la Prevención de Fraudes en Retail

## 1. 📋 Resumen Ejecutivo

:information_source: Este proyecto final implementa una solución analítica de Business Intelligence (BI) de extremo a extremo para el monitoreo y prevención de fraudes transaccionales en el sector retail. Cubre el ciclo completo: desde la ingesta multi-fuente, modelado estrella, persistencia cloud en AWS, analítica SQL avanzada hasta la explotación visual interactiva.

| Campo | Valor |
| ------ | ------ |
| **Pregunta Analítica** | ¿Cuáles son los patrones temporales (horarios), las sucursales críticas y los perfiles transaccionales que concentran la mayor vulnerabilidad y pérdida financiera por fraude en la cadena retail? |
| **Dataset Base** | *Fraud Detection Dataset* (Fuentes operacionales relacionales fragmentadas recopiladas desde Kaggle) |
| **Volumen Analítico** | 1,000 registros base escalados programáticamente a **15,000 transacciones únicas** |
| **Modelo Dimensional** | Esquema Estrella con 1 Fact Table (`fact_transacciones`) y 3 Dimensiones desnormalizadas (`dim_clientes`, `dim_comercios`, `dim_tiempo`) |
| **Infraestructura** | AWS Aurora PostgreSQL Cloud Cluster (`aurora-mod4`, esquema `loss_prevention_dwh`) |
| **ETL Pipeline** | `scripts/etl_pipeline.py` automatizado de extremo a extremo, modular e idempotente (pandas + SQLAlchemy) |
| **SQL Avanzado** | Funciones de ventana analíticas (`LAG`), funciones de clasificación (`RANK`), Common Table Expressions (`CTEs`) y agregación condicional (`COUNT FILTER`) |
| **Dashboard** | Aplicación web interactiva nativa desarrollada en Python con **Streamlit** y **Plotly Express** |

## 🎯 Problema y Motivación (Business Case)
En la operación de retail moderno, las mermas derivadas de actividades fraudulentas en puntos de venta físicos (POS) y canales digitales representan impactos críticos sobre el margen de utilidad neta. Identificar estas anomalías de forma manual sobre bases transaccionales transitorias es inviable debido a la velocidad y el volumen de las operaciones. 

Este entorno analítico de Data Warehouse responde a tres dolores de cabeza del negocio:
1. **Velocidad de Compra (Clonación):** Detectar si una misma identidad de cliente está operando terminales distintas en intervalos de tiempo físicamente imposibles.
2. **Vulnerabilidad de Sucursales:** Identificar qué comercios específicos están registrando mermas financieras severas por fraudes confirmados para desplegar auditorías físicas.
3. **Comportamiento por Categoría:** Descubrir cuáles pasillos o modalidades de venta sufren la mayor tasa de incidencia criminal para ajustar las reglas automáticas de prevención de pérdidas.

---

## 📦 Arquitectura y Origen de los Datos (Flujo End-to-End)

Los datos crudos de origen emulan el ecosistema fragmentado de un sistema transaccional (OLTP). El pipeline ETL toma como insumos los siguientes archivos CSV heterogéneos alojados localmente dentro del directorio `/datasets`:
* `customer_data.csv` y `account_activity.csv` (Datos demográficos y financieros del cliente).
* `merchant_data.csv` y `transaction_category_labels.csv` (Metadatos de las sucursales y giros comerciales).
* `transaction_records.csv`, `transaction_metadata.csv`, `anomaly_scores.csv` y `amount_data.csv` (Métricas operacionales y scores de riesgo).
* `fraud_indicators.csv` y `suspicious_activity.csv` (Banderas e indicadores de auditoría).

### 🧠 Algoritmo de Escalamiento Volumétrico (Data Augmentation)
Dado que las muestras públicas de origen venían limitadas a 1,000 transacciones, se diseñó un motor de **Data Augmentation** programático dentro de la fase de transformación en Python. El algoritmo aplica un bucle multiplicador con desfases controlados (*Time-shifting* e *ID-scaling*), expandiendo el volumen analítico a **15,000 registros transaccionales únicos**. Esta técnica simula un entorno analítico corporativo de alta carga (*Stress Testing*) garantizando la variabilidad de montos, distribución temporal y la preservación absoluta de la integridad referencial.

---

## 📂 Estructura del Repositorio

El proyecto mantiene una estructura modular y limpia para garantizar la reproducibilidad completa del entorno analítico:

```text
proyecto-prevencion-fraude/
├── .gitignore                   # Excluye del control de versiones los CSVs operativos pesados
├── README.md                    # Portada, decisiones de diseño Kimball y hallazgos del negocio
├── datasets/                    # Carpeta local contenedora de los CSVs operativos crudos
│   ├── customer_data.csv
│   ├── account_activity.csv
│   ├── merchant_data.csv
│   ├── transaction_category_labels.csv
│   ├── transaction_records.csv
│   ├── transaction_metadata.csv
│   ├── anomaly_scores.csv
│   ├── amount_data.csv
│   ├── fraud_indicators.csv
│   └── suspicious_activity.csv
├── scripts/                     # Scripts de automatización de infraestructura e ingesta
│   ├── 01_schema_ddl.sql        # Definición del esquema e integridad relacional en AWS Aurora
│   └── etl_pipeline.py          # Código modular E-T-L y Data Augmentation en Python
├── analisis/                    # Capa analítica avanzada
│   └── queries_analiticas.sql   # Consultas de SQL avanzado optimizadas para PostgreSQL
└── dashboard/                   # Capa de Business Intelligence y Explotación
    ├── app.py                   # Aplicación interactiva con Streamlit y Plotly
    └── dashboard_view.jpg       # Evidencia gráfica del portal analítico funcionando

--- 
## 🛠️ Cómo Ejecutar e Instalar (Paso a Paso)

### 1. Preparación de la Infraestructura en AWS Aurora
Asume que se cuenta con el clúster cloud activo del diplomado (`aurora-mod4`). Desde tu cliente SQL (como **DBeaver**), abre una pestaña de consola conectada al clúster y ejecuta íntegramente el script `scripts/01_schema_ddl.sql`. Esto creará el esquema aislado `loss_prevention_dwh` y las cuatro tablas relacionales vacías con sus respectivas Primary Keys, Surrogate Keys e índices de optimización.

### 2. Configuración del Entorno de Python
Instala las librerías necesarias en tu sistema operativo ejecutando el siguiente comando en la terminal de tu Mac:
```bash
pip install pandas sqlalchemy psycopg2-binary streamlit plotly

## 2. Modelo Dimensional (Esquema Estrella)
Para optimizar las consultas analíticas del negocio y desacoplar la carga del entorno transaccional, se diseñó e implementó un **Esquema Estrella** compuesto por una tabla de hechos central y tres dimensiones desnormalizadas.

```text
                    +------------------------------------+
                    |            Dim_Clientes            |
                    +------------------------------------+
                    | PK  | cliente_key (Surrogate)      |
                    |     | customer_id (Natural)        |
                    |     | nombre, edad, saldo_cuenta   |
                    |     | es_sospechoso (Historial)    |
                    +------------------------------------+
                                      |
                                      | 1:N
                                      v
+------------------------------------+     +------------------------------------+
|           Dim_Comercios            |     |         Fact_Transacciones         |
+------------------------------------+     +------------------------------------+
| PK  | comercio_key (Surrogate)     |     | PK  | transaction_id               |
|     | merchant_id (Natural)        |---->| FK  | cliente_key                  |
|     | nombre_comercio, ubicacion   | 1:N | FK  | comercio_key                 |
+------------------------------------+     | FK  | tiempo_key                   |
                                           |     | monto, anomaly_score         |
                                           |     | es_fraude (Flag)             |
                                           |     | categoria (Degenerado)       |
                                           |     | tarjeta_simulada_hash        |
                                           +------------------------------------+
                                                              ^
                                                              | 1:N
                                                              |
                                           +------------------------------------+
                                           |             Dim_Tiempo             |
                                           +------------------------------------+
                                           | PK  | tiempo_key (Surrogate)       |
                                           |     | fecha_completa (Timestamp)   |
                                           |     | anio, mes, dia, hora, minuto |
                                           |     | dia_semana, es_fin_de_semana |
                                           +------------------------------------+
```
### 💡 Decisiones de Diseño Kimball
* **Grano de la Fact Table:** El átomo más fino disponible en el origen de datos es una fila por transacción individual única ejecutada en el ecosistema.
* **Separación de la Dimensión de Tiempo:** Siguiendo las mejores prácticas de modelado analítico, las marcas de tiempo se separaron en una dimensión ortogonal (`Dim_Tiempo`). Esto permite segmentar agregaciones complejas (como el comportamiento por turnos u horas pico) de forma independiente a los efectos estacionales del calendario (como días de pago o quincenas).
* **Manejo de Atributos Degenerados:** La columna `categoria` de la transacción viene vinculada directamente al identificador de la compra y no al comercio estable. Por ende, se modeló como un atributo degenerado dentro de la `Fact_Transacciones` para evitar joins innecesarios y optimizar el almacenamiento.

---

## ☁️ 3. Infraestructura Cloud (AWS Aurora)
El Data Warehouse analítico fue desplegado de manera exitosa en la nube utilizando un clúster de **AWS Aurora PostgreSQL** (`aurora-mod4`). 
* El diseño e integridad relacional fue inyectado en la instancia mediante el script estructurado de base de datos alojado en `scripts/01_schema_ddl.sql`.
* **Seguridad de Accesos:** En alineación estricta con las restricciones del Criterio 3, las credenciales de conexión del clúster (Host, Password) no fueron harcodeadas en texto plano en ningún archivo del código, mitigando vulnerabilidades críticas mediante el consumo dinámico de Variables de Entorno del sistema operativo.

---

## 🐍 4. Pipeline ETL Automatizado e Idempotente
El corazón del procesamiento de datos reside en el archivo modular `scripts/etl_pipeline.py`, el cual implementa las tres fases analíticas de forma agnóstica:

1. **Extract (Extracción Multi-fuente):** Consume de forma ordenada múltiples archivos CSV heterogéneos desde el directorio local `/datasets` utilizando pandas.
2. **Transform (Transformación Avanzada):** Ejecuta la limpieza de datos, resuelve conflictos de codificación no-ASCII (removiendo caracteres especiales como la letra Ñ en los metadatos de tiempo), y ejecuta el motor de *Data Augmentation* para escalar la métrica transaccional a 15,000 registros únicos con variabilidad pseudoaleatoria.
3. **Load (Carga e Idempotencia):** Establece el canal de comunicación seguro a través del motor SQLAlchemy. Para garantizar la **Idempotencia** obligatoria del pipeline, la función ejecuta un comando estructurado de `TRUNCATE TABLE ... CASCADE` previo a la carga, asegurando que el script pueda re-correrse un número infinito de veces sin duplicar llaves foráneas ni corromper el histórico del Data Warehouse.

---

## 🛡️ 5. Consultas Analíticas Avanzadas en SQL
Para dar cumplimiento y demostrar el dominio teórico de las técnicas de SQL Avanzado del diplomado, se desarrollaron cuatro consultas de negocio complejas almacenadas en `analisis/queries_analiticas.sql`, aplicando las siguientes metodologías:
* **Funciones de Ventana analíticas (`LAG`):** Utilizada en la auditoría de velocidad de compra (*Time-Delta*) para calcular de forma milimétrica los minutos transcurridos entre la transacción actual y la inmediata anterior realizada por el mismo cliente.
* **Funciones de Ventana de Clasificación (`RANK`) combinadas con CTEs:** Utilizada para aislar y construir el podio financiero de las sucursales con mayores pérdidas económicas derivadas de fraudes confirmados.
* **Agregación Condicional Avanzada (Cláusula `FILTER`):** Implementada para calcular la tasa porcentual de bateo y efectividad del fraude por categorías comerciales directamente sobre el flujo de los datos agrupados de PostgreSQL.

---

## 📊 6. Visualización Interactiva (Streamlit Portal)
El sistema analítico concluye con una interfaz web dinámica desarrollada con **Streamlit** y **Plotly Express**, conectada en tiempo real mediante SSL a la nube de AWS Aurora.

### Evidencia de la Interfaz Analítica
![Monitoreo de Fraude en Retail](dashboard/dashboard_view..png)

### 🧠 Conclusiones y Hallazgos Principales del Negocio
A través de la explotación interactiva del portal y la segmentación por parámetros de auditoría, se extrajeron dos descubrimientos de alto valor para la toma de decisiones estratégicas:
1. **Puntos de Venta Críticos:** El establecimiento comercial identificado como **Merchant 2583** se consolidó de forma aislada como el punto físico más vulnerable de la cadena corporativa, liderando las pérdidas financieras acumuladas por fraude con un impacto superior a los **$1,450 USD**. Esto gatilla la necesidad de ejecutar una auditoría física inmediata sobre las terminales de dicha sucursal.
2. **Vectores de Ataque Predominantes:** El análisis demostró que el canal digital (**Online**) representa el mayor riesgo activo concentrando el **22.7%** de los incidentes de fraude. No obstante, el canal convencional (**Retail**) se mantiene críticamente cerca con un **20.8%**, validando plenamente la urgencia de implementar controles automáticos de velocidad en los puntos de cobro físicos para mitigar el uso repetido de plásticos clonados.


