import pandas as pd
import yaml

folder = "data/STORE1"

users = pd.read_csv(f"{folder}/users.csv", dtype=str)
users = users.drop_duplicates().drop_duplicates(subset="id", keep="first")

def norm_text(s):
    return s.fillna("").str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    
users["n_name"] = norm_text(users["name"])
users["n_address"] = norm_text(users["address"])
users["n_email"] = norm_text(users["email"])
users["n_phone"] = users["phone"].fillna("").str.replace(r"\D", "", regex=True)  # digits only

print(users[["phone", "n_phone"]].head())
print("users:", len(users))

with open(f"{folder}/books.yaml", encoding="utf-8") as f:
    books = pd.DataFrame(yaml.safe_load(f))
books.columns = [c.lstrip(":") for c in books.columns]   # ':id' -> 'id'
books = books.drop_duplicates().drop_duplicates(subset="id", keep="first")

books["authors"] = books["author"].fillna("").map(
    lambda s: frozenset(a.strip() for a in s.split(",") if a.strip())
)

print(books[["id", "author", "authors"]].head())
print("books:", len(books), "| columns:", list(books.columns))