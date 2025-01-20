# Does a search and replace on all text fields in a resource.

from karp.foundation import json
import sys

entry_commands.start_transaction()

resource_name = sys.argv[1]

for line in sys.stdin.readlines():
    id, search, replace = line.split()

    entry = entry_queries.by_id(resource_name, id)
    print(entry.id)

    for path in json.all_paths(entry.entry):
        value = json.get_path(path, entry.entry)

        if isinstance(value, str):
            new_value = value.replace(search, replace)

            if value != new_value:
                print(value, "=>", new_value)
                json.set_path(path, new_value, entry.entry)

    entry_commands.update_entry(resource_name, entry.id, entry.version, "", "", entry.entry)

entry_commands.commit()
