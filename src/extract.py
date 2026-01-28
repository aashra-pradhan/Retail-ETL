import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
print("Current working directory:", os.getcwd())


load_dotenv(dotenv_path="config/.env")  # <-- specify relative path to your .env

def extract_tables():
    """
    Connect to PostgreSQL directly using psycopg2 and extract tables as pandas DataFrames.
    Returns a dictionary with table names as keys and DataFrames as values.
    """

    # --- Database credentials from environment variables ---
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", 5432))
    database = os.getenv("DB_NAME", "RETAIL_RAW_DB")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")  # make sure this is set in your .env file

    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print("❌ Connection failed")
        print(e)
        return {}  # return empty dict if connection fails

    # List of tables to extract
    tables = ['customers', 'products', 'stores', 'sales_orders', 'sales_order_items']
    dataframes = {}

    # Extract each table
    for table in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table};", conn)
            dataframes[table] = df
            print(f"✅ Extracted table: {table}")
        except Exception as e:
            print(f"⚠️ Failed to extract table {table}")
            print(e)

    # Close connection
    conn.close()

    return dataframes
