# Scope Confirmation — Glamira Project 05

**Ngày quyết định**: 2026-11-10  
**Người thực hiện**: Data Engineer  
**Trạng thái**: Approved (GO)  

---

## Question 1: Có cần IP Location không?
- **Yêu cầu Dashboard**: Cần báo cáo phân tích hiệu suất địa lý (Geographic Performance) — ví dụ: *"Doanh thu ở Đức cao hơn Pháp không?"*.
- **Data thực tế trong Raw Events**: 
  - Đã kiểm tra ở Phase 0: Chỉ có địa chỉ `ip` (ví dụ: `85.115.53.202`).
  - Hoàn toàn **KHÔNG CÓ** trường `country` hay `city`.
- **Decision: [ BUILD ]**
- **Lý do**: Bắt buộc phải dùng cơ sở dữ liệu ngoại tuyến IP2Location (`IP-COUNTRY-REGION-CITY.BIN`) để làm giàu dữ liệu (Enrichment), ánh xạ từ `IP -> Country, City` ở Phase 2 (Step 2.1).

---

## Question 2: Có cần Product Crawling không?
- **Yêu cầu Dashboard**: Cần báo cáo phân tích sản phẩm (Product Analysis) — ví dụ: *"Nhẫn bán chạy hơn vòng tay không?"*.
- **Data thực tế trong Raw Events**: 
  - Đã kiểm tra ở Phase 0: Sự kiện `view_product_detail` và `checkout_success` chỉ có `product_id` (ví dụ: `96047`) và đường link `current_url`.
  - Hoàn toàn **KHÔNG CÓ** trường `product_name` hay `category`.
- **Decision: [ BUILD ]**
- **Lý do**: Bắt buộc phải viết web crawler (dùng BeautifulSoup) để cào trang web Glamira theo `current_url` nhằm lấy `name` và `category` ở Phase 2 (Step 2.2).

---

## Question 3: Cần load bao nhiêu data?
- **Tùy chọn kỹ thuật**:
  - Sample 100K rows: Có thể nạp thẳng BigQuery.
  - Full 41M rows (~20GB BSON): Cần máy ảo GCP VM + cài đặt MongoDB.
- **Decision: [ FULL ]**
- **Lý do**: Project 05 yêu cầu xử lý dữ liệu ở quy mô thực tế (Production-scale) của 2 tháng (10/2019 - 11/2019), rèn luyện kỹ năng xử lý theo khối (Chunked batching), đánh chỉ mục (Indexing) và quản trị cơ sở dữ liệu MongoDB trên Linux.

---

## 🚀 GO / NO-GO DECISION
- [x] **GO: Chấp thuận triển khai Hạ tầng Cloud ở Phase 1**
- **Phạm vi chốt lại (Confirmed Scope)**:
  - Tra cứu vị trí địa lý (IP Location): **YES**
  - Cào dữ liệu sản phẩm (Product Crawling): **YES**
  - Nạp toàn bộ dữ liệu (Full 41M Data): **YES**
