import json
from pathlib import Path
import re
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bookstore Analytics", page_icon="📚", layout="wide")

# load the results saved by run_all.py
results = {}
for p in sorted(Path("output").glob("STORE*.json")):
    results[p.stem] = json.loads(p.read_text(encoding="utf-8"))

st.title("📚 Bookstore Analytics")
st.caption("Prices in USD (€1 = $1.20)")

if not results:
    st.error("No output/STORE*.json found. Run: python src/run_all.py")
    st.stop()

def users_bot(q, d):
    ql = q.lower()
    groups = d["merged_users"]
    ids = [int(n) for n in re.findall(r"\d{3,}", q)]
    if ids:
        for g in groups:
            if ids[0] in g:
                return f"User {ids[0]} is the same person as ids {g}."
        return f"User {ids[0]} has no detected aliases."
    if any(w in ql for w in ("best", "top", "buyer", "spent")):
        return f"Best buyer: {d['best_buyer_ids']}, total spent ${d['best_buyer_spent']:,.2f}."
    if any(w in ql for w in ("merged", "alias", "same")):
        return f"{len(groups)} people appear under more than one id. Largest groups: {groups[:3]}"
    if any(w in ql for w in ("how", "why", "method")):
        return ("Two records are the same person if at least 3 of the 4 fields "
                "(name, address, phone, email) match after normalization. "
                "Matches are chained with union-find.")
    c = d["cleaning"]
    return (f"{d['unique_users']:,} unique users from {c['users_clean']:,} user records. "
            "Try: 'who is the best buyer?', 'show merged users', 'how does matching work?', or a user id.")


def authors_bot(q, d):
    ql = q.lower()
    sets = d["author_sets_sold"]
    if any(w in ql for w in ("popular", "top", "best", "most")):
        lines = [f"{i}. {', '.join(s['authors'])}: {s['sold']} sold" for i, s in enumerate(sets[:5], 1)]
        return "Top 5 author sets by books sold:\n\n" + "\n".join(lines)
    if any(w in ql for w in ("how many", "unique", "count", "number")):
        return f"{d['unique_author_sets']} unique author sets (name order does not matter)."
    words = re.findall(r"[a-zA-Z']{3,}", q)
    hits = [s for s in sets if any(w.lower() in a.lower() for w in words for a in s["authors"])]
    if hits:
        return "Matching author sets:\n\n" + "\n".join(
            f"- {', '.join(s['authors'])}: {s['sold']} sold" for s in hits[:8])
    return "Try: 'which author is most popular?', 'how many author sets?', or type an author name."


def chat_area(key, bot, d, placeholder):
    hist = f"hist_{key}"
    st.session_state.setdefault(hist, [])
    box = st.container(height=260)
    with box:
        for role, text in st.session_state[hist]:
            with st.chat_message(role):
                st.markdown(text)
    q = st.chat_input(placeholder, key=f"in_{key}")
    if q:
        st.session_state[hist] += [("user", q), ("assistant", bot(q, d))]
        st.rerun()

tabs = st.tabs(list(results.keys()))          # one tab per store

for tab, (store, d) in zip(tabs, results.items()):
    with tab:
        daily = pd.DataFrame(d["daily_revenue"])
        daily["date"] = pd.to_datetime(daily["date"])

        # 1. key numbers
        c1, c2, c3 = st.columns(3)
        c1.metric("Unique users", f"{d['unique_users']:,}")
        c2.metric("Unique author sets", f"{d['unique_author_sets']:,}")
        c3.metric("Total revenue", f"${daily['revenue'].sum():,.0f}")

        # 2. daily revenue chart
        st.subheader("Daily revenue")
        fig = px.line(daily, x="date", y="revenue", labels={"date": "", "revenue": "Revenue, $"})
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch", key=f"chart_{store}")

        # 3. tables
        left, right = st.columns(2)
        with left:
            st.subheader("Top 5 days by revenue")
            top = pd.DataFrame(d["top5_days"])
            st.dataframe(top, hide_index=True, width="stretch")
        with right:
            st.subheader("Most popular author(s)")
            for authors in d["most_popular_authors"]:
                st.markdown("**" + ", ".join(authors) + "**")
            st.caption(f"{d['most_popular_sold']} books sold")
            st.subheader("Best buyer (all ids)")
            st.code(str(d["best_buyer_ids"]), language="text")
                
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Ask about users")
            chat_area(f"users_{store}", users_bot, d, "e.g. who is the best buyer?")
        with c2:
            st.subheader("Ask about author sets")
            chat_area(f"authors_{store}", authors_bot, d, "e.g. which author is most popular?")