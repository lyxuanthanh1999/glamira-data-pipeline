import bson
from bson import json_util

INPUT_BSON_PATH = "dump/countly/summary.bson"
OUTPUT_JSON_PATH = "data/sample.json"
SAMPLE_LIMIT = 10000
data = []

with open(INPUT_BSON_PATH,"rb") as f:
        for i, doc in enumerate(bson.decode_file_iter(f)):
            data.append(doc)

            if(i+1)%2000 == 0:
                print(f"Đã trích xuất {i+1}/{SAMPLE_LIMIT}")
            if (i + 1) >= SAMPLE_LIMIT:
                break
with open(OUTPUT_JSON_PATH,"w",encoding="utf-8") as out_file:
    out_file.write(json_util.dumps(data))
    print('Hoàn thành')
