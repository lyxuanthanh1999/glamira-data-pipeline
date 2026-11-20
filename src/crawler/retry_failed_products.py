import os
import sys
from pathlib import Path
import time
import random
import datetime
import threading
import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from curl_cffi import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import parse_glamira_html

ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
write_lock = threading.Lock()

# Uu tien cac domain Chau Au khong bi chan Geolocation modal
FALLBACK_DOMAINS = [
    "glamira.co.uk",
    "glamira.de",
    "glamira.fr",
    "glamira.es",
    "glamira.ca",
    "glamira.com"
]

def get_missing_product_ids(
    all_products_csv="output/products_to_crawl_full.csv",
    products_full_csv="output/products_full.csv",
    recovered_csv="output/crawled_products_recovered.csv"
) -> list:
    """
    Xac dinh tat ca Product ID con thieu hoac bi rong (Name / Price la N/A).
    """
    if not os.path.exists(all_products_csv):
        print(f"Khong tim thay file {all_products_csv}")
        return []

    df_all = pd.read_csv(all_products_csv)
    all_pids = set(df_all["product_id"].astype(str).str.strip())
    
    # 1. Tap hop cac ID da co du lieu hop le trong products_full.csv
    valid_pids = set()
    if os.path.exists(products_full_csv) and os.path.getsize(products_full_csv) > 0:
        df_full = pd.read_csv(products_full_csv)
        valid_mask = (
            df_full["product_name"].notna() &
            (df_full["product_name"] != "N/A") &
            (df_full["product_name"].astype(str).str.strip() != "") &
            df_full["price"].notna() &
            (df_full["price"] != "N/A") &
            (df_full["price"].astype(str).str.strip() != "")
        )
        valid_pids.update(df_full.loc[valid_mask, "product_id"].astype(str).str.strip())

    # 2. Bo qua cac ID da duoc cuu ho thanh cong trong recovered_csv
    if os.path.exists(recovered_csv) and os.path.getsize(recovered_csv) > 0:
        df_rec = pd.read_csv(recovered_csv)
        if "product_name" in df_rec.columns and "price" in df_rec.columns:
            rec_valid_mask = (
                df_rec["product_name"].notna() &
                (df_rec["product_name"] != "N/A") &
                (df_rec["product_name"].astype(str).str.strip() != "") &
                df_rec["price"].notna() &
                (df_rec["price"] != "N/A") &
                (df_rec["price"].astype(str).str.strip() != "")
            )
            valid_pids.update(df_rec.loc[rec_valid_mask, "product_id"].astype(str).str.strip())

    missing = sorted(list(all_pids - valid_pids))
    print(f"Tim thay {len(missing):,} san pham can cao bo sung / cuu ho (Name hoac Price con trong)...")
    return missing

def fetch_with_domain_rotation(product_id: str):
    """
    Thu lan luot cac Domain Chau Au va Magento Router de lay Name va Price that.
    """
    for domain in FALLBACK_DOMAINS:
        url = f"https://www.{domain}/catalog/product/view/id/{product_id}"
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9,de;q=0.8,fr;q=0.7',
            'Referer': f'https://www.{domain}/'
        }
        try:
            time.sleep(random.uniform(0.5, 1.2))
            res = requests.get(url, headers=headers, impersonate="chrome120", timeout=12, allow_redirects=True)
            if res.status_code == 200 and len(res.content) > 3000:
                data = parse_glamira_html(res.content, product_id, res.url)
                # Kiem tra: phai co ca Ten va Gia hop le
                if (data['product_name'] and data['product_name'] != 'N/A' and
                    data['price'] and data['price'] != 'N/A'):
                    return data
        except Exception:
            continue
    return None

def process_single_product(product_id: str, recovered_csv="output/crawled_products_recovered.csv"):
    """Xu ly tung san pham: fetch -> ghi vao file recovered."""
    data = fetch_with_domain_rotation(product_id)
    if data:
        with write_lock:
            is_new = not os.path.exists(recovered_csv) or os.path.getsize(recovered_csv) == 0
            pd.DataFrame([data]).to_csv(recovered_csv, mode="a", header=is_new, index=False)
        return True, product_id, data['product_name'], data['price']
    else:
        return False, product_id, "Discontinued / Not Found", "N/A"

def run_retry(max_workers=5):
    missing_ids = get_missing_product_ids()
    if not missing_ids:
        print("Tat ca san pham deu da co du lieu hop le. Khong can retry.")
        return

    print(f"\nBat dau quet {len(missing_ids):,} san pham voi {max_workers} luong luan phien Domain...\n")
    recovered = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_product, pid): pid for pid in missing_ids}
        for idx, fut in enumerate(as_completed(futures), 1):
            success, pid, name, price = fut.result()
            if success:
                recovered += 1
                print(f"[{idx:>4}/{len(missing_ids)}] Cuu duoc ID {pid}: {name[:30]} | Gia: {price[:25]}")
            else:
                print(f"[{idx:>4}/{len(missing_ids)}] ID {pid}: Khong tim thay tren moi domain")

    print("\n" + "=" * 60)
    print(f"KET QUA RETRY: Da cuu them {recovered:,} / {len(missing_ids):,} san pham!")
    print("=" * 60)

def update_merged_products(
    crawled_csv="output/crawled_products_sample.csv",
    recovered_csv="output/crawled_products_recovered.csv",
    output_full_csv="output/products_full.csv",
    mongo_uri="mongodb://127.0.0.1:27017/",
    db_name="countly",
    collection_name="products"
):
    """Gop du lieu cu + moi, uu tien ban ghi co Ten va Gia hop le, luu vao products_full.csv va MongoDB."""
    print("\nBAT DAU HOP NHAT DU LIEU VAO products_full.csv...")
    dfs = []
    if os.path.exists(crawled_csv) and os.path.getsize(crawled_csv) > 0:
        dfs.append(pd.read_csv(crawled_csv))
    if os.path.exists(recovered_csv) and os.path.getsize(recovered_csv) > 0:
        dfs.append(pd.read_csv(recovered_csv))

    if not dfs:
        print("Khong co du lieu de hop nhat!")
        return

    df_merged = pd.concat(dfs, ignore_index=True)
    df_merged["product_id"] = df_merged["product_id"].astype(str).str.strip()

    # Tinh diem chat luong de uu tien ban ghi co name va price that
    has_valid_name = (
        df_merged["product_name"].notna() &
        (df_merged["product_name"] != "N/A") &
        (df_merged["product_name"].astype(str).str.strip() != "")
    )
    has_valid_price = (
        df_merged["price"].notna() &
        (df_merged["price"] != "N/A") &
        (df_merged["price"].astype(str).str.strip() != "")
    )
    df_merged["quality_score"] = (has_valid_name.astype(int) * 2) + has_valid_price.astype(int)

    # Sap xep quality_score giam dan de lay ban ghi tot nhat cho moi product_id
    df_merged = df_merged.sort_values(by=["product_id", "quality_score"], ascending=[True, False])
    df_unique = df_merged.drop_duplicates(subset=["product_id"], keep="first").copy()
    df_unique = df_unique.drop(columns=["quality_score"])
    df_unique = df_unique.where(pd.notnull(df_unique), None)

    # Luu file hop nhat
    df_unique.to_csv(output_full_csv, index=False)
    print(f"Da cap nhat file: {output_full_csv} ({len(df_unique):,} san pham)")

    # Thu cap nhat vao MongoDB neu VM dang chay
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.server_info() # test ket noi
        db = client[db_name]
        col = db[collection_name]
        col.drop()
        records = df_unique.to_dict(orient='records')
        col.insert_many(records, ordered=False)
        col.create_index("product_id", unique=True)
        print(f"Da dong bo {len(records):,} san pham vao MongoDB ({collection_name}).")
    except (ConnectionFailure, ServerSelectionTimeoutError):
        print("MongoDB offline (VM da tat), da luu an toan o file CSV local.")

if __name__ == "__main__":
    # 1. Chay retry cuu ho cac san pham con thieu / rong
    run_retry(max_workers=5)
    # 2. Hop nhat du lieu vao output/products_full.csv
    update_merged_products()
