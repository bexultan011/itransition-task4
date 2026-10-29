# Task 4: Bookstore analytics

Cleans the STORE1 to STORE5 datasets (users, orders, books) and shows the results in a Streamlit dashboard.

- src/pipeline.py: cleaning and analysis (daily revenue, unique users, author sets, best buyer)
- src/run_all.py: runs the pipeline for every store and writes output/STORE*.json
- app.py: dashboard with one tab per store and chat areas for users and author sets
