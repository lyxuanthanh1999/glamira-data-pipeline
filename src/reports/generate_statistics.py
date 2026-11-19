"""
Glamira Project 05 - Thống Kê Toàn Diện Dữ Liệu (Pipeline & Crawl Statistics)
Mục tiêu:
1. Thống kê tiến độ & chất lượng cào dữ liệu sản phẩm (Crawl & Recovery Coverage).
2. Thống kê phân bố danh mục (Categories) và trạng thái dữ liệu (Missing rate).
3. Thống kê phân tích các loại lỗi phát sinh khi cào (HTTP 403, Timeout, ...).
4. Thống kê kết quả làm giàu dữ liệu địa lý IP (IP Geolocation).
5. Kiểm tra nhanh số lượng documents trong MongoDB (nếu có kết nối).
"""

import os
import pandas as pd
from pymongo import MongoClient

TARGET_PRODUCTS_CSV = "output/products_to_crawl_full.csv"
CRAWLED_SAMPLE_CSV = "output/crawled_products_sample.csv"
CRAWLED_RECOVERED_CSV = "output/crawled_products_recovered.csv"
CRAWL_ERRORS_LOG = "output/crawl_errors.log"
IP_LOCATION_CSV = "output/ip_location_full.csv"
REPORT_MD_PATH = "docs/crawl_statistics_report.md"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)

def generate_statistics():
    print_section("BÁO CÁO THỐNG KÊ TIẾN TRÌNH & DỮ LIỆU GLAMIRA PROJECT 05")

    # -------------------------------------------------------------
    # 1. THỐNG KÊ CÀO DỮ LIỆU SẢN PHẨM (WEB SCRAPING PERFORMANCE)
    # -------------------------------------------------------------
    total_target = 0
    pids_target = set()
    if os.path.exists(TARGET_PRODUCTS_CSV):
        df_target = pd.read_csv(TARGET_PRODUCTS_CSV)
        pids_target = set(df_target["product_id"].astype(str))
        total_target = len(pids_target)

    pids_sample = set()
    df_sample = pd.DataFrame()
    if os.path.exists(CRAWLED_SAMPLE_CSV):
        df_sample = pd.read_csv(CRAWLED_SAMPLE_CSV)
        pids_sample = set(df_sample["product_id"].astype(str))

    pids_rec = set()
    df_rec = pd.DataFrame()
    if os.path.exists(CRAWLED_RECOVERED_CSV):
        df_rec = pd.read_csv(CRAWLED_RECOVERED_CSV)
        pids_rec = set(df_rec["product_id"].astype(str))

    combined_pids = pids_sample.union(pids_rec)
    total_crawled_unique = len(combined_pids)
    remaining_pids = pids_target - combined_pids
    coverage_rate = (total_crawled_unique / total_target * 100) if total_target > 0 else 0.0

    print("\n1. TIẾN ĐỘ CÀO DỮ LIỆU SẢN PHẨM (PRODUCT CRAWLING):")
    print(f"   - Tổng số sản phẩm mục tiêu (Target)      : {total_target:,} sản phẩm")
    print(f"   - Cào thành công đợt 1 (Full crawl)       : {len(pids_sample):,} sản phẩm")
    print(f"   - Cứu hộ thành công đợt 2 (Recovery crawl): {len(pids_rec):,} sản phẩm")
    print(f"   - Tổng sản phẩm độc nhất thu được         : {total_crawled_unique:,} / {total_target:,}")
    print(f"   - TỶ LỆ HOÀN THÀNH (COVERAGE RATE)     : {coverage_rate:.2f}%")
    print(f"   - Số lượng còn sót chưa cào được          : {len(remaining_pids):,} sản phẩm")

    # Gộp dữ liệu sản phẩm để phân tích chất lượng
    frames = []
    cols_needed = ["product_id", "product_name", "category", "price", "url"]
    for d in [df_sample, df_rec]:
        if not d.empty:
            avail_cols = [c for c in cols_needed if c in d.columns]
            frames.append(d[avail_cols])

    if frames:
        df_products = pd.concat(frames, ignore_index=True)
        df_products["product_id"] = df_products["product_id"].astype(str)
        df_products = df_products.sort_values(by=["product_id", "product_name"], na_position="last")
        df_products = df_products.drop_duplicates(subset=["product_id"], keep="first")

        print("\n2. CHẤT LƯỢNG DỮ LIỆU SẢN PHẨM (DATA QUALITY):")
        total_prod = len(df_products)
        has_name = df_products["product_name"].notnull().sum()
        has_cat = df_products["category"].notnull().sum()
        has_price = df_products["price"].notnull().sum()

        print(f"   - Có Tên sản phẩm (product_name) : {has_name:,} / {total_prod:,} ({has_name/total_prod*100:.1f}%)")
        print(f"   - Có Danh mục (category)         : {has_cat:,} / {total_prod:,} ({has_cat/total_prod*100:.1f}%)")
        print(f"   - Có Giá niêm yết (price)        : {has_price:,} / {total_prod:,} ({has_price/total_prod*100:.1f}%)")
        print(f"   - Sản phẩm ngưng kinh doanh/rỗng : {total_prod - has_name:,} ({((total_prod - has_name)/total_prod)*100:.1f}%)")

        print("\n3. TOP 10 DANH MỤC PHỔ BIẾN NHẤT:")
        top_cats = df_products["category"].value_counts().head(10)
        for rank, (cat, cnt) in enumerate(top_cats.items(), 1):
            print(f"   {rank:>2}. {cat:<32}: {cnt:>5,} sản phẩm ({cnt/total_prod*100:>4.1f}%)")

    # -------------------------------------------------------------
    # 2. THỐNG KÊ LỖI PHÁT SINH KHI CÀO (ERROR ANALYSIS)
    # -------------------------------------------------------------
    if os.path.exists(CRAWL_ERRORS_LOG):
        df_err = pd.read_csv(CRAWL_ERRORS_LOG)
        print("\n[CANH BAO] 4. PHÂN TÍCH LỖI KHI CÀO WEB (CRAWL ERROR LOG):")
        print(f"   - Tổng số lượt request gặp lỗi : {len(df_err):,}")
        if "status" in df_err.columns:
            err_counts = df_err["status"].value_counts()
            for status, cnt in err_counts.items():
                print(f"     + Mã lỗi {status:<15}: {cnt:>5,} lần ({cnt/len(df_err)*100:.1f}%)")

    # -------------------------------------------------------------
    # 3. THỐNG KÊ DỮ LIỆU IP GEOLOCATION
    # -------------------------------------------------------------
    if os.path.exists(IP_LOCATION_CSV):
        print("\n5. THỐNG KÊ LÀM GIÀU DỮ LIỆU ĐỊA LÝ (IP GEOLOCATION):")
        # Đọc 200,000 dòng mẫu hoặc toàn bộ để lấy top countries
        df_ip = pd.read_csv(IP_LOCATION_CSV, nrows=300000)
        total_ip_rows = sum(1 for _ in open(IP_LOCATION_CSV)) - 1
        valid_countries = df_ip[df_ip["country_name"] != "-"]
        print(f"   - Tổng số IP duy nhất đã tra cứu  : {total_ip_rows:,} IP")
        print(f"   - Tỷ lệ phủ sóng quốc gia         : {len(valid_countries)/len(df_ip)*100:.2f}%")
        print("   - Top 5 Quốc gia có lượng truy cập lớn nhất (Mẫu):")
        for rank, (c_name, cnt) in enumerate(valid_countries["country_name"].value_counts().head(5).items(), 1):
            print(f"     {rank}. {c_name:<20}: {cnt:>6,} IP")

    # -------------------------------------------------------------
    # 4. KIỂM TRA MONGODB COLLECTIONS
    # -------------------------------------------------------------
    print("\n6. KIỂM TRA DỮ LIỆU TRONG MONGODB:")
    try:
        client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=2000)
        db = client["countly"]
        col_names = db.list_collection_names()
        print(f"   - Các collections hiện có: {col_names}")
        for col_name in ["summary", "ip_locations", "products"]:
            if col_name in col_names:
                cnt = db[col_name].count_documents({})
                print(f"     + {col_name:<15}: {cnt:>10,} documents")
            else:
                print(f"     + {col_name:<15}: [FAIL] Chưa tạo")
        client.close()
    except Exception as e:
        print(f"   [CANH BAO] Không thể kết nối MongoDB (Chưa bật service hoặc cần port forwarding): {e}")

    # -------------------------------------------------------------
    # 5. XUẤT BÁO CÁO MARKDOWN
    # -------------------------------------------------------------
    os.makedirs(os.path.dirname(REPORT_MD_PATH), exist_ok=True)
    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f_out:
        f_out.write(f"# Glamira Project 05 - Báo Cáo Thống Kê Toàn Diện\n\n")
        f_out.write(f"- **Ngày thống kê**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f_out.write(f"- **Tiến độ cào sản phẩm**: {coverage_rate:.2f}% ({total_crawled_unique:,} / {total_target:,} sản phẩm)\n")
        f_out.write(f"- **Số sản phẩm cứu hộ qua retry**: {len(pids_rec):,} sản phẩm\n")
        f_out.write(f"- **Dữ liệu IP Geolocation**: {total_ip_rows if 'total_ip_rows' in locals() else 'N/A':,} IP duy nhất\n\n")
        f_out.write(f"## Top Danh Mục Sản Phẩm Đã Cào Được\n\n")
        if 'top_cats' in locals():
            f_out.write(f"| Hạng | Tên Danh Mục | Số lượng | Tỷ lệ |\n|:---:|:---|:---:|:---:|\n")
            for rank, (cat, cnt) in enumerate(top_cats.items(), 1):
                f_out.write(f"| {rank} | {cat} | {cnt:,} | {cnt/total_prod*100:.1f}% |\n")

    print(f"\nĐã tự động xuất file báo cáo Markdown: '{REPORT_MD_PATH}'")
    print("=" * 70)

if __name__ == "__main__":
    generate_statistics()

