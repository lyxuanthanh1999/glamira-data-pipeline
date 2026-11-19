# Data Quality Report — Sample (10K rows)

**Ngày thực hiện**: 2026-11-10  
**Tập dữ liệu**: Sample trích xuất từ `dump/countly/summary.bson`  
**Dung lượng mẫu**: 10,000 documents  

---

## 1. Executive Summary (Bảng tóm tắt đánh giá chất lượng)
| Tiêu chí kiểm tra (Check) | Kết quả thực tế (Result) | Đánh giá | Cần hành động? (Action Needed) |
|---|---|:---:|---|
| **Trùng lặp Document ID (`_id`)** | 0 dòng (0.00%) |  Đạt | **No** — Mỗi document là duy nhất |
| **Trùng lặp cặp (`ip`, `time_stamp`)** | 119 dòng (1.19%) | ⚠️ Chú ý | **No** — Do 1 IP gửi nhiều tracking event trong cùng 1 giây |
| **Dải thời gian (Timestamp)** | 2020-06-04 16:59:46 → 17:21:32 (~22 phút) |  Đạt | **No** — Không có ngày lỗi ở tương lai |
| **Đơn giá âm (Negative Revenue)** | 0 dòng (Min: 55.00, Max: 2,766.00) |  Đạt | **No** — Doanh thu hợp lệ, không có giá trị bất thường |
| **Định dạng địa chỉ IP** | 10,000 / 10,000 (100.00% IPv4 hợp lệ) |  Đạt | **No** — Dữ liệu IP cực kỳ sạch, sẵn sàng cho Geolocation |
| **Số lượng IP duy nhất (Unique IPs)** | 2,075 / 10,000 (Trùng 79.25%) |  Tối ưu | **Yes** — Chỉ cần tra cứu Geolocation cho 2,075 IP duy nhất |
| **Đa tiền tệ (Multiple Currencies)** | 5 loại: `€`, `CHF`, `£`, `$`, `kr` | ⚠️ Cảnh báo | **YES** — Bắt buộc phải quy đổi tỷ giá (FX Conversion) về cùng 1 đơn vị tiền tệ |

---

## 2. Key Findings (Phát hiện cốt lõi)

### 2.1. Bản chất Schema-on-Read và tỷ lệ NULL cao
- Một số cột có tỷ lệ thiếu rất cao (> 90%):
  - `order_id` (99.91%), `cart_products` (98.68%), `price` (99.60%), `currency` (99.60%).
  - `user_id_db` (92.72%), `email_address` (92.72%).
- **Lý do**: Đây **KHÔNG PHẢI LỖI DỮ LIỆU**, mà là bản chất của **Schema-on-read** trong NoSQL/Countly:
  - Chỉ có sự kiện `checkout_success` (9/10,000 dòng ~ 0.09%) mới có thông tin đơn hàng và thanh toán.
  - Đa số người dùng lướt web ẩn danh (Guest), chỉ khi đăng nhập hoặc thanh toán mới có `email_address` và `user_id_db`.

  ### 2.2. Vấn đề định dạng giá tiền (Price Formatting)
- Giá sản phẩm trong `cart_products` được lưu dưới dạng chuỗi (String) và mang cả hai kiểu định dạng:
  - Chuẩn Mỹ/Quốc tế: Dấu chấm thập phân (ví dụ: `880.00`).
  - Chuẩn Châu Âu: Dấu chấm hàng nghìn, dấu phẩy thập phân (ví dụ: `1.836,00`).
- **Xử lý**: Pipeline ETL cần làm sạch dấu phẩy `,` thành dấu chấm `.` trước khi ép kiểu sang số thực (`Float/Decimal`).

  ### 2.3. Vấn đề đa tiền tệ (Currency FX)
- Doanh thu bao gồm 5 đơn vị tiền: Bảng Anh (`£`), Euro (`€`), Franc Thụy Sĩ (`CHF`), Đô la Mỹ (`$`), và Krone (`kr`).
- **Hệ quả**: Không thể tính tổng `SUM(price)` trực tiếp trong Data Warehouse nếu chưa có bảng tỷ giá quy đổi về một đồng tiền chuẩn (ví dụ: EUR hoặc USD).


## 3. Risks & Recommendations for Full Dataset (41M rows)
1. **Rủi ro tràn bộ nhớ (Out of Memory - OOM)**:
   - File full dump nặng ~19.5 GB BSON. Tuyệt đối không nạp nguyên file vào Pandas trên máy local.
   - **Khuyến nghị**: Sử dụng cơ chế nạp theo Batch/Chunk (ví dụ: 10,000 dòng/batch) khi đẩy vào MongoDB trên máy ảo Google Cloud (Phase 1).
2. **Tối ưu hóa hiệu năng IP Geolocation (Phase 2)**:
   - Tỷ lệ trùng IP lên đến ~79%. Trong 41 triệu dòng ước tính chỉ có khoảng 1–2 triệu IP duy nhất.
   - **Khuyến nghị**: Lọc lấy tập hợp **Unique IPs** (`SET`) để tra cứu IP2Location một lần duy nhất, sau đó dùng lệnh JOIN/Map ngược lại để tránh lặp lại hàng chục triệu truy vấn dư thừa.
3. **Cần lưu vết dữ liệu (Data Lineage)**:
   - Khi load 41 triệu dòng lên MongoDB, cần bổ sung thêm các trường metadata: `_loaded_at` (thời điểm load) và `_source_file` để dễ dàng kiểm toán (audit) khi có sự cố.
