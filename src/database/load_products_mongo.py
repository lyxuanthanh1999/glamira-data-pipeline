import os
import time
import pandas as pd
from pymongo import MongoClient

def load_products_to_mongodb(
    crawled_csv="output/crawled_products_sample.csv",
    recovered_csv="output/crawled_products_recovered.csv",
    output_backup_csv="output/products_full.csv",
    mongo_uri: str = "mongodb://127.0.0.1:27017/",
    db_name: str = "countly",
    collection_name: str = "products",
    batch_size: int = 5000,
    ):
    dfs = []

    if os.path.exists(crawled_csv) and os.path.getsize(crawled_csv) > 0:
        print(f"Đang đọc file lần 1: {crawled_csv}...")
        dfs.append(pd.read_csv(crawled_csv))

    if os.path.exists(recovered_csv) and os.path.getsize(recovered_csv) > 0:
        print(f"Đang đọc file retry: {recovered_csv}...")
        dfs.append(pd.read_csv(recovered_csv))

    if not dfs:
        print("Không tìm thấy dữ liệu sản phẩm nào!")
        return

    df: pd.DataFrame = pd.concat(dfs, ignore_index=True)
    df["product_id"] = df["product_id"].astype(str).str.strip()

    df["price"] = df["price"].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

    for col_name in ['description', 'sku']:
        if col_name not in df.columns:
            df[col_name] = 'N/A'
    df['description'] = df['description'].fillna('N/A')
    df['sku'] = df['sku'].fillna('N/A')

    df = df.sort_values(by=['product_id', 'product_name'], na_position='last')
    df_unique = df.drop_duplicates(subset=['product_id'], keep='first').copy()
    df_unique = df_unique.where(pd.notnull(df_unique), None)

    df_unique.to_csv(output_backup_csv, index=False)
    print("=" * 60)
    print(f"Đã lưu file tổng hợp đầy đủ: {output_backup_csv} ({len(df_unique):,} sản phẩm)")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db[collection_name]
    col.drop()

    records = df_unique.to_dict(orient="records")
    start_time = time.time()
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        col.insert_many(batch, ordered=False)
        print(f"  Đã nạp {min(i + batch_size, len(records)):,}/{len(records):,} documents")
    print(f"Nạp xong trong {time.time() - start_time:.2f} giây")
    print("Tạo unique index trên trường product_id")
    col.create_index("product_id", unique=True)

    stats = db.command('collStats', collection_name)
    sample_doc = col.find_one({}, {"_id": 0})
    print("\n" + "=" * 60)
    print("BÁO CÁO NGHIỆM THU COLLECTION PRODUCTS (MONGODB)")
    print("=" * 60)
    print(f"  Tổng sản phẩm trong MongoDB     : {stats.get('count'):,} (Kỳ vọng: {len(records):,})")
    print(f"  Dung lượng dữ liệu (Data Size)  : {stats.get('size') / 1024 / 1024:.2f} MB")
    print(f"  Số lượng Indexes                : {stats.get('nindexes')}")
    print(f"  Sample Document mẫu             : {sample_doc}")
    print("=" * 60)



if __name__ =="__main__":
    load_products_to_mongodb()