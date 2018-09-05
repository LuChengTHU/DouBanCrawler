import os
import json

actors = {}

if not os.path.exists("actors_add/"):
    os.mkdir("actors_add/")

files = os.listdir("result/")
for filename in files:
    with open("result/" + filename, encoding="utf-8") as f:
        actor = json.load(f)
    with open("year/" + filename, encoding='utf-8') as f:
        year = json.load(f)
    actor['firstYear'] = year['firstYear']
    with open("actors_add/" + filename, "w", encoding='utf-8') as f:
        json.dump(actor, f)

