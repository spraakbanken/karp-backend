import json

with open('places.jsonl') as fp:
     content = fp.readlines()

out = open('places2.jsonl')

for row in content:
  place = json.loads(row)
  id = place['']
  print(place)

