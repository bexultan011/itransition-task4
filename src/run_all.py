from pathlib import Path
from pipeline import run

for folder in sorted(Path("data").glob("STORE*")):
    r = run(folder)
    print(r["store"], "| users:", r["unique_users"], "| author sets:", r["unique_author_sets"],
          "| best buyer:", r["best_buyer_ids"], "| top5:", [d["date"] for d in r["top5_days"]])
