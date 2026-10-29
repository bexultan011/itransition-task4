import sys
sys.path.insert(0, "src")
from step2 import orders  # runs step 2 and gives the cleaned table

# 1. daily revenue: sum of paid_price per date
daily = orders.groupby("date")["paid_price"].sum().round(2).sort_index()
print(daily.head())
print("days:", len(daily), "| total revenue:", round(daily.sum(), 2))

# 2. top 5 days
top5 = daily.nlargest(5)
for d, v in top5.items():
    print(d.strftime("%Y-%m-%d"), v)

for i, path in enumerate(sys.path):
    print(i, path)