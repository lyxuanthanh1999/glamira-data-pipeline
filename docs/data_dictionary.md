# 📖 TỪ ĐIỂN DỮ LIỆU DỰ ÁN GLAMIRA (DATA DICTIONARY)
> **Dự án**: Glamira Clickstream Analytics Pipeline (Project 05)  
> **Nguồn gốc**: 41,432,473 sự kiện hành vi người dùng (Clickstream logs) từ nền tảng thương mại điện tử trang sức Glamira (Tháng 10 - Tháng 11/2019).  
> **Cơ sở dữ liệu Staging**: MongoDB 6.0 trên Google Compute Engine (`glamira-project-05`).

---

## 📑 MỤC LỤC
1. [Kiến trúc Schema-on-Read & Tổng quan Collections](#1-kiến-trúc-schema-on-read--tổng-quan-collections)
2. [Chi tiết Collection: `summary` (Raw Clickstream Events)](#2-chi-tiết-collection-summary)
3. [Chi tiết Collection: `ip_locations` (Enriched Geolocation)](#3-chi-tiết-collection-ip_locations)
4. [Chi tiết Collection: `products` (Enriched Product Catalog)](#4-chi-tiết-collection-products)
5. [Quy tắc nghiệp vụ cốt lõi (Business Rules & Caveats)](#5-quy-tắc-nghiệp-vụ-cốt-lõi)

---

## 1. Kiến trúc Schema-on-Read & Tổng quan Collections

Dữ liệu thô ban đầu được thu thập bởi SDK Countly dưới dạng NoSQL Document. Do đặc thù **Schema-on-Read**, mỗi loại sự kiện (`collection`) chỉ mang theo các trường thông tin phù hợp với ngữ cảnh của nó:
- Các trường định danh phiên (`device_id`, `ip`, `time_stamp`) luôn xuất hiện ở mọi sự kiện (0% NULL).
- Các trường định danh giao dịch (`order_id`, `price`, `currency`) chỉ xuất hiện khi khách hàng hoàn tất mua hàng (`checkout_success`). Các sự kiện khác (`view`, `click_buy`, `add_to_cart`) trường này sẽ là **NULL**.

### Bảng tóm tắt các Collections trong MongoDB:

| Collection Name | Số lượng bản ghi | Nguồn dữ liệu | Mục đích |
|---|---:|---|---|
| `countly.summary` | **41,432,473** | File BSON gốc (`summary.bson`) | Lưu trữ toàn bộ sự kiện clickstream thô |
| `countly.ip_locations` | **2,035,839** | Làm giàu qua IP2Location DB | Ánh xạ địa chỉ IP sang Quốc gia, Thành phố, Tọa độ |
| `countly.products` | **18,868** | Crawl trực tiếp từ website Glamira | Lưu thông tin chi tiết: Tên, Giá niêm yết, Danh mục sản phẩm |

---

## 2. Chi tiết Collection: `summary`

- **Tên Database**: `countly`
- **Tên Collection**: `summary`
- **Mô tả**: Ghi nhận toàn bộ tương tác của người dùng trên website (xem trang, thêm vào giỏ, tìm kiếm, đặt hàng thành công).

### Danh mục các trường (Field Specifications):

| Tên trường | Kiểu dữ liệu | Tỷ lệ NULL | Mô tả chi tiết & Ví dụ |
|---|---|:---:|---|
| `_id` | ObjectId | 0% | Khóa chính tự sinh của MongoDB (BSON ObjectId). |
| `collection` | String | 0% | **Loại sự kiện hành vi**: `view`, `click_buy`, `add_to_cart`, `checkout_success`, `search`, `basket_item_delete`, `order_status`, `detail_page_view`. |
| `device_id` | String | 0% | Mã định danh thiết bị/trình duyệt của người dùng (Cookie/Fingerprint). |
| `ip` | String | 0% | Địa chỉ IPv4 của người dùng tại thời điểm phát sinh sự kiện. Dùng để join với `ip_locations`. |
| `time_stamp` | Int64 | 0% | Unix Timestamp tính bằng giây (Epoch time) khi sự kiện xảy ra trên thiết bị client. |
| `server_time` | Int64 | 0% | Unix Timestamp tính bằng giây khi server Countly tiếp nhận bản ghi. |
| `product_id` | Int64 / String | ~48.2% | Mã định danh sản phẩm. Xuất hiện trong các event liên quan đến sản phẩm (`view`, `click_buy`, `add_to_cart`, `checkout_success`). Dùng để join với `products`. |
| `url` | String | ~2.1% | Đường dẫn URL đầy đủ người dùng truy cập tại thời điểm diễn ra sự kiện. |
| `view` | Double / Int | ~15.0% | Số lượt xem trang hoặc chỉ số view đếm bởi client. |
| `order_id` | String / Int | ~98.9% | **Mã đơn hàng**: Chỉ xuất hiện và có giá trị khi `collection = 'checkout_success'`. Các event khác là NULL (đây là thiết kế chuẩn Schema-on-Read). |
| `price` | String / Double | ~98.9% | **Giá trị đơn hàng thực tế (Actual Checkout Price)**: Chỉ có trong `checkout_success`. Là tổng số tiền khách thanh toán cho đơn hàng đó (bao gồm giảm giá, tùy chọn vàng/bạc/kim cương, phí vận chuyển). |
| `currency` | String | ~98.9% | Đơn vị tiền tệ thanh toán (`EUR`, `CHF`, `GBP`, `USD`, `TRY`, `DKK`,...). Chỉ có trong `checkout_success`. |
| `cart_products` | String / Array | ~98.9% | Chi tiết danh sách sản phẩm trong giỏ hàng tại thời điểm checkout. |
| `current_key` | String | ~70.0% | Từ khóa tìm kiếm nếu người dùng sử dụng tính năng Search trên website. |
| `utm_source` | String | ~85.0% | Kênh tiếp thị chuyển đổi (Google, Facebook, Direct, Newsletter,...). |
| `utm_medium` | String | ~85.0% | Phương thức tiếp thị (cpc, organic, email, referral,...). |
| `utm_campaign`| String | ~88.0% | Tên chiến dịch tiếp thị cụ thể. |

---

## 3. Chi tiết Collection: `ip_locations`

- **Tên Database**: `countly`
- **Tên Collection**: `ip_locations`
- **Độ bao phủ (Coverage)**: **98.99%** (Tìm thấy vị trí cho 2,015,274 / 2,035,839 IP unique).
- **Mô tả**: Bảng danh mục chiều địa lý (Geographic Dimension) được làm giàu từ cơ sở dữ liệu nhị phân `IP-COUNTRY-REGION-CITY.BIN`.

### Danh mục các trường:

| Tên trường | Kiểu dữ liệu | Ví dụ | Mô tả chi tiết |
|---|---|---|---|
| `ip` | String (**PK**) | `185.108.106.12` | Địa chỉ IP độc nhất (Primary Key). Đã đánh Unique Index. |
| `country_code` | String | `DE` | Mã quốc gia theo chuẩn ISO-3166 2 ký tự. |
| `country_name` | String | `Germany` | Tên quốc gia đầy đủ bằng tiếng Anh. |
| `region_name` | String | `Bavaria` | Tên tỉnh / bang / vùng lãnh thổ. |
| `city_name` | String | `Munich` | Tên thành phố / thị xã. |
| `latitude` | Float | `48.1351` | Vĩ độ địa lý (hỗ trợ vẽ bản đồ nhiệt GIS trên Dashboard). |
| `longitude` | Float | `11.5820` | Kinh độ địa lý. |
| `zip_code` | String | `80331` | Mã bưu chính (Postal code) nếu có. |
| `time_zone` | String | `+01:00` | Múi giờ địa phương của người dùng. |

---

## 4. Chi tiết Collection: `products`

- **Tên Database**: `countly`
- **Tên Collection**: `products`
- **Độ bao phủ (Coverage)**: **98.11%** (Cào thành công 18,868 / 19,232 sản phẩm unique).
- **Mô tả**: Bảng danh mục sản phẩm (Product Dimension) được thu thập tự động từ hệ thống website Glamira bằng cơ chế xoay vòng domain quốc tế (`.com`, `.de`, `.co.uk`, `.fr`, `.es`, `.ca`) và Magento Fallback Routing.

### Danh mục các trường:

| Tên trường | Kiểu dữ liệu | Ví dụ | Mô tả chi tiết |
|---|---|---|---|
| `product_id` | Int64 (**PK**) | `86381` | Mã sản phẩm duy nhất (Primary Key). Đã đánh Unique Index. |
| `name` | String | `Aurelia Diamond Ring` | Tên thương mại của sản phẩm. |
| `price` | Float | `1250.00` | **Giá niêm yết (Catalogue/Listed Price)**: Giá cơ sở hiển thị trên trang chi tiết sản phẩm. |
| `currency` | String | `EUR` | Đơn vị tiền tệ niêm yết trên trang cào. |
| `category` | String | `Rings > Diamond Rings` | Cây phân cấp ngành hàng (Breadcrumb category). Dùng để phân tích nhóm sản phẩm bán chạy. |
| `url` | String | `https://www.glamira.com/...` | Đường dẫn gốc của sản phẩm trên website. |
| `crawled_at` | Timestamp | `2026-11-16 15:30:00` | Thời điểm bot thu thập dữ liệu thành công. |

---

## 5. Quy tắc nghiệp vụ cốt lõi (Business Rules & Caveats)

### ⚠️ Quy tắc 1: Phân biệt "Giá niêm yết" và "Giá thanh toán thực tế" (RẤT QUAN TRỌNG)
- **`products.price` (Listed Price)**: Là giá hiển thị trên website khi chưa tùy biến chất liệu và chưa áp dụng mã giảm giá.
- **`summary.price` (Actual Checkout Price)**: Là số tiền thực tế khách hàng thanh toán tại thời điểm đặt hàng thành công (`checkout_success`), đã bao gồm các tùy chọn nâng cấp (kim cương, vàng trắng, khắc tên) và chiết khấu.
- **Quy tắc tính doanh thu**: **TUYỆT ĐỐI KHÔNG** dùng `products.price` để tính doanh thu tổng của công ty. Doanh thu tài chính bắt buộc phải lấy từ trường `summary.price` trong sự kiện `checkout_success`.

### ⚠️ Quy tắc 2: Xử lý đa tiền tệ (Multi-currency Conversion)
- Dữ liệu chứa 5+ loại tiền tệ khác nhau (`EUR`, `CHF`, `GBP`, `USD`, `TRY`,...).
- Khi nạp vào Data Warehouse (Phase 3), cần áp dụng tỷ giá chuẩn hóa (FX Rate) để quy đổi tất cả doanh thu về một loại tiền tệ thống nhất (thường là **USD** hoặc **EUR**) trước khi tính KPI tổng.

### ⚠️ Quy tắc 3: Schema-on-Read và Tỷ lệ NULL
- Tỷ lệ NULL cao ở các trường `order_id`, `price`, `currency` không phải là lỗi dữ liệu hay mất mát dữ liệu, mà là do bản chất hành vi: Trong thương mại điện tử, 1,000 lượt xem (`view`) mới tạo ra 1 đơn hàng thành công (`checkout_success`).
- Khi thiết kế Data Warehouse Star Schema ở Phase 3:
  - Bảng Fact giao dịch (`fact_orders`) sẽ chỉ lọc các bản ghi `collection = 'checkout_success'`.
  - Bảng Fact hành vi (`fact_events`) sẽ chứa tất cả các lượt tương tác với kích thước tinh gọn.

