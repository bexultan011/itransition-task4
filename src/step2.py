import re
import pandas as pd
from dateutil import parser as dtparser

folder = "data/STORE1"
orders = pd.read_parquet(f"{folder}/orders.parquet")

EUR_TO_USD = 1.2


def parse_price(raw):
    """'$ 35', '30.0USD', 'USD25.25', '37.0 USD', '€10' -> dollars."""
    s = str(raw)
    m = re.search(r"\d+(?:[.,]\d+)?", s)
    if not m:
        return None
    value = float(m.group().replace(",", "."))
    if "€" in s or "EUR" in s.upper():
        value *= EUR_TO_USD
    return value


def parse_ts(raw):
    """'09:28,10-Dec-2025', '2025-06-25;05:00:01 A.M.', etc."""
    s = str(raw).strip()
    s = re.sub(r"([AaPp])\.\s*([Mm])\.", r"\1\2", s)  # A.M. -> AM
    s = s.replace(";", " ").replace(",", " ")
    # dotted numeric dates are DD.MM.YYYY; slash dates are MM/DD/YY
    dayfirst = bool(re.search(r"(?<!\d)\d{1,2}\.\d{1,2}\.\d{4}", s))
    try:
        return pd.Timestamp(dtparser.parse(s, dayfirst=dayfirst))
    except (ValueError, OverflowError):
        return pd.NaT


orders = orders.drop_duplicates().drop_duplicates(subset="id", keep="first")
orders["unit_price_usd"] = orders["unit_price"].map(parse_price)
orders["timestamp"] = orders["timestamp"].map(parse_ts)

before = len(orders)
orders = orders.dropna(subset=["unit_price_usd", "timestamp"])
print("rows dropped:", before - len(orders))

orders["paid_price"] = (orders["quantity"] * orders["unit_price_usd"]).round(2)
orders["date"] = orders["timestamp"].dt.date

print(orders[["id", "unit_price", "unit_price_usd", "timestamp", "paid_price", "date"]].head(10))
print(orders.dtypes)