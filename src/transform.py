import pandas as pd

def clean_and_transform(dfs):
    # Customers
    customers = dfs['customers'].copy()
    customers['first_name'] = customers['first_name'].fillna('UNKNOWN')
    customers['last_name'] = customers['last_name'].fillna('UNKNOWN')
    customers['date_of_birth'] = customers['date_of_birth'].fillna(pd.Timestamp('1900-01-01'))

    # Products
    products = dfs['products'].copy()
    products['brand'] = products['brand'].fillna('UNKNOWN')
    products['unit_price'] = products['unit_price'].clip(lower=0)

    # Stores
    stores = dfs['stores'].copy()
    stores['city'] = stores['city'].fillna('UNKNOWN')

    # Orders
    orders = dfs['sales_orders'].copy()
    orders['customer_id'] = orders['customer_id'].fillna(0)
    orders['order_date'] = pd.to_datetime(orders['order_date'], errors='coerce')
    orders = orders.drop_duplicates(subset=['order_id'])

    # Order items
    order_items = dfs['sales_order_items'].copy()
    order_items['quantity'] = order_items['quantity'].clip(lower=0)
    order_items['unit_price'] = order_items['unit_price'].clip(lower=0)
    order_items['total_price'] = order_items['quantity'] * order_items['unit_price']
    order_items = order_items.drop_duplicates(subset=['order_item_id'])

    # Handle invalid foreign keys
    valid_product_ids = set(products['product_id'])
    order_items.loc[~order_items['product_id'].isin(valid_product_ids), 'product_id'] = 0

    valid_order_ids = set(orders['order_id'])
    order_items = order_items[order_items['order_id'].isin(valid_order_ids)]

    # Build dimensions
    dim_customer = customers.rename(columns={'customer_id': 'customer_key'})
    dim_product = products.rename(columns={'product_id': 'product_key'})
    dim_store = stores.rename(columns={'store_id': 'store_key'})
    all_dates = pd.to_datetime(orders['order_date'].dropna().unique())
    dim_date = pd.DataFrame({
        'date_key': all_dates,
        'year': all_dates.year,
        'quarter': all_dates.quarter,
        'month': all_dates.month,
        'day': all_dates.day,
        'weekday': all_dates.weekday
    })

    # Build fact table
    fact_sales = order_items.merge(
        orders[['order_id', 'store_id', 'customer_id', 'order_date', 'payment_method', 'total_amount']],
        on='order_id',
        how='left'
    )
    fact_sales = fact_sales.rename(columns={
        'order_id': 'order_key',
        'store_id': 'store_key',
        'customer_id': 'customer_key',
        'order_date': 'order_date_key'
    })

    dims = {
        'dim_customer': dim_customer,
        'dim_product': dim_product,
        'dim_store': dim_store,
        'dim_date': dim_date
    }

    return dims, fact_sales
