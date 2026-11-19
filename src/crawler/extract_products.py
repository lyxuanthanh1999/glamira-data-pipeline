import time
import pandas as pd
from pymongo import MongoClient
import os

client = MongoClient("mongodb://127.0.0.1:27017")
db = client["countly"]
col = db["summary"]

target_collections = [
    'view_product_detail',
    'select_product_option',
    'select_product_option_quality',
    'add_to_cart_action',
    'product_detail_recommendation_visible',
    'product_detail_recommendation_noticed',
    'back_to_product_action',
    'view_all_recommend',
    'product_view_all_recommend_clicked'
]

projection = {
    "_id":0,
    "product_id":1,
    "viewing_product_id":1,
    "current_url":1,
    "referrer_url":1
}

cursor = col.find(
    {"collection":{"$in":target_collections}},
    projection
).hint("collection_1").batch_size(20000)

distinct_products = {}

for doc in cursor:
    pid = doc.get('product_id')
    if not pid or pid == "":
        pid = doc.get("viewing_product_id")
    url = doc.get("current_url")
    if not url or url =="":
        url = doc.get('referrer_url')

    if pid and url:
        pid_str = str(int(pid) if isinstance(pid,(int,float) )else str(pid).strip()) 
        raw_url = str(url).strip()
        clean_url = raw_url.split("?")[0]
        if pid_str != "" and pid_str != "None" and clean_url.endswith(".html"):
            if pid_str not in distinct_products:
                distinct_products[pid_str] = clean_url
        
    

products_df = pd.DataFrame(
    list(distinct_products.items()),
    columns=['product_id','product_url']
)
os.makedirs("output",exist_ok=True)
output_file = "output/products_to_crawl_full.csv"
products_df.to_csv(output_file,index=False)
print(f" Đã lưu {len(distinct_products)} sản phẩm độc nhất vào {output_file}")
