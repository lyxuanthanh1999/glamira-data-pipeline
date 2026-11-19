"""
Glamira Project 05 - Data Pipeline Entrypoint
"""

def main():
    print("=" * 65)
    print("GLAMIRA E-COMMERCE DATA PIPELINE (PROJECT 05)")
    print("=" * 65)
    print("Các script chức năng theo Module trong thư mục 'src/':\n")
    print("--- [1. EXPLORATION - KHÁM PHÁ & ĐÁNH GIÁ DATA] ---")
    print("  1. uv run src/exploration/extract.py                 # Trích xuất 10K sample BSON -> JSON")
    print("  2. uv run src/exploration/date_exploration.py        # Thống kê Event & Schema-on-read")
    print("  3. uv run src/exploration/data_quality_assessment.py # Đánh giá 6 tiêu chí chất lượng data\n")
    print("--- [2. DATABASE - QUẢN LÝ MONGODB] ---")
    print("  4. uv run src/database/create_indexes.py             # Đánh index: ip, collection, product_id")
    print("  5. uv run src/database/load_data_to_mongodb.py       # Nạp 41M sự kiện thô vào 'summary'")
    print("  6. uv run src/database/load_products_mongo.py        # Nạp sản phẩm sạch vào 'products'\n")
    print("--- [3. ENRICHMENT - LÀM GIÀU VỊ TRÍ ĐỊA LÝ] ---")
    print("  7. uv run src/enrichment/enrich_ip_locations.py      # Tra cứu IP2Location -> 'ip_locations'\n")
    print("--- [4. CRAWLER - BÓC TÁCH WEB SẢN PHẨM] ---")
    print("  8. uv run src/crawler/extract_products.py           # Trích xuất danh sách Product IDs & URLs")
    print("  9. uv run src/crawler/crawl_products_full.py        # Cào chính thức đa luồng vượt Cloudflare")
    print(" 10. uv run src/crawler/retry_failed_products.py       # Cứu link lỗi qua Magento Fallback & Domain Rotation\n")
    print("--- [5. REPORTS - BÁO CÁO THỐNG KÊ] ---")
    print(" 11. uv run src/reports/generate_statistics.py        # Thống kê tiến trình & danh mục sản phẩm\n")
    print("=" * 65)
    print("Tài liệu dự án: 'docs/data_quality_report.md', 'docs/scope_confirmation.md', 'docs/data_dictionary.md'")
    print("Kế hoạch chi tiết: 'PLAN.md' | Hướng dẫn: 'README.md'")
    print("=" * 65)

if __name__ == "__main__":
    main()
