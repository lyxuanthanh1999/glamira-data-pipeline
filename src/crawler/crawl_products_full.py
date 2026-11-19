import os
import sys
from pathlib import Path
import time
import random
import datetime

import pandas as pd

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from curl_cffi import requests

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import parse_glamira_html

ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
MAX_WORKERS = 5

write_lock = threading.Lock()

def get_delay():
    return random.uniform(1.0,3.0)

def get_headers()->dict:
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
    }

# def parse_product_html(html_content:bytes, product_id:str,url:str):
#             soup = BeautifulSoup(html_content,'html.parser')

#             h1 = soup.find('h1')
#            # 1. Bóc tách Tên sản phẩm (thẻ h1)
#             h1 = soup.find('h1')
#             product_name = h1.text.strip() if h1 else 'N/A'
            
#             # 2. Bóc tách Danh mục (Category từ Breadcrumb)
#             crumbs = [b.text.strip() for b in soup.select('.breadcrumbs li, .breadcrumb li') if b.text.strip()]
#             category = crumbs[-2] if len(crumbs) >= 2 else (crumbs[-1] if crumbs else 'N/A')
            
#             # 3. Bóc tách Giá niêm yết
#             price_el = soup.select_one('.price-box, .price, [data-price-type="finalPrice"]')
#             price = price_el.text.strip().replace('\n', ' ') if price_el else 'N/A'
            
#             return {
#                 'product_id': product_id,
#                 'product_name': product_name,
#                 'category': category,
#                 'price': price,
#                 'url': url,
#                 'crawled_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 'status': 'SUCCESS'
#             }

def crawl_product(product_id:str,url:str):
    session = requests.Session(impersonate="chrome120")

    time.sleep(get_delay())
    
    headers = get_headers()

    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return parse_glamira_html(response.content,product_id,url)
        else:
            return {
                'product_id': product_id,
                'url': url,
                'status': f'HTTP_{response.status_code}',
                'error': f'Server trả về mã {response.status_code}'
            }
    except requests.exceptions.Timeout:
        return {'product_id': product_id, 'url': url, 'status': 'TIMEOUT', 'error': 'Timeout (>10s)'}
    except requests.exceptions.RequestException as e:
        return {'product_id': product_id, 'url': url, 'status': 'ERROR', 'error': str(e)}

def load_checkpoint(file_path:str)->set:
    if os.path.exists(file_path) and os.path.getsize(file_path)>0:
        df_done = pd.read_csv(file_path)
        if 'product_id' in df_done.columns:
            done_ids = set(df_done['product_id'].astype(str))
            print(f"Checkpoint: Đã có {len(done_ids):,} sản phẩm cào trước đó. Sẽ bỏ qua.")
            return done_ids
    return set()

def filter_todo_products(input_csv: str, already_crawled_ids: set, limit: int = None) -> dict:
    if not os.path.exists(input_csv):
        print(f"Không tìm thấy file đầu vào: {input_csv}")
        return {}
    df = pd.read_csv(input_csv)
    if limit:
        df = df.head(limit)
    todo = {}
    for idx, row in df.iterrows():
        pid = str(row['product_id'])
        url = row['product_url']
        if pid not in already_crawled_ids:
            todo[pid] = url
        else:
            pass
    print(f"Tổng số sản phẩm cần cào đợt này: {len(todo):,} sản phẩm")
    return todo

def save_results(result:dict,success_csv: str, error_csv: str):
    with write_lock:
        if result['status'] == 'SUCCESS':
            is_new = not os.path.exists(success_csv) or os.path.getsize(success_csv) == 0
            pd.DataFrame([result]).to_csv(success_csv, mode='a', header=is_new, index=False)
        else:
            is_err_new = not os.path.exists(error_csv) or os.path.getsize(error_csv) == 0
            pd.DataFrame([result]).to_csv(error_csv, mode='a', header=is_err_new, index=False)


def main(input_csv="output/products_to_crawl_full.csv",limit=50):
    if not os.path.exists(input_csv):
        print(f"Không tìm thấy file đầu vào: {input_csv}")
        return 

    df_products = pd.read_csv(input_csv)
    test_batch = df_products.head(limit)

    output_success_csv = "output/crawled_products_sample.csv"
    output_error_csv = "output/crawl_errors.log"
    os.makedirs("output", exist_ok=True)
    

    already_crawled_ids = load_checkpoint(output_success_csv)

    todo = filter_todo_products(input_csv, already_crawled_ids, limit=limit)

    

    print(f"\nBắt đầu cào {len(todo)} sản phẩm bằng {MAX_WORKERS} luồng song song...\n")

    success_products = []
    error_logs = [] 
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        futures = {executor.submit(crawl_product, pid, url): pid for pid, url in todo.items()}
        
        for idx, future in enumerate(as_completed(futures), 1):
            result = future.result()
            pid = result['product_id']
            
            save_results(result,output_success_csv,output_error_csv)
            if result['status'] == 'SUCCESS':
                success_products.append(result)
                print(f"[{idx:>5}/{len(todo)}]  ID {pid}: {result['product_name'][:30]} | Cat: {result['category']}")
            else:
                error_logs.append(result)
                print(f"[{idx:>5}/{len(todo)}]  ID {pid}: {result['status']} ({result.get('error', '')})")
if __name__ == "__main__":
    main(limit=20000)