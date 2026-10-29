import re
import pandas as pd

raw = pd.read_parquet("data/STORE1/orders.parquet")["timestamp"].astype(str)

pat = raw.str.replace(r"\d", "9", regex=True).str.replace(r"[A-Za-z]+", "a", regex=True)
print(pat.value_counts().to_string(), "\n")

rx = re.compile(r"(?<!\d)(\d{1,2})([./-])(\d{1,2})\2(\d{2,4})(?!\d)")
rows = []
for s in raw:
    m = rx.search(s)
    if m:
        rows.append((m.group(2), int(m.group(1)), int(m.group(3))))
df = pd.DataFrame(rows, columns=["sep", "first", "second"])
print(df.groupby("sep").agg(count=("first", "size"),
                            max_first=("first", "max"),
                            max_second=("second", "max")))