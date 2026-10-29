import sys
sys.path.insert(0, "src")
from step4 import users  
parent = {}

def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]  
        x = parent[x]
    return x

def union(a, b):
    parent[find(a)] = find(b)

for uid in users["id"]:
    find(uid) 

fields = ["n_name", "n_address", "n_phone", "n_email"]

for skip in fields:                     
    keep = [f for f in fields if f != skip]
    sub = users[(users[keep] != "").all(axis=1)]  
    for _, group in sub.groupby(keep):
        ids = group["id"].tolist()
        for other in ids[1:]:
            union(ids[0], other)


person = {uid: find(uid) for uid in users["id"]}
print("user records:", len(users))
print("unique users:", len(set(person.values())))

groups = {}
for uid, root in person.items():
    groups.setdefault(root, []).append(uid)
merged = [g for g in groups.values() if len(g) > 1]
print("people with more than one id:", len(merged))
for g in merged[:3]:
    print(users[users["id"].isin(g)][["id", "name", "address", "phone", "email"]], "\n")