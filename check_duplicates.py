from tastetrail.store import RestaurantStore
from collections import defaultdict

s = RestaurantStore.load()
loc_map = defaultdict(list)
for r in s.all():
    loc_map[r.name].append((r.id, r.location))

dup_info = {name: locs for name, locs in loc_map.items() if len(locs) > 1}

print("Duplicate restaurants with different locations/IDs:")
for name, locs in list(dup_info.items())[:10]:
    print(f"\n{name}:")
    for rid, loc in locs[:5]:
        print(f"  ID: {rid}, Location: {loc}")
