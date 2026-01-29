import pandas as pd

# =========================
# Generic Transformation Functions
# =========================

def handle_missing(df, strategy_dict):
    df = df.copy()
    for col, strategy in strategy_dict.items():
        if col in df.columns:
            df[col] = df[col].fillna(strategy)
    return df

def fix_dtypes(df, dtype_dict):
    df = df.copy()
    for col, dtype in dtype_dict.items():
        if col in df.columns:
            if dtype == 'datetime':
                df[col] = pd.to_datetime(df[col], errors='coerce')
            else:
                df[col] = df[col].astype(dtype, errors='ignore')
    return df

def remove_duplicates(df, subset_cols):
    df = df.copy()
    return df.drop_duplicates(subset=subset_cols)

def standardize_text(df, text_cols, method='title'):
    df = df.copy()
    for col in text_cols:
        if col in df.columns:
            if method == 'title':
                df[col] = df[col].str.title()
            elif method == 'upper':
                df[col] = df[col].str.upper()
            elif method == 'lower':
                df[col] = df[col].str.lower()
    return df

def validate_values(df, rules_dict):
    df = df.copy()
    invalid_rows = pd.DataFrame()
    for col, rule in rules_dict.items():
        if col in df.columns:
            invalid = df[~df[col].apply(rule)]
            if not invalid.empty:
                invalid_rows = pd.concat([invalid_rows, invalid])
    return invalid_rows

def detect_outliers(df, numeric_cols):
    df = df.copy()
    outliers = pd.DataFrame()
    for col in numeric_cols:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            mask = (df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)
            if mask.any():
                outliers_col = df[mask]
                outliers = pd.concat([outliers, outliers_col])
    return outliers

def transform_table(df, config):
    """
    Apply modular transformations to a DataFrame based on config.
    """
    df = handle_missing(df, config.get('fillna', {}))
    df = fix_dtypes(df, config.get('dtypes', {}))
    df = standardize_text(df, config.get('text_cols', []), config.get('text_method', 'title'))
    df = remove_duplicates(df, config.get('pk', []))
    invalid_rows = validate_values(df, config.get('validation', {}))
    outliers = detect_outliers(df, config.get('numeric_cols', []))
    return df, invalid_rows, outliers

# =========================
# Surrogate Key Generator
# =========================

def generate_surrogate_key(df, sk_name):
    df = df.copy()
    if sk_name not in df.columns:
        df[sk_name] = range(1, len(df)+1)
    return df

# =========================
# Full Transformation with Surrogate Keys
# =========================

def clean_and_transform(tables):
    transformed_tables = {}

    # -------------------------
    # 1️⃣ Customers
    # -------------------------
    customers_config = {
        'fillna': {'first_name':'UNKNOWN', 'last_name':'UNKNOWN',
                   'loyalty_member': False, 'created_at': pd.Timestamp('1900-01-01')},
        'dtypes': {'dob':'datetime', 'created_at':'datetime','loyalty_member':bool},
        'text_cols': ['first_name','last_name'],
        'text_method': 'title',
        'pk': ['customer_id'],
        'validation': {'loyalty_member': lambda x: isinstance(x,bool)},
        'numeric_cols': []
    }
    df_customers, _, _ = transform_table(tables['customers'], customers_config)
    df_customers = generate_surrogate_key(df_customers, 'customer_sk')
    transformed_tables['customers'] = df_customers

    # -------------------------
    # 2️⃣ Products
    # -------------------------
    products_config = {
        'fillna': {'product_name':'UNKNOWN','category':'UNKNOWN','brand':'UNKNOWN','unit_price':0,
                   'created_at': pd.Timestamp('1900-01-01')},
        'dtypes': {'unit_price':float,'created_at':'datetime'},
        'text_cols': ['category','brand','product_name'],
        'text_method': 'title',
        'pk': ['product_id'],
        'validation': {'unit_price': lambda x: x>=0},
        'numeric_cols': ['unit_price']
    }
    df_products, _, _ = transform_table(tables['products'], products_config)
    df_products = generate_surrogate_key(df_products, 'product_sk')
    transformed_tables['products'] = df_products

    # -------------------------
    # 3️⃣ Stores
    # -------------------------
    stores_config = {
        'fillna': {},
        'dtypes': {'opening_date':'datetime'},
        'text_cols': ['store_name','city','state'],
        'text_method': 'title',
        'pk': ['store_id'],
        'validation': {},
        'numeric_cols': []
    }
    df_stores, _, _ = transform_table(tables['stores'], stores_config)
    df_stores = generate_surrogate_key(df_stores, 'store_sk')
    transformed_tables['stores'] = df_stores

    # -------------------------
    # 4️⃣ Sales Orders
    # -------------------------
    sales_orders_config = {
        'fillna': {'total_amount':0,'payment_method':'Unknown'},
        'dtypes': {'order_date':'datetime','total_amount':float},
        'text_cols':['payment_method'],
        'text_method':'title',
        'pk':['order_id'],
        'validation': {'total_amount': lambda x: x>=0},
        'numeric_cols':['total_amount']
    }
    df_orders, _, _ = transform_table(tables['sales_orders'], sales_orders_config)

    # Missing flags for surrogate key joins
    df_orders['customer_sk_missing'] = 0
    df_orders['store_sk_missing'] = 0
    transformed_tables['sales_orders'] = df_orders

    # -------------------------
    # 5️⃣ Sales Order Items
    # -------------------------
    sales_items_config = {
        'fillna': {'quantity':1,'unit_price':0},
        'dtypes': {'quantity':int,'unit_price':float,'total_price':float},
        'text_cols':[],
        'pk':['order_item_id'],
        'validation': {'quantity': lambda x:x>0, 'unit_price': lambda x:x>=0},
        'numeric_cols':['quantity','unit_price','total_price']
    }
    df_items = tables['sales_order_items'].copy()
    df_items['quantity'] = df_items['quantity'].fillna(1)
    df_items['unit_price'] = df_items['unit_price'].fillna(0)
    df_items['total_price'] = df_items['quantity'] * df_items['unit_price']
    df_items['product_sk_missing'] = 0
    df_items['order_sk_missing'] = 0
    df_items, _, _ = transform_table(df_items, sales_items_config)
    transformed_tables['sales_order_items'] = df_items

    # -------------------------
    # 6️⃣ Return dims & fact
    # -------------------------
    dims = {
        'customers': transformed_tables['customers'],
        'products': transformed_tables['products'],
        'stores': transformed_tables['stores']
    }
    fact = {
        'sales_orders': transformed_tables['sales_orders'],
        'sales_order_items': transformed_tables['sales_order_items']
    }

    return dims, fact
