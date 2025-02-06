# Exports a resource as pickle and jsonl.

import json
import pickle

resource_name = sys.argv[1]
pickle_name = sys.argv[2]
jsonl_name = sys.argv[3]

entries = list(entry_queries.all_entries(resource_name, expand_plugins=False))

with open(pickle_name, "wb") as file:
    pickle.dump(entries, file)

with open(jsonl_name, "w") as file:
    for entry in entries:
        json.dump(entry.dict(), file)
        file.write("\n")
