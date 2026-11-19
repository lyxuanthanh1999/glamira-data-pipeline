# 💎 Glamira E-Commerce Data Pipeline (Project 05)

Hệ thống Data Pipeline xử lý clickstream thương mại điện tử quốc tế của Glamira từ dữ liệu thô MongoDB BSON sang Cloud Data Warehouse (Phase 0 đến Phase 3).

---

## 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```
Project5/
├── data/                               # Dữ liệu mẫu phục vụ khám phá ban đầu
│   ├── sample.json                     # 10,000 sự kiện mẫu trích xuất từ summary.bson
│   └── summary.json                    # Backup dữ liệu mẫu
├── docs/                               # Tài liệu & Báo cáo kỹ thuật của dự án
│   ├── data_quality_report.md          # Báo cáo 6 tiêu chí chất lượng dữ liệu (Phase 0)
│   ├── scope_confirmation.md           # Biên bản chốt phạm vi dự án GO/NO-GO (Phase 0)
│   ├── crawl_statistics_report.md      # Báo cáo phân bố danh mục & tỷ lệ cào sản phẩm
│   └── data_dictionary.md              # Từ điển dữ liệu toàn diện 3 collections MongoDB
├── dump/                               # Dữ liệu thô gốc (BSON, BIN - không commit git)
│   ├── countly/summary.bson            # File sự kiện thô (~18GB, ~41 triệu documents)
│   └── IP-COUNTRY-REGION-CITY.BIN      # Cơ sở dữ liệu IP2Location ngoại tuyến
├── output/                             # Kết quả xử lý & làm giàu dữ liệu (Data Enrichment)
│   ├── ip_location_full.csv            # 2,035,839 IP duy nhất đã tra cứu (Độ phủ 98.99%)
│   ├── products_to_crawl_full.csv      # 19,232 Product ID & URL trích xuất từ events
│   ├── crawled_products_sample.csv     # 18,210 sản phẩm cào thành công ở đợt 1
│   ├── crawl_errors.log                # Log ghi nhận các URL lỗi (404/403)
│   ├── crawled_products_recovered.csv  # 658 sản phẩm cứu được qua Fallback & Domain Rotation
│   └── products_full.csv               # 18,868 sản phẩm hợp nhất sạch (Độ phủ 98.11%)
├── src/                                # Mã nguồn các script trong Data Pipeline
│   ├── config.py                       # Cấu hình đường dẫn, User-Agent & hàm parse HTML chung
│   ├── extract.py                      # Trích xuất 10,000 dòng mẫu từ file BSON
│   ├── date_exploration.py             # Phân tích schema-on-read & tỷ lệ NULL theo event type
│   ├── create_indexes.py               # Tạo indexes trên MongoDB để tăng tốc query
│   ├── enrich_ip_locations.py          # Làm giàu Geolocation người dùng qua IP2Location
│   ├── extract_products.py             # Trích xuất danh sách (product_id, url) cần cào
│   ├── crawl_products.py               # Bot cào thử nghiệm 100 sản phẩm (Test crawler)
│   ├── crawl_products_full.py          # Bot cào chính thức đa luồng vượt Cloudflare
│   ├── retry_failed_products.py        # Bot cứu hộ link lỗi qua Magento Fallback & Domain Rotation
│   ├── load_products_mongo.py          # Gộp dữ liệu, làm sạch, nạp vào MongoDB & lấy collStats
│   ├── load_data_to_mongodb.py         # Nạp toàn bộ sự kiện thô từ BSON vào MongoDB theo batch
│   ├── generate_statistics.py          # Tổng hợp và xuất báo cáo thống kê cào sản phẩm
│   └── report/
│       └── data_quality_assessment.py  # Đánh giá 6 tiêu chí chất lượng dữ liệu
├── .gitignore                          # Loại trừ file rác, file nhị phân lớn và virtualenv
├── PLAN.md                             # Kế hoạch chi tiết 11 Checkpoints dự án
├── pyproject.toml                      # Quản lý thư viện và môi trường với uv
└── uv.lock
```

---

## 🛠️ Chi Tiết Chức Năng Từng File Python Trong `src/`

Mỗi file Python đảm nhận **đúng một trách nhiệm (Single Responsibility Principle)** trong luồng xử lý:

| STT | Tên File | Giai đoạn | Chức năng chi tiết |
|:---:|:---|:---:|:---|
| **1** | [`config.py`](src/config.py) | *Toàn bộ* | Quản lý đường dẫn tuyệt đối (`Path`) tập trung, khởi tạo User-Agent ngẫu nhiên và các cấu hình chung để tránh lỗi `FileNotFoundError`. |
| **2** | [`extract.py`](src/extract.py) | **Phase 0** | Đọc tuần tự luồng nhị phân từ `dump/countly/summary.bson` và trích xuất đúng 10,000 dòng mẫu ra `data/sample.json` giúp khám phá dữ liệu nhanh chóng mà không cần nạp cả file 18GB. |
| **3** | [`date_exploration.py`](src/date_exploration.py) | **Phase 0** | Đọc dữ liệu mẫu, đếm số lượng từng loại sự kiện (`collection`), đo tỷ lệ NULL của các trường theo từng event type để chứng minh bản chất **Schema-on-read**. |
| **4** | [`report/data_quality_assessment.py`](src/report/data_quality_assessment.py) | **Phase 0** | Kiểm tra 6 tiêu chí dữ liệu: Duplicate `_id`, Duplicate `(ip, time_stamp)`, dải ngày bất thường, doanh thu âm, tiền tệ quốc tế và chuẩn IPv4 làm cơ sở viết `data_quality_report.md`. |
| **5** | [`create_indexes.py`](src/create_indexes.py) | **Phase 1** | Kết nối MongoDB local/VM, tạo chỉ mục B-Tree trên 3 trường quan trọng của collection `summary`: `ip_1`, `collection_1`, `product_id_1` để tăng tốc truy vấn gấp 20-50 lần. |
| **6** | [`load_data_to_mongodb.py`](src/load_data_to_mongodb.py) | **Phase 1** | Đọc file `summary.bson` theo khối (`batch_size=10,000`), bổ sung metadata truy vết (`_loaded_at`, `_source_file`) và nạp vào collection `countly.summary` bằng `insert_many(ordered=False)`. |
| **7** | [`enrich_ip_locations.py`](src/enrich_ip_locations.py) | **Phase 2** | Dùng Covered Index Scan quét nhanh IP duy nhất từ `countly.summary`, tra cứu qua database nhị phân `IP-COUNTRY-REGION-CITY.BIN` để lấy Quốc gia, Vùng, Thành phố. Lưu vào collection `countly.ip_locations` và xuất `output/ip_location_full.csv`. |
| **8** | [`extract_products.py`](src/extract_products.py) | **Phase 2** | Quét các sự kiện liên quan sản phẩm (`view_product_detail`, `add_to_cart`, `checkout_success`), bóc tách danh sách cặp `(product_id, product_url)` duy nhất, lọc bỏ URL rác và xuất ra `output/products_to_crawl_full.csv`. |
| **9** | [`crawl_products.py`](src/crawl_products.py) | **Phase 2** | Script cào thử nghiệm (Checkpoint #10) trên 100 sản phẩm mẫu để kiểm tra bộ bóc tách HTML (BeautifulSoup) và kiểm tra khả năng vượt bot-detection của Glamira. |
| **10** | [`crawl_products_full.py`](src/crawl_products_full.py) | **Phase 2** | Bot cào chính thức đa luồng (`ThreadPoolExecutor` 5 workers), dùng `curl_cffi` giả lập TLS Chrome 120 vượt Cloudflare, có cơ chế checkpoint tự động bỏ qua ID đã cào. Cào thành công 18,210 sản phẩm. |
| **11** | [`retry_failed_products.py`](src/retry_failed_products.py) | **Phase 2** | Bot cứu hộ sản phẩm lỗi (Resilient Scraping) bằng kỹ thuật: <br>1. Fallback URL router Magento: `/catalog/product/view/id/{id}/`<br>2. Domain Rotation luân phiên 6 tên miền (`.com`, `.de`, `.co.uk`, `.fr`, `.es`, `.ca`).<br>Cứu thêm 658 sản phẩm lỗi, nâng độ phủ lên 98.11%. |
| **12** | [`load_products_mongo.py`](src/load_products_mongo.py) | **Phase 2** | Gộp kết quả cào lần 1 và đợt cứu hộ, chuẩn hóa khoảng trắng của `price`, bù đắp trường thiếu (`description`, `sku`), xuất file chuẩn `output/products_full.csv`, nạp vào collection `countly.products`, tạo Unique Index và thu thập siêu dữ liệu (`collStats`). |
| **13** | [`generate_statistics.py`](src/generate_statistics.py) | **Phase 2** | Phân tích file sản phẩm hợp nhất, đếm top danh mục sản phẩm, tính toán tỷ lệ hoàn thành và tự động tạo báo cáo `docs/crawl_statistics_report.md`. |

---

## 🚀 Hướng Dẫn Chạy Các Script Bằng `uv`

Dự án sử dụng trình quản lý gói hiện đại **`uv`**. Tất cả câu lệnh đều thực hiện tại thư mục gốc `Project5/`:

### 0. Cài đặt môi trường
```bash
uv sync
```

---

### Phase 0: Khám Phá & Đánh Giá Chất Lượng Dữ Liệu
```bash
# 1. Trích xuất 10,000 dòng mẫu từ file BSON
uv run src/extract.py

# 2. Khám phá sự kiện và phân tích tỷ lệ NULL (Schema-on-read)
uv run src/date_exploration.py

# 3. Chạy báo cáo kiểm định 6 tiêu chí chất lượng dữ liệu
uv run src/report/data_quality_assessment.py
```

---

### Phase 1: Tạo Index & Nạp Dữ Liệu Raw Vào MongoDB
```bash
# 1. Tạo chỉ mục (Index) trên MongoDB local/VM
uv run src/create_indexes.py

# 2. Nạp toàn bộ dữ liệu sự kiện thô từ file summary.bson vào MongoDB (nếu nạp bằng Python)
uv run src/load_data_to_mongodb.py
```
*(Hoặc trên môi trường Linux/VM, bạn có thể nạp nhanh bằng công cụ dòng lệnh:)*
```bash
mongorestore --db=countly --collection=summary dump/countly/summary.bson
```

---

### Phase 2: Làm Giàu Dữ Liệu (IP Geolocation & Product Crawling)

```bash
# 1. Làm giàu vị trí địa lý từ IP (Checkpoint #8)
uv run src/enrich_ip_locations.py

# 2. Trích xuất danh sách sản phẩm cần cào (Checkpoint #9)
uv run src/extract_products.py

# 3. Chạy bot cào sản phẩm đa luồng vượt Cloudflare (Checkpoint #10, #11)
uv run src/crawl_products_full.py

# 4. Chạy bot cứu hộ các sản phẩm bị lỗi 404/403 qua Domain Rotation
uv run src/retry_failed_products.py

# 5. Gộp dữ liệu, làm sạch và nạp sản phẩm vào MongoDB countly.products
uv run src/load_products_mongo.py

# 6. Tạo báo cáo thống kê danh mục sản phẩm
uv run src/generate_statistics.py
```

---

## 📊 Kết Quả Đạt Được Đến Hiện Tại

1. **IP Geolocation**: Đã ánh xạ thành công **2,035,839 IP duy nhất**, đạt tỷ lệ phủ sóng **98.99%** (Yêu cầu đề bài $\ge 80\%$).
2. **Product Enrichment**: Đã cào và cứu thành công **18,868 / 19,232 sản phẩm**, đạt tỷ lệ phủ sóng **98.11%** (Yêu cầu đề bài $\ge 80\%$).
3. **Database MongoDB Local**:
   - `countly.summary`: Chứa dữ liệu sự kiện thô với các index tối ưu `ip`, `collection`, `product_id`.
   - `countly.ip_locations`: Chứa dữ liệu địa lý IP (Quốc gia, Thành phố) có index `ip`.
   - `countly.products`: Chứa thông tin sản phẩm (Tên, Danh mục, Giá, Mô tả, SKU, URL) có Unique Index `product_id`.
