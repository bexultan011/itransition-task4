import sys
import pandas as pd
sys.path.insert(0, "src")
from pipeline import load, clean_orders

users, raw, books = load("data/STORE1")
o = clean_orders(raw)

today = pd.Timestamp("2026-10-28")
future = o[o["timestamp"] > today]
print("last order date:", o["timestamp"].max())
print("orders after today:", len(future), "of", len(o))
print("revenue after today: $", round(future["paid_price"].sum(), 2))

raw["parsed"] = raw["timestamp"].map(lambda s: None)
latest = o.sort_values("timestamp", ascending=False).head(10)
print(raw[raw["id"].isin(latest["id"])][["id", "timestamp"]])
print(latest[["id", "timestamp"]])

print(o.set_index("timestamp").resample("MS")["paid_price"].agg(["count", "sum"]).tail(8))