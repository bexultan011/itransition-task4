import sys
import os
os.makedirs("output", exist_ok=True)
sys.path.insert(0, "src")
from step2 import orders  

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

daily = orders.groupby("date")["paid_price"].sum().round(2).sort_index().reset_index()
daily.columns = ["date", "revenue"]
daily["date"] = pd.to_datetime(daily["date"])

plt.figure(figsize=(10, 4))
plt.plot(daily["date"], daily["revenue"], color="#2a6fdb", linewidth=1.5)
plt.title("Daily revenue - STORE1")
plt.xlabel("Date")
plt.ylabel("Revenue, $")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("output/STORE1_revenue.png", dpi=120)
print("saved output/STORE1_revenue.png")

fig = px.line(daily, x="date", y="revenue", title="Daily revenue - STORE1",
              labels={"date": "Date", "revenue": "Revenue, $"})
fig.update_traces(line_color="#2a6fdb")
fig.write_html("output/STORE1_revenue.html")
print("saved output/STORE1_revenue.html")