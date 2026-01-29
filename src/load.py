from sqlalchemy import create_engine, text
from config.db_config import DB_CONFIG
import pandas as pd

# ------------------------
# Create engine from config
# ------------------------
def create_engine_from_config(config):
    return create_engine(
        f"postgresql+psycopg2://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )

# ------------------------
# Load dims and fact tables
# ------------------------
def load_to_dw(dims, fact):
    engine = create_engine_from_config(DB_CONFIG['target'])
    conn = engine.connect()
    
    # ------------------------
    # Load dimension tables
    # ------------------------
    for dim_name, df in dims.items():
        print(f"Loading dimension: {dim_name} ...")
        df.to_sql(dim_name, engine, if_exists='replace', index=False)  # replace for dimensions
        print(f"Dimension {dim_name} loaded. Rows: {len(df)}")
    
    # ------------------------
    # Map surrogate keys in fact tables
    # ------------------------
    print("Mapping surrogate keys in fact tables ...")
    
    # Map customer_sk and store_sk in sales_orders
    orders = fact['sales_orders'].copy()
    customers = dims['customers'][['customer_id','customer_sk']]
    stores = dims['stores'][['store_id','store_sk']]
    
    # Customer SK
    orders = orders.merge(customers, on='customer_id', how='left')
    orders['customer_sk_missing'] = orders['customer_sk'].isna().astype(int)
    
    # Store SK
    orders = orders.merge(stores, on='store_id', how='left')
    orders['store_sk_missing'] = orders['store_sk'].isna().astype(int)
    
    fact['sales_orders'] = orders

    # Map product_sk and order_sk in sales_order_items
    items = fact['sales_order_items'].copy()
    products = dims['products'][['product_id','product_sk']]
    order_sk_map = orders[['order_id','order_sk']] if 'order_sk' in orders.columns else orders[['order_id']]
    
    items = items.merge(products, on='product_id', how='left')
    items['product_sk_missing'] = items['product_sk'].isna().astype(int)
    
    # For order_sk, map using order_id
    if 'order_sk' in order_sk_map.columns:
        items = items.merge(order_sk_map, on='order_id', how='left')
        items['order_sk_missing'] = items['order_sk'].isna().astype(int)
    
    fact['sales_order_items'] = items

    # ------------------------
    # Load fact tables
    # ------------------------
    for fact_name, df in fact.items():
        print(f"Loading fact table: {fact_name} ...")
        df.to_sql(fact_name, engine, if_exists='append', index=False)  # append for fact tables
        print(f"Fact table {fact_name} loaded. Rows: {len(df)}")
    
    conn.close()
    print("✅ ETL load completed successfully!")
