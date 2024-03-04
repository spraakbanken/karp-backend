import json
from karp.plugins.plugin import *
from pprint import pp
from karp.main import *
import karp.plugins.link_plugin

config = json.load(open("assets/testing/config/places.json"))
data = json.loads(open("assets/testing/data/places.jsonl").readline())

linked_config = json.load(open("assets/testing/config/municipalities.json"))

plugins = Plugins(with_new_session(bootstrap_app().injector))

print("Initial config:")
pp(config)

result = transform_config(plugins, config)

print("Final config:")
pp(result)

print("Initial data:")
pp(data)

result = transform(plugins, config, data)

print("Final data:")
pp(result)
