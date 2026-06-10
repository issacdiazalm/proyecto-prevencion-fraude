print("--- SCRIPT EN EJECUCIÓN ---")
import os
import pandas as pd
from sqlalchemy import create_engine, text
import hashlib

# Configuraccion de acceso 
DB_USER = os.environ.get("AWS_DB_USER", "postgres")
DB_PASS = os.environ.get("AWS_DB_PASS")  # Sin valor por defecto por seguridad
DB_HOST = os.environ.get("AWS_DB_HOST", "aurora-mod4.cluster-cido1i6sg4cb.us-east-1.rds.amazonaws.com")
DB_PORT = os.environ.get("AWS_DB_PORT", "5432")
DB_NAME = os.environ.get("AWS_DB_NAME", "northwind")    

def get_db_engine():
    """Crea la conexión hacia el clúster de AWS Aurora PostgreSQL."""
    connection_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def extract_data():
    """
    FASE 1: EXTRACT
    Lee todos los archivos CSV desde la carpeta relacional /datasets.
    """
    print("🚀 Iniciando fase de Extracción...")
    
    try:
        # 1. Customer Profiles
        df_customer = pd.read_csv("datasets/customer_data.csv")
        df_activity = pd.read_csv("datasets/account_activity.csv")
        
        # 2. Fraudulent Patterns
        df_fraud_indicators = pd.read_csv("datasets/fraud_indicators.csv")
        df_suspicious = pd.read_csv("datasets/suspicious_activity.csv")
        
        # 3. Merchant Information
        df_merchant = pd.read_csv("datasets/merchant_data.csv")
        df_category = pd.read_csv("datasets/transaction_category_labels.csv")
        
        # 4. Transaction Amounts & Data
        df_amount = pd.read_csv("datasets/amount_data.csv")
        df_anomaly = pd.read_csv("datasets/anomaly_scores.csv")
        df_records = pd.read_csv("datasets/transaction_records.csv")
        df_metadata = pd.read_csv("datasets/transaction_metadata.csv")
        
        print("✅ Todos los archivos CSV fueron extraídos exitosamente.")
        
        # Retornamos un diccionario con todos los DataFrames para pasarlos a la transformación
        return {
            "customer": df_customer, "activity": df_activity,
            "fraud_indicators": df_fraud_indicators, "suspicious": df_suspicious,
            "merchant": df_merchant, "category": df_category,
            "amount": df_amount, "anomaly": df_anomaly,
            "records": df_records, "metadata": df_metadata
        }
        
    except FileNotFoundError as e:
        print(f"❌ Error en la extracción: No se encontró un archivo. Detalle: {e}")
        raise e

def transform_data(extracted_data):
    """
    FASE 2: TRANSFORM
    Cruza los datasets operacionales, genera dimensiones/hechos y aplica reglas de negocio.
    Implementa Data Augmentation para escalar el volumen a 15,000 registros.
    """
    print("🧠 Iniciando fase de Transformación con Data Augmentation...")
    
    # Desempaquetar los DataFrames del diccionario
    df_cust = extracted_data["customer"]
    df_act = extracted_data["activity"]
    df_susp = extracted_data["suspicious"]
    df_merch = extracted_data["merchant"]
    df_cat = extracted_data["category"]
    df_amt = extracted_data["amount"]
    df_anom = extracted_data["anomaly"]
    df_rec = extracted_data["records"]
    df_meta = extracted_data["metadata"]
    df_fraud = extracted_data["fraud_indicators"]

    # 1. CONSTRUIR DIM_CLIENTES
    print("   -> Modelando Dim_Clientes...")
    dim_clientes = df_cust.merge(df_act, on="CustomerID", how="left")
    dim_clientes = dim_clientes.merge(df_susp, on="CustomerID", how="left")
    
    dim_clientes = dim_clientes.rename(columns={
        "CustomerID": "customer_id", "customerid": "customer_id",
        "Name": "nombre", "Age": "edad", "Address": "direccion",
        "accountbalance": "saldo_cuenta", "AccountBalance": "saldo_cuenta",
        "lastlogin": "ultimo_login", "LastLogin": "ultimo_login",
        "Suspiciousflag": "es_sospechoso", "SuspiciousFlag": "es_sospechoso", "suspiciousflag": "es_sospechoso"
    })
    dim_clientes["es_sospechoso"] = dim_clientes["es_sospechoso"].fillna(0).astype(int)

    # 2. CONSTRUIR DIM_COMERCIOS
    print("   -> Modelando Dim_Comercios...")
    dim_comercios = df_merch.rename(columns={
        "MerchantID": "merchant_id", "MerchantName": "nombre_comercio", "Location": "ubicacion"
    })

    # 3. UNIFICAR NÚCLEO TRANSACCIONAL BASE
    print("   -> Unificando datos transaccionales base...")
    fact_base = df_rec.merge(df_meta, on="TransactionID", how="left")
    fact_base = fact_base.merge(df_amt, on="TransactionID", how="left")
    fact_base = fact_base.merge(df_anom, on="TransactionID", how="left")
    fact_base = fact_base.merge(df_fraud, on="TransactionID", how="left")
    fact_base = fact_base.merge(df_cat, on="TransactionID", how="left")
    
    fact_base["Timestamp"] = pd.to_datetime(fact_base["Timestamp"])

    # 🚀 ALGORITMO DE DATA AUGMENTATION (Multiplicar 1,000 x 15 = 15,000 filas)
    print("   -> 🚀 Ejecutando algoritmo de escalamiento volumétrico (Meta: 15,000 filas)...")
    fact_augmented = []
    
    for i in range(15):
        df_temp = fact_base.copy()
        # Modificar TransactionID de forma secuencial para evitar duplicación de llaves operacionales
        df_temp["TransactionID"] = df_temp["TransactionID"] + (i * 50000)
        # Desfasar el tiempo 'i' días hacia el futuro para crear una ventana temporal real de 2 semanas
        df_temp["Timestamp"] = df_temp["Timestamp"] + pd.to_timedelta(i, unit='D')
        # Alterar levemente los montos (+0.5% por iteración) para meter variabilidad financiera real
        df_temp["TransactionAmount"] = df_temp["TransactionAmount"] * (1 + (i * 0.005))
        fact_augmented.append(df_temp)
        
    fact_completa = pd.concat(fact_augmented, ignore_index=True)

    # 4. CONSTRUIR DIM_TIEMPO (Basado en el universo expandido de fechas)
    print("   -> Modelando Dim_Tiempo expandido...")
    unique_timestamps = pd.DataFrame({"fecha_completa": fact_completa["Timestamp"].unique()})
    
    dim_tiempo = pd.DataFrame()
    dim_tiempo["fecha_completa"] = unique_timestamps["fecha_completa"]
    dim_tiempo["anio"] = dim_tiempo["fecha_completa"].dt.year
    dim_tiempo["mes"] = dim_tiempo["fecha_completa"].dt.month
    dim_tiempo["dia"] = dim_tiempo["fecha_completa"].dt.day
    dim_tiempo["hora"] = dim_tiempo["fecha_completa"].dt.hour
    dim_tiempo["minuto"] = dim_tiempo["fecha_completa"].dt.minute
    dim_tiempo["dia_semana"] = dim_tiempo["fecha_completa"].dt.dayofweek + 1
    dim_tiempo["es_fin_de_semana"] = dim_tiempo["dia_semana"].isin([6, 7])

    # 5. REGLA DE NEGOCIO: Simulación de tarjetas de crédito
    import hashlib
    def generar_tarjeta(row):
        base = f"CARD_{row['CustomerID']}"
        try:
            es_par = int(row["TransactionID"]) % 2 == 0
        except (ValueError, TypeError):
            es_par = int(str(row["TransactionID"])[-1], 16) % 2 == 0

        if row["AnomalyScore"] > 0.75 and es_par:
            base += "_FRAUD_ATTEMPT"
        return hashlib.md5(base.encode()).hexdigest()[:16].upper()

    print("   -> Aplicando Regla de Negocio: Simulación de métodos de pago sobre dataset extendido...")
    fact_completa["tarjeta_simulada_hash"] = fact_completa.apply(generar_tarjeta, axis=1)

    # Renombrar campos finales para acoplar con el DWH en AWS
    fact_final = fact_completa.rename(columns={
        "TransactionID": "transaction_id", "CustomerID": "customer_id",
        "MerchantID": "merchant_id", "Timestamp": "fecha_completa",
        "TransactionAmount": "monto", "AnomalyScore": "anomaly_score",
        "Category": "categoria", "Fraudindicator": "es_fraude",
        "FraudIndicator": "es_fraude", "fraudindicator": "es_fraude"
    })
    
    fact_final["es_fraude"] = fact_final["es_fraude"].fillna(0).astype(int)
    fact_final = fact_final[["transaction_id", "customer_id", "merchant_id", "fecha_completa", 
                             "monto", "anomaly_score", "categoria", "es_fraude", "tarjeta_simulada_hash"]]

    print("✅ Fase de Transformación y Aumento completada con éxito.")
    return dim_clientes, dim_comercios, dim_tiempo, fact_final

def load_data(dim_clientes, dim_comercios, dim_tiempo, fact):
    """
    FASE 3: LOAD
    Carga los DataFrames en las tablas de AWS Aurora PostgreSQL.
    Garantiza idempotencia limpiando las tablas antes de poblar.
    """
    print("📥 Iniciando fase de Carga (Load) en AWS Aurora...")
    from sqlalchemy import text
    engine = get_db_engine()
    
    try:
        with engine.begin() as connection:
            print("   -> Limpiando tablas previas (Garantizando Idempotencia)...")
            connection.execute(text("TRUNCATE TABLE loss_prevention_dwh.fact_transacciones CASCADE;"))
            connection.execute(text("TRUNCATE TABLE loss_prevention_dwh.dim_clientes CASCADE;"))
            connection.execute(text("TRUNCATE TABLE loss_prevention_dwh.dim_comercios CASCADE;"))
            connection.execute(text("TRUNCATE TABLE loss_prevention_dwh.dim_tiempo CASCADE;"))
            
        print("   -> Cargando Dim_Clientes en la nube...")
        dim_clientes.to_sql("dim_clientes", con=engine, schema="loss_prevention_dwh", if_exists="append", index=False)
        
        print("   -> Cargando Dim_Comercios en la nube...")
        dim_comercios.to_sql("dim_comercios", con=engine, schema="loss_prevention_dwh", if_exists="append", index=False)
        
        print("   -> Cargando Dim_Tiempo en la nube...")
        dim_tiempo.to_sql("dim_tiempo", con=engine, schema="loss_prevention_dwh", if_exists="append", index=False)
        
# 2. Mapear llaves: Recuperamos los IDs seriales que generó Aurora para vincular la Fact
        print("   -> Recuperando llaves generadas para el mapeo relacional...")
        db_clientes = pd.read_sql("SELECT cliente_key, customer_id FROM loss_prevention_dwh.dim_clientes", con=engine)
        db_comercios = pd.read_sql("SELECT comercio_key, merchant_id FROM loss_prevention_dwh.dim_comercios", con=engine)
        db_tiempo = pd.read_sql("SELECT tiempo_key, fecha_completa FROM loss_prevention_dwh.dim_tiempo", con=engine)
        
        # 🌟 HOMOLOGACIÓN DE TIPOS DE DATOS (Evita el ValueError de int64 vs str) 🌟
        fact["customer_id"] = fact["customer_id"].astype(str)
        db_clientes["customer_id"] = db_clientes["customer_id"].astype(str)
        
        fact["merchant_id"] = fact["merchant_id"].astype(str)
        db_comercios["merchant_id"] = db_comercios["merchant_id"].astype(str)
        
        # Asegurar mismos tipos de formato fecha para el cruce
        db_tiempo["fecha_completa"] = pd.to_datetime(db_tiempo["fecha_completa"])
        fact["fecha_completa"] = pd.to_datetime(fact["fecha_completa"])
        
        # 3. Cruzar IDs naturales por llaves sustitutas (Surrogate Keys)
        print("   -> Vinculando llaves foráneas en Fact_Transacciones...")
        fact_mapeada = fact.merge(db_clientes, on="customer_id", how="inner")
        fact_mapeada = fact_mapeada.merge(db_comercios, on="merchant_id", how="inner")
        fact_mapeada = fact_mapeada.merge(db_tiempo, on="fecha_completa", how="inner")
        
        print("   -> Vinculando llaves foráneas en Fact_Transacciones...")
        fact_mapeada = fact.merge(db_clientes, on="customer_id", how="inner")
        fact_mapeada = fact_mapeada.merge(db_comercios, on="merchant_id", how="inner")
        fact_mapeada = fact_mapeada.merge(db_tiempo, on="fecha_completa", how="inner")
        
        fact_final = fact_mapeada[[
            "transaction_id", "cliente_key", "comercio_key", "tiempo_key",
            "monto", "anomaly_score", "categoria", "es_fraude", "tarjeta_simulada_hash"
        ]]
        
        print("   -> Cargando Fact_Transacciones en la nube...")
        fact_final.to_sql("fact_transacciones", con=engine, schema="loss_prevention_dwh", if_exists="append", index=False)
        
        print("✅ ¡Pipeline ETL ejecutado de Extremo a Extremo con éxito! Data Warehouse listo.")
        
    except Exception as e:
        print(f"❌ Error en la fase de Carga: {e}")
        raise e

if __name__ == "__main__":
    # 1. Extraer
    extracted_data = extract_data()
    
    # 2. Transformar
    dim_clientes, dim_comercios, dim_tiempo, fact = transform_data(extracted_data)

    # 3. Cargar 
    load_data(dim_clientes, dim_comercios, dim_tiempo, fact)

    # Verificación rápida en consola del tamaño de lo que procesamos
    print(f"\n📊 Resumen de transformación para el DW:")
    print(f"   - Clientes procesados: {len(dim_clientes)}")
    print(f"   - Comercios procesados: {len(dim_comercios)}")
    print(f"   - Registros de Tiempo: {len(dim_tiempo)}")
    print(f"   - Transacciones listas para carga: {len(fact)}")
    
    # Llamada a la función
    load_data(dim_clientes, dim_comercios, dim_tiempo, fact)
