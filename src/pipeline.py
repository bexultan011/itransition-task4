
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml
from dateutil import parser as dtparser

EUR_TO_USD = 1.2


def parse_price(raw):
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    m = re.search(r"\d+(?:[.,]\d+)?", s)
    if not m:
        return None
    value = float(m.group().replace(",", "."))
    if "€" in s or "EUR" in s.upper():
        value *= EUR_TO_USD
    return value


def parse_ts(raw):
    
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return pd.NaT
    s = str(raw).strip()
    s = re.sub(r"([AaPp])\.\s*([Mm])\.", r"\1\2", s)  # A.M. -> AM
    s = s.replace(";", " ").replace(",", " ")
    # dotted numeric dates are DD.MM.YYYY; slash dates are MM/DD/YY (checked on the data)
    dayfirst = bool(re.search(r"(?<!\d)\d{1,2}\.\d{1,2}\.\d{4}", s))
    try:
        return pd.Timestamp(dtparser.parse(s, dayfirst=dayfirst))
    except (ValueError, OverflowError):
        return pd.NaT


def load(folder):
    folder = Path(folder)
    users = pd.read_csv(folder / "users.csv", dtype=str)
    orders = pd.read_parquet(folder / "orders.parquet")
    with open(folder / "books.yaml", encoding="utf-8") as f:
        books = pd.DataFrame(yaml.safe_load(f))
    books.columns = [c.lstrip(":") for c in books.columns]  # ':id' -> 'id'
    return users, orders, books


def clean_orders(orders):
    o = orders.copy()
    o = o.drop_duplicates().drop_duplicates(subset="id", keep="first")
    o["quantity"] = pd.to_numeric(o["quantity"], errors="coerce")
    o["unit_price_usd"] = o["unit_price"].map(parse_price)
    o["timestamp"] = o["timestamp"].map(parse_ts)
    o = o.dropna(subset=["user_id", "book_id", "quantity", "unit_price_usd", "timestamp"])
    o = o[(o["quantity"] > 0) & (o["unit_price_usd"] >= 0)].copy()
    o["quantity"] = o["quantity"].astype(int)
    o["paid_price"] = (o["quantity"] * o["unit_price_usd"]).round(2)
    o["date"] = o["timestamp"].dt.date
    o["user_id"] = o["user_id"].astype(str)
    o["book_id"] = o["book_id"].astype(str)
    return o


def clean_users(users):
    u = users.copy().drop_duplicates().drop_duplicates(subset="id", keep="first")
    u["id"] = u["id"].astype(str)
    u["n_name"] = u["name"].fillna("").str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    u["n_address"] = u["address"].fillna("").str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    u["n_phone"] = u["phone"].fillna("").str.replace(r"\D", "", regex=True)
    u["n_email"] = u["email"].fillna("").str.lower().str.strip()
    return u


def clean_books(books):
    b = books.copy().drop_duplicates()
    b["id"] = b["id"].astype(str)
    b = b.drop_duplicates(subset="id", keep="first")
    b["authors"] = b["author"].fillna("").map(
        lambda s: frozenset(a.strip() for a in str(s).split(",") if a.strip())
    )
    return b


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def reconcile_users(u):
    """Same person <=> at least 3 of the 4 fields (name, address, phone, email)
    are equal (only one field may change). Group by every 3-field combination
    instead of comparing all pairs."""
    fields = ["n_name", "n_address", "n_phone", "n_email"]
    dsu = DSU()
    for uid in u["id"]:
        dsu.find(uid)
    for skip in fields:
        keep = [f for f in fields if f != skip]
        sub = u[(u[keep] != "").all(axis=1)]
        for _, grp in sub.groupby(keep):
            ids = grp["id"].tolist()
            for other in ids[1:]:
                dsu.union(ids[0], other)
    return {uid: dsu.find(uid) for uid in u["id"]}


def run(folder):
    folder = Path(folder)
    users, orders, books = load(folder)
    o, u, b = clean_orders(orders), clean_users(users), clean_books(books)

    daily = o.groupby("date")["paid_price"].sum().round(2).sort_index()
    top5 = daily.nlargest(5)

    comp = reconcile_users(u)
    n_users = len(set(comp.values()))
    members = defaultdict(list)
    for uid, root in comp.items():
        members[root].append(uid)
    o["person"] = o["user_id"].map(comp) 
    spend = o.dropna(subset=["person"]).groupby("person")["paid_price"].sum()
    best_root = spend.idxmax()
    best_ids = sorted(members[best_root], key=int)

    
    n_sets = b["authors"].nunique()
    sold = o.merge(b[["id", "authors"]], left_on="book_id", right_on="id", how="inner")
    by_set = sold.groupby("authors")["quantity"].sum().sort_values(ascending=False)
    top_qty = int(by_set.iloc[0])
    top_sets = [sorted(s) for s, q in by_set.items() if q == top_qty]

    out = Path("output")  
    out.mkdir(exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ax = daily.plot(figsize=(10, 4), title=f"Daily revenue - {folder.name}")
    ax.set_xlabel("date")
    ax.set_ylabel("revenue, $")
    plt.tight_layout()
    plt.savefig(out / f"{folder.name}_revenue.png", dpi=120)
    plt.close()

    result = {
        "store": folder.name,
        "top5_days": [{"date": d.strftime("%Y-%m-%d"), "revenue": float(v)} for d, v in top5.items()],
        "unique_users": int(n_users),
        "unique_author_sets": int(n_sets),
        "most_popular_authors": top_sets,
        "most_popular_sold": top_qty,
        "best_buyer_ids": [int(i) for i in best_ids],
        "best_buyer_spent": round(float(spend.max()), 2),
        "merged_users": sorted(
            (sorted(int(i) for i in ids) for ids in members.values() if len(ids) > 1),
            key=lambda g: (-len(g), g[0]),
        ),
        "author_sets_sold": [
            {"authors": sorted(s), "sold": int(q)} for s, q in by_set.items()
        ],
        "daily_revenue": [{"date": d.strftime("%Y-%m-%d"), "revenue": float(v)} for d, v in daily.items()],
        "cleaning": {
            "orders_raw": len(orders), "orders_clean": len(o),
            "users_raw": len(users), "users_clean": len(u),
            "books_raw": len(books), "books_clean": len(b),
        },
    }
    (out / f"{folder.name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    r = run(sys.argv[1])
    skip = {"daily_revenue", "merged_users", "author_sets_sold"}
    print(json.dumps({k: v for k, v in r.items() if k not in skip}, indent=2))