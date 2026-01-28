from sqlalchemy import create_engine
from config.db_config import DB_CONFIG

def create_engine_from_config(config):
    return create_engine(f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}")

def load_to_dw(dims, fact):
    target_engine = create_engine_from_config(DB_CONFIG['target'])

    # Load dimensions
    for name, df in dims.items():
        df.to_sql(name, target_engine, if_exists='replace', index=False)
    
    # Load fact table
    fact.to_sql('fact_sales', target_engine, if_exists='replace', index=False)
