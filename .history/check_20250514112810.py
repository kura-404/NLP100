batches = client.batches.list()
for b in batches.data:
    print(f"{b.id}: {b.status} ({b.created_at})")