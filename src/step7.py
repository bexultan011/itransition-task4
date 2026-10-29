import sys
sys.path.insert(0, "src")
from step2 import orders  
from step5 import person   

orders["person"] = orders["user_id"].astype(str).map(person)
print("orders without a matching user:", orders["person"].isna().sum())


spend = orders.groupby("person")["paid_price"].sum()
best = spend.idxmax()

best_ids = sorted(int(uid) for uid, root in person.items() if root == best)

print("\nbest buyer ids:", best_ids)
print("total spent: $", round(spend.max(), 2))

print("best single user_id spent: $", round(orders.groupby("user_id")["paid_price"].sum().max(), 2))