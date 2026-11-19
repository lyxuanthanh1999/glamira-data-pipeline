import time
from pymongo import MongoClient

def create_indexes():
    client = MongoClient("mongodb://127.0.0.1:27017")
    col = client['countly']['summary']
    indexes_to_create = [
        ("ip","Tăng tốc trích xuất danh sách IP duy nhất"),
        ("collection", "Tăng tốc lọc các sự kiện liên quan đến sản phẩm"),
        ("product_id","Tăng tốc tra cứu thông tin sản phẩm")
    ]
    for field, desc in indexes_to_create:
        start = time.time()
        col.create_index(field)
        elapsed = time.time() - start
        print(f" Hoàn tất index '{field}' trong {elapsed:.2f} giây.\n")

    for idx in col.list_indexes():
        print(f"- {idx['name']} : {idx['key']}")

if __name__ == "__main__":
    create_indexes()