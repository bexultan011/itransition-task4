import sys
sys.path.insert(0, "src")
from step2 import orders 
from step4 import books    

print("unique author sets:", books["authors"].nunique())

sold = orders.merge(books[["id", "authors"]], left_on="book_id", right_on="id", how="inner")
by_set = sold.groupby("authors")["quantity"].sum().sort_values(ascending=False)

print("\ntop 5 author sets by books sold:")
for authors, qty in by_set.head(5).items():
    print(qty, "|", ", ".join(sorted(authors)))

top_qty = by_set.iloc[0]
winners = [sorted(a) for a, q in by_set.items() if q == top_qty]
print("\nmost popular:", winners, "with", top_qty, "sold")