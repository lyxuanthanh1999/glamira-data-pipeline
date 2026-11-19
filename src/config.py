from pathlib import Path
from fake_useragent import UserAgent
import datetime
from bs4 import BeautifulSoup

# Thư mục gốc dự án (Project5)
BASE_DIR = Path(__file__).resolve().parent.parent

# Các thư mục con chính
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
DUMP_DIR = BASE_DIR / "dump"
DOCS_DIR = BASE_DIR / "docs"

# Dữ liệu mẫu & kết quả xử lý
SAMPLE_JSON_PATH = DATA_DIR / "sample.json"
SUMMARY_JSON_PATH = DATA_DIR / "summary.json"
IP_LOCATION_CSV_PATH = DATA_DIR / "ip_location.csv"
PRODUCTS_CSV_PATH = DATA_DIR / "products_to_crawl.csv"

# Dữ liệu gốc trong dump
BSON_PATH = DUMP_DIR / "countly" / "summary.bson"
IP2LOCATION_BIN_PATH = DUMP_DIR / "IP-COUNTRY-REGION-CITY.BIN"


ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
HEADERS = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,de;q=0.7',
        'Referer': 'https://www.google.com/'
    }

def parse_glamira_html(html_content: bytes, product_id: str, url: str) -> dict:
    """
        Hàm parse CHUẨN DÙNG CHUNG cho cả crawl và retry.
        Trả về dict với ĐẦY ĐỦ 9 trường nhất quán.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    # 1. Tên sản phẩm
    h1 = soup.find('h1')
    product_name = h1.text.strip() if h1 else 'N/A'

    # 2. Danh mục (Breadcrumb)
    crumbs = [b.text.strip() for b in soup.select('.breadcrumbs li, .breadcrumb li') if b.text.strip()]
    category = crumbs[-2] if len(crumbs) >= 2 else (crumbs[-1] if crumbs else 'N/A')
    
    # 3. Giá niêm yết (chuẩn hóa khoảng trắng)
    price_el = soup.select_one('.price-box, .price, [data-price-type="finalPrice"]')
    price = " ".join(price_el.text.split()) if price_el else 'N/A'

    # 4. Mô tả (Meta description)
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    description = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else 'N/A'
    
    # 5. SKU (Thử nhiều selector vì Glamira có thể thay đổi HTML)
    for sku_sel in ['.product.attribute.sku .value', '[itemprop="sku"]', '.sku .value']:
        sku_tag = soup.select_one(sku_sel)
        if sku_tag and sku_tag.text.strip():
            sku = sku_tag.text.strip()
            break
    else:
        sku = 'N/A'
    return {
        'product_id': str(product_id),
        'product_name': product_name,
        'category': category,
        'price': price,
        'description': description[:300],
        'sku': sku,
        'url': url,
        'crawled_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'SUCCESS'
    }