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

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import parse_glamira_html

ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
write_lock = threading.Lock()


FALLBACK_DOMAINS = [
    "glamira.com",
    "glamira.co.uk",
    "glamira.de",
    "glamira.fr",
    "glamira.es",
    "glamira.ca"
]

def get_missing_product_ids(
    all_products_csv="output/products_to_crawl_full.csv", 
    crawled_csv="output/crawled_products_sample.csv",
    recovered_csv="output/crawled_products_recovered.csv" 
) -> list:

    df_all = pd.read_csv(all_products_csv)
    all_pids = set(df_all["product_id"].astype(str).str.strip())
    done_pids = set()

    if os.path.exists(crawled_csv) and os.path.getsize(crawled_csv) > 0:
        df_crawled = pd.read_csv(crawled_csv)
        done_pids.update(df_crawled["product_id"].astype(str).str.strip())
        
    if os.path.exists(recovered_csv) and os.path.getsize(recovered_csv) > 0:
        df_rec = pd.read_csv(recovered_csv)
        done_pids.update(df_rec["product_id"].astype(str).str.strip())
    missing = list(all_pids - done_pids)
    print(f"Tìm thấy {len(missing):,} sản phẩm cần thử lại (Retry)...")
    return missing

def fetch_with_domain_rotation(product_id: str):
    
    
    for domain in FALLBACK_DOMAINS:
        url = f"https://www.{domain}/catalog/product/view/id/{product_id}"
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        try:
            time.sleep(random.uniform(0.5, 1.5))
            res = requests.get(url, headers=headers, impersonate="chrome120", timeout=12, allow_redirects=True)
            if res.status_code == 200 and len(res.content) > 5000:
                if b"<h1" in res.content:
                    return res.content, res.url 
        except Exception:
            continue
    return None, None

# def parse_advanced_html(html_bytes: bytes, product_id: str, final_url: str) -> dict:
#     """Bóc tách tối đa thông tin: Name, Category, Price, Description, SKU."""
#     soup = BeautifulSoup(html_bytes, "html.parser")
    
#     # 1. Tên sản phẩm
#     h1 = soup.find("h1")
#     product_name = h1.text.strip() if h1 else "N/A"
    
#     # 2. Danh mục
#     crumbs = [b.text.strip() for b in soup.select(".breadcrumbs li, .breadcrumb li") if b.text.strip()]
#     category = crumbs[-2] if len(crumbs) >= 2 else (crumbs[-1] if crumbs else "N/A")
    
#     # 3. Giá
#     price_tag = soup.select_one(".price-box, .price, [data-price-type='finalPrice']")
#     price = " ".join(price_tag.text.split()) if price_tag else "N/A"
    
#     # 4. Mô tả sản phẩm
#     meta_desc = soup.find("meta", attrs={"name": "description"})
#     description = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else "N/A"
    
#     # 5. SKU
#     sku_tag = soup.select_one(".sku .value, [itemprop='sku']")
#     sku = sku_tag.text.strip() if sku_tag else "N/A"
    
#     return {
#         "product_id": str(product_id),
#         "product_name": product_name,
#         "category": category,
#         "price": price,
#         "description": description[:300],
#         "sku": sku,
#         "url": final_url,
#         "crawled_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "status": "SUCCESS"
#     }


def process_single_product(product_id: str, recovered_csv="output/crawled_products_recovered.csv"):
    """Xử lý từng sản phẩm: fetch -> parse -> ghi vào file recovered."""
    html_bytes, final_url = fetch_with_domain_rotation(product_id)
    if html_bytes:
        data = parse_glamira_html(html_bytes, product_id, final_url)
        with write_lock:
            is_new = not os.path.exists(recovered_csv) or os.path.getsize(recovered_csv) == 0
            pd.DataFrame([data]).to_csv(recovered_csv, mode="a", header=is_new, index=False)
        return True, product_id, data['product_name']
    else:
        return False, product_id, "Discontinued / Not Found"

def run_retry(max_workers=5):
    
    missing_ids = get_missing_product_ids()
    if not missing_ids:
        print("Không còn sản phẩm nào bị thiếu.")
        return

    print(f"\nBắt đầu quét {len(missing_ids)} sản phẩm với {max_workers} luồng luân phiên Domain...\n")
    recovered = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_product, pid): pid for pid in missing_ids}
        for idx, fut in enumerate(as_completed(futures), 1):
            success, pid, info = fut.result()
            if success:
                recovered += 1
                print(f"[{idx:>4}/{len(missing_ids)}] Cứu được ID {pid}: {info[:35]}")
            else:
                print(f"[{idx:>4}/{len(missing_ids)}] ID {pid}: Hết hạn trên mọi tên miền")

    print("\n" + "=" * 60)
    print(f"KẾT QUẢ RETRY: Đã cứu thêm {recovered:,} / {len(missing_ids):,} sản phẩm!")
    print("=" * 60)

def update_db_and_analyze(
    crawled_csv="output/crawled_products_sample.csv",
    recovered_csv="output/crawled_products_recovered.csv",
    mongo_uri="mongodb://127.0.0.1:27017/",
    db_name="countly",
    collection_name="products"
):
    """Gộp dữ liệu cũ + mới, nạp MongoDB và thu thập thống kê (ANALYZE)."""
    print("\nBẮT ĐẦU NẠP VÀO MONGODB & CẬP NHẬT SIÊU DỮ LIỆU (ANALYZE)...")
    
    dfs = []
    if os.path.exists(crawled_csv):
        dfs.append(pd.read_csv(crawled_csv))
    if os.path.exists(recovered_csv):
        dfs.append(pd.read_csv(recovered_csv))
        
    if not dfs:
        print(" Không có dữ liệu để nạp!")
        return
        
    df_merged = pd.concat(dfs, ignore_index=True)
    df_merged["product_id"] = df_merged["product_id"].astype(str).str.strip()
    df_merged = df_merged.sort_values(by=['product_id', 'product_name'], na_position='last')
    df_unique = df_merged.drop_duplicates(subset=['product_id'], keep='first').copy()
    df_unique = df_unique.where(pd.notnull(df_unique), None)

    # Lưu bản backup hợp nhất
    df_unique.to_csv("output/products_full.csv", index=False)
    print(f"Đã lưu file tổng hợp: output/products_full.csv ({len(df_unique):,} sản phẩm)")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db[collection_name]

    col.drop()
    records = df_unique.to_dict(orient='records')
    col.insert_many(records, ordered=False)

    # 1. Tạo Unique Index
    col.create_index("product_id", unique=True)

    # 2. Thu thập thống kê tương đương lệnh ANALYZE (collStats)
    stats = db.command("collStats", collection_name)

    # 3. Kiểm tra Query Execution Plan (Xác nhận Query Optimizer sử dụng Index)
    sample_id = records[0]["product_id"]
    explain_plan = col.find({"product_id": sample_id}).explain("executionStats")
    winning_plan = explain_plan.get("queryPlanner", {}).get("winningPlan", {})
    stage = winning_plan.get("stage", "UNKNOWN")
    input_stage = winning_plan.get("inputStage", {}).get("stage", "")
    is_ixscan = "IXSCAN" in [stage, input_stage]

    print("\n" + "=" * 60)
    print("BÁO CÁO SIÊU DỮ LIỆU & THỐNG KÊ (METADATA & STATISTICS)")
    print("=" * 60)
    print(f"  Collection Name          : {collection_name}")
    print(f"  Tổng số Documents         : {stats.get('count'):,}")
    print(f"  Dung lượng dữ liệu (Size): {stats.get('size') / 1024 / 1024:.2f} MB")
    print(f"  Số lượng Indexes         : {stats.get('nindexes')}")
    print(f"  Kế hoạch Query Optimizer : {'[OK] IXSCAN (Dùng Index tối ưu)' if is_ixscan else '[CANH BAO] COLLSCAN (Quét toàn bảng)'}")
    print("=" * 60)

if __name__ == "__main__":
    # 1. Chạy retry để cứu thêm sản phẩm
    run_retry(max_workers=5)
    # 2. Cập nhật vào DB và lấy thống kê
    # update_db_and_analyze()