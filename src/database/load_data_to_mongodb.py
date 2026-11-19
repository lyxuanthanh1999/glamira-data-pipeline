"""
Glamira Project 05 - Phase 1: Full Data Loading to MongoDB (Step 1.3)
Mục tiêu:
1. Đọc dữ liệu sự kiện thô theo khối (Batch / Chunked Processing, ví dụ 10,000 docs/batch).
2. Thêm trường metadata: _loaded_at, _source_file để theo dõi lineage dữ liệu.
3. Nạp vào MongoDB collection 'summary' bằng insert_many(..., ordered=False).
4. Kiểm tra đối soát số lượng dòng (Row count validation) khớp với nguồn.

Ghi chú: Trên máy ảo GCP VM thực tế, bạn có thể chạy script này hoặc dùng lệnh:
mongorestore --db=countly --collection=summary dump/countly/summary.bson
"""

import os
import time
import datetime
import bson
from pymongo import MongoClient

def load_full_data_to_mongodb(
    bson_path="dump/countly/summary.bson",
    mongo_uri="mongodb://127.0.0.1:27017/",
    db_name="countly",
    collection_name="summary",
    batch_size=10000,
    limit=None
):
    print("=" * 65)
    print(" NẠP DỮ LIỆU FULL EVENTS VÀO MONGODB (PHASE 1 - STEP 1.3)")
    print("=" * 65)

    if not os.path.exists(bson_path):
        print(f"[CANH BAO] Không tìm thấy file BSON tại: {bson_path}")
        print("Lưu ý: Trên môi trường Production/Cloud, lệnh sau thường được ưu tiên:")
        print(f"   mongorestore --db={db_name} --collection={collection_name} {bson_path}")
        return

    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db[collection_name]

    print(f"Kết nối tới MongoDB: {mongo_uri} (DB: {db_name}, Col: {collection_name})")
    print(f"Bắt đầu đọc và nạp theo khối (batch_size={batch_size:,})...")

    batch = []
    total_loaded = 0
    start_time = time.time()
    source_filename = os.path.basename(bson_path)

    with open(bson_path, "rb") as f:
        for doc in bson.decode_file_iter(f):
            # Thêm metadata lineage
            doc["_loaded_at"] = datetime.datetime.now(datetime.timezone.utc)
            doc["_source_file"] = source_filename

            batch.append(doc)
            total_loaded += 1

            if len(batch) >= batch_size:
                col.insert_many(batch, ordered=False)
                batch = []
                if total_loaded % 100000 == 0:
                    elapsed = time.time() - start_time
                    print(f"   -> Đã nạp {total_loaded:,} dòng (Tốc độ: {total_loaded/elapsed:,.0f} docs/s)...")

            if limit and total_loaded >= limit:
                break

        if batch:
            col.insert_many(batch, ordered=False)

    total_time = time.time() - start_time
    print(f"[OK] Hoàn tất nạp dữ liệu! Tổng số: {total_loaded:,} dòng trong {total_time:.2f}s")

    # Xác thực số lượng documents
    count_in_db = col.count_documents({})
    print("\n" + "=" * 65)
    print(" BÁO CÁO NGHIỆM THU (CHECKPOINT #7)")
    print(f"  Số dòng đọc từ nguồn     : {total_loaded:,}")
    print(f"  Số document trong MongoDB : {count_in_db:,}")
    print(f"  Trạng thái khớp           : {' KHỚP 100%' if total_loaded == count_in_db else '[CANH BAO] CẦN KIỂM TRA LẠI'}")
    print("=" * 65)

if __name__ == "__main__":
    load_full_data_to_mongodb()

