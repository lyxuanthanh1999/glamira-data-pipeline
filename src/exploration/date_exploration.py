"""
Glamira Project 05 - Phase 0: Data Exploration (Checkpoint #1)
Mục tiêu:
1. Nạp và khám phá tập dữ liệu mẫu (10,000 dòng từ dump/countly/summary.bson)
2. Thống kê số lượng từng loại sự kiện (collection)
3. Xác định dải thời gian (min / max timestamp)
4. Phân tích tỷ lệ NULL theo từng event type để chứng minh bản chất Schema-on-read
"""

import os
import json
import pandas as pd
from datetime import datetime

# Đường dẫn file mẫu (ưu tiên data/sample.json, fallback sample.json)
SAMPLE_PATHS = ["data/sample.json", "sample.json"]

def load_sample_data():
    for path in SAMPLE_PATHS:
        if os.path.exists(path):
            print(f" Đang nạp dữ liệu từ: {path}")
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            return pd.DataFrame(raw_data)
    raise FileNotFoundError(f"[FAIL] Không tìm thấy file mẫu trong các đường dẫn: {SAMPLE_PATHS}")

def explore_data():
    print("=" * 65)
    print(" PHASE 0 - STEP 0.1 & 0.2: DATA EXPLORATION & SCHEMA ANALYSIS")
    print("=" * 65)

    df = load_sample_data()

    # 1. Thông tin tổng quan tập dữ liệu
    print(f"\n 1. TỔNG QUAN TẬP DỮ LIỆU:")
    print(f"   - Kích thước DataFrame : {df.shape[0]:,} dòng x {df.shape[1]} cột")
    print(f"   - Số lượng IP duy nhất : {df['ip'].nunique():,} / {len(df):,} ({df['ip'].nunique()/len(df)*100:.2f}%)")

    # 2. Dải thời gian
    if "time_stamp" in df.columns:
        min_ts = df["time_stamp"].min()
        max_ts = df["time_stamp"].max()
        min_date = datetime.fromtimestamp(min_ts)
        max_date = datetime.fromtimestamp(max_ts)
        print(f"   - Dải thời gian (Timestamp): {min_date} → {max_date}")

    # 3. Thống kê theo từng Event Type (collection)
    print(f"\n 2. PHÂN BỐ CÁC LOẠI EVENT (COLLECTION):")
    event_counts = df["collection"].value_counts()
    for event, count in event_counts.items():
        pct = count / len(df) * 100
        print(f"   - {event:<38}: {count:>5,} dòng ({pct:>5.2f}%)")

    # 4. Phân tích tỷ lệ NULL theo từng Event Type (Schema-on-read Discovery)
    print(f"\n 3. PHÂN TÍCH SCHEMA-ON-READ & TỶ LỆ NULL THEO EVENT TYPE:")
    key_fields = ["product_id", "order_id", "cart_products", "ip", "current_url"]
    
    # Chỉ hiển thị các fields có trong DataFrame
    check_fields = [f for f in key_fields if f in df.columns]

    target_events = [
        "view_product_detail",
        "select_product_option",
        "add_to_cart_action",
        "checkout_success",
        "view_listing_page"
    ]

    for event in target_events:
        subset = df[df["collection"] == event]
        if subset.empty:
            continue
        print(f"\n   Event: '{event}' ({len(subset):,} dòng):")
        for f in check_fields:
            null_count = subset[f].isna().sum()
            null_rate = null_count / len(subset) * 100
            print(f"      - {f:<15} NULL: {null_count:>5,} / {len(subset):<5} ({null_rate:>5.1f}%)")

    print("\n" + "=" * 65)
    print("KẾT LUẬN QUAN TRỌNG (KEY DISCOVERY):")
    print("   - Sự kiện 'checkout_success' chứa order_id, cart_products và revenue.")
    print("   - Các sự kiện xem hàng ('view_product_detail',...) có product_id nhưng không có order_id.")
    print("   -> Đây là bản chất SCHEMA-ON-READ của MongoDB (thiết kế có chủ đích, không phải lỗi dữ liệu).")
    print("=" * 65)

if __name__ == "__main__":
    explore_data()

