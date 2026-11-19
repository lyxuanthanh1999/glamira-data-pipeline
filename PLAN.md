# 📋 KẾ HOẠCH DỰ ÁN GLAMIRA PROJECT 05 & TIẾN ĐỘ THỰC HIỆN

> **Nguyên tắc cốt lõi**: *Hiểu data trước, code sau. Mỗi checkpoint = 1 khái niệm, ≤ 2 giờ. Xong → commit → push GitHub → mới sang bước tiếp theo.*

---

## 📊 TỔNG QUAN TIẾN ĐỘ (PROGRESS TRACKER)

- **Trạng thái hiện tại**: Đã **HOÀN THÀNH 11/11 CHECKPOINTS (PHASE 0, 1 & 2)** 🎉
- **Tiến độ Micro-checkpoints**: **11 / 11 Checkpoints hoàn thành** (100% Phase 0, 1, 2)
- **Mục tiêu tiếp theo**: Bước vào **PHASE 3 — CLOUD DATA WAREHOUSE (BIGQUERY)**

```
[████████████████████] 100% Complete (Phase 0, 1, 2)
Phase 0: [██████████] 100% (Hoàn thành!)
Phase 1: [██████████] 100% (GCS, MongoDB VM, 41.4M rows loaded!)
Phase 2: [██████████] 100% (IP 98.99%, Product Crawl 98.11%, Data Dictionary done!)
Phase 3: [░░░░░░░░░░] 0%   (Sẵn sàng: BigQuery & Star Schema)
```

---

## 📅 LỘ TRÌNH 11 MICRO-CHECKPOINTS CHI TIẾT

| # | Phase | Checkpoint | Khái niệm cốt lõi | Thời gian | Trạng thái |
|:---:|:---:|---|---|:---:|:---:|
| **1** | **0** | **NULL % theo từng event type đã đo xong** | Local exploration, schema-on-read | 2h | [x] **HOÀN THÀNH** |
| **2** | **0** | **`data_quality_report.md` viết xong** | Data quality assessment | 2h | [x] **HOÀN THÀNH** |
| **3** | **0** | **`scope_confirmation.md` có GO decision: IP & Product** | Scope decision | 1h | [x] **HOÀN THÀNH** |
| **4** | **1** | **GCP project + APIs enabled, GCS bucket tạo + test upload** | Cloud IAM, Object storage | 2h | [x] **HOÀN THÀNH** |
| **5** | **1** | **UV project init, `uv sync` chạy được** | Modern Python tooling | 30' | [x] **HOÀN THÀNH** |
| **6** | **1** | **MongoDB VM up, connect từ local OK** | SSH, Linux service, firewall | 2h | [x] **HOÀN THÀNH** |
| **7** | **1** | **Load full 41M rows — row count match** | Chunked processing / mongorestore | 3h | [x] **HOÀN THÀNH** (41,432,473 rows) |
| **8** | **2** | **IP geolocation xong, coverage % đo được** | External DB lookup | 2h | [x] **HOÀN THÀNH** (98.99% coverage) |
| **9** | **2** | **Product IDs + URLs extracted (set unique)** | Set deduplication | 1h | [x] **HOÀN THÀNH** (19,232 products) |
| **10** | **2** | **Crawl 100 products test — HTML parse OK** | Web scraping basics | 2h | [x] **HOÀN THÀNH** |
| **11** | **2** | **Crawl toàn bộ + `data_dictionary.md` hoàn chỉnh** | Rate limiting, upsert, domain rotate | 4h | [x] **HOÀN THÀNH** (18,868 items - 98.11%) |

---

## 🎯 CHI TIẾT TỪNG GIAI ĐOẠN

### 🎯 PHASE 0: DATA INVESTIGATION (Khám phá dữ liệu)
*Mục tiêu: Hiểu data và confirm scope TRƯỚC KHI tốn tiền GCP và thời gian setup.*

- [x] **Step 0.1: Setup Python Project & Trích xuất Sample**
  - [x] Cài đặt UV, khởi tạo project (`pyproject.toml`, `uv.lock`)
  - [x] Tạo file `extract.py` trích xuất 10,000 dòng mẫu từ `summary.bson` ra `sample.json`
  - [x] Cập nhật `.gitignore` loại trừ file nặng (`dump/`, `*.bson`, `*.tar.gz`, `*.BIN`)
  - [x] Tạo script `date_exploration.py` đo số lượng từng loại `collection`
  - *Checkpoint #1 Passed: Đã in ra được list event types và số dòng mỗi loại.*

- [x] **Step 0.2: Schema & NULL Analysis**
  - [x] Đo tỷ lệ NULL theo từng event type trong `date_exploration.py`
  - [x] Phát hiện `checkout_success` có `order_id`, các event khác 100% NULL
  - [x] Khẳng định bản chất **Schema-on-read** (thiết kế có chủ đích, không phải lỗi data)
  - *Checkpoint #1 Passed: Đã giải thích được lý do NULL pattern khác nhau.*

- [x] **Step 0.3: Data Quality Assessment**
  - [x] Viết `data_quality_assessment.py` kiểm tra 6 tiêu chí: NULL, Duplicate, Date range, Revenue, Currency, IP format.
  - [x] Phát hiện 5 loại tiền tệ (`€`, `CHF`, `£`, `$`, `kr`) và định dạng giá tiền Châu Âu.
  - [x] Tạo báo cáo hoàn chỉnh: [data_quality_report.md](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/docs/data_quality_report.md)
  - *Checkpoint #2 Passed: File `data_quality_report.md` có đầy đủ số liệu thực tế.*

- [x] **Step 0.4: Scope Confirmation**
  - [x] Trả lời 3 câu hỏi phạm vi (IP Location, Product Crawling, Full 41M rows)
  - [x] Tạo file `scope_confirmation.md` với quyết định GO/NO-GO
  - *Checkpoint #3 Passed: Đã chốt GO decision, đủ điều kiện bước sang Phase 1.*

---

### 🏗️ PHASE 1: INFRASTRUCTURE & FULL DATA LOADING (Hạ tầng Cloud & Nạp dữ liệu)
*Mục tiêu: Setup GCP và nạp toàn bộ 41M dòng vào MongoDB khi đã biết rõ scope.*

- [x] **Step 1.1: GCP + GCS Setup**
  - [x] Tạo GCP Project, enable Compute Engine, GCS, BigQuery APIs
  - [x] Tạo Cloud Storage Bucket `glamira-raw-data-thanh-asia-se1`
  - [x] Test upload file mẫu thành công lên GCS console.
  - *Checkpoint #4 Passed.*

- [x] **Step 1.1b: UV Project Setup**
  - [x] `uv sync` chạy mượt mà, quản lý virtualenv reproducible.
  - *Checkpoint #5 Passed.*

- [x] **Step 1.2: VM + MongoDB Setup**
  - [x] Tạo Compute Engine VM `glamira-mongo-vm` (Ubuntu 22.04 LTS, 100GB disk, 4 vCPU, 16GB RAM, Spot)
  - [x] SSH vào VM, cài đặt MongoDB 6.0
  - [x] Cấu hình `bindIp: 0.0.0.0` và Firewall rule mở port 27017
  - [x] Test kết nối `mongosh` từ máy local thành công vào VM
  - *Checkpoint #6 Passed: Kết nối từ local vào VM thành công, không lỗi auth.*

- [x] **Step 1.3: Full Data Loading (3 hours)**
  - [x] Đưa dữ liệu 41M rows vào máy ảo qua GCS staging bucket
  - [x] Nạp dữ liệu vào MongoDB collection `summary` bằng `mongorestore` song song (11 phút)
  - [x] Validate row count: `db.summary.countDocuments()` = 41,432,473 (khớp 100% file BSON)
  - [x] Tạo Index trên: `time_stamp`, `device_id`
  - [x] Nạp dữ liệu `ip_locations` và `products` vào MongoDB qua `mongoimport`
  - [x] ⚠️ **Tắt VM instance trên GCP sau khi load xong để dừng tính phí compute!**
  - *Checkpoint #7 Passed: Row count khớp 41,432,473 / 41,432,473 (0 failed).*

---

### 🔍 PHASE 2: DATA ENRICHMENT (CONDITIONAL) (Làm giàu dữ liệu)
*Mục tiêu: Bổ sung Country/City từ IP và Crawl thông tin sản phẩm.*

- [x] **Step 2.1: IP Location Processing (2 hours)**
  - [x] Cài đặt `uv add ip2location-python`
  - [x] Dùng database `IP-COUNTRY-REGION-CITY.BIN` có sẵn
  - [x] Viết `enrich_ip_locations.py` tra cứu trên 2,035,839 Unique IPs
  - [x] Lưu kết quả vào MongoDB `ip_locations` và xuất backup `output/ip_location_full.csv` (Độ bao phủ 98.99%)
  - *Checkpoint #8 Passed: Coverage 98.99% ≥ 80%, CSV export xong.*

- [x] **Step 2.2: Product Information Collection (8 hours)**
  - [x] **Step 2.2a**: Extract unique `(product_id, url)` set từ các event tương tác sản phẩm (19,232 sản phẩm) (*Checkpoint #9 Passed*)
  - [x] **Step 2.2b**: Viết parser chuẩn `parse_glamira_html` trong `src/config.py`, test cào sản phẩm (*Checkpoint #10 Passed*)
  - [x] **Step 2.2c**: Crawl toàn bộ danh sách sản phẩm với đa luồng, xoay vòng domain quốc tế (`.com`, `.de`, `.co.uk`, `.fr`, `.es`, `.ca`) và Magento Fallback routing (`/catalog/product/view/id/{id}`). Cứu thành công 18,868 sản phẩm (Độ bao phủ **98.11%**), lưu vào `countly.products` và xuất `output/products_full.csv` (*Checkpoint #11 Passed*)

- [x] **Step 2.3: Data Dictionary (2 hours)**
  - [x] Viết `docs/data_dictionary.md` tài liệu hóa đầy đủ 3 collections: `summary`, `ip_locations`, `products`, quy tắc Listed Price vs Checkout Price, và Schema-on-Read.

---

### 🚀 PHASE 3: CLOUD DATA WAREHOUSE & ANALYTICS (Sắp tới ⭐)
*Mục tiêu: Xây dựng Star Schema trên BigQuery, tính toán doanh thu FX, trực quan hóa Dashboard.*

- [ ] **Step 3.1: Data Modeling & Schema Design** (Fact table: `fact_events`, Dim tables: `dim_product`, `dim_location`, `dim_date`)
- [ ] **Step 3.2: BigQuery Staging & ETL** (Chuyển dữ liệu sang BigQuery, Currency Normalization về USD)
- [ ] **Step 3.3: Business KPI Analytics & Dashboard** (Looker Studio / Power BI)

---

## 📋 BẢNG CHECKLIST SẢN PHẨM NỘP (DELIVERABLES)

- [x] [date_exploration.py](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/src/exploration/date_exploration.py) (Script khám phá dữ liệu mẫu)
- [x] [data_quality_report.md](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/docs/data_quality_report.md) (Báo cáo chất lượng dữ liệu)
- [x] [scope_confirmation.md](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/docs/scope_confirmation.md) (Quyết định phạm vi GO/NO-GO ⭐)
- [x] [crawl_statistics_report.md](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/docs/crawl_statistics_report.md) (Báo cáo thu thập sản phẩm)
- [x] [data_dictionary.md](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/docs/data_dictionary.md) (Từ điển dữ liệu hoàn chỉnh ⭐)
- [x] GCP Bucket `gs://glamira-raw-data-thanh-asia-se1` + Compute Engine VM hoạt động
- [x] Full 41.4M events nạp thành công vào MongoDB `countly.summary`
- [x] [enrich_ip_locations.py](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/src/enrichment/enrich_ip_locations.py) + `ip_location_full.csv`
- [x] [extract_products.py](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/src/crawler/extract_products.py)
- [x] [crawl_products_full.py](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/src/crawler/crawl_products_full.py) + [retry_failed_products.py](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/src/crawler/retry_failed_products.py) + `products_full.csv`
- [x] [.gitignore](file:///Users/lyxuanthanh/Documents/DataEngineer/Project5/.gitignore) đã loại trừ file lớn và credentials
- [ ] GitHub Repository được commit đầy đủ
