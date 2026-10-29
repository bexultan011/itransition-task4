import pandas as pd
import yaml

folder = "data/STORE1"

users = pd.read_csv(f"{folder}/users.csv", dtype=str)
orders = pd.read_parquet(f"{folder}/orders.parquet")

with open(f"{folder}/books.yaml", encoding="utf-8") as f:
    books = pd.DataFrame(yaml.safe_load(f))

print(users.head(), "\n")
print(orders.head(), "\n")
print(books.head(), "\n")

print(users.info())
print(orders.info())
print(books.info())