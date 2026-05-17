from api import fetch_data
from db import create_table, store_data

create_table()
data = fetch_data()
store_data(data)