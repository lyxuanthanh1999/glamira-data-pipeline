import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ip2location.database import IP2Location
from config import IP2LOCATION_BIN_PATH
import csv
from pymongo import MongoClient
import os

BIN_PATH = IP2LOCATION_BIN_PATH

client = MongoClient("mongodb://127.0.0.1:27017")
db = client["countly"]
source_col = db["summary"] 
target_col = db["ip_locations"]

target_col.drop()

ip_db = IP2Location(BIN_PATH)

cursor = source_col.find(
    {"ip": {"$gt": ""}},   
    {"_id":0,"ip":1}
).hint("ip_1").batch_size(50000)

last_ip = None
total_unique = 0        
valid_count = 0         
batch_records = []      
BATCH_SIZE = 20000      

output_csv = "output/ip_location_full.csv"
os.makedirs("output", exist_ok=True)

with open(output_csv,mode="w",newline="",encoding="utf-8") as f_csv:
    fields = ['ip', 'country_code', 'country_name', 'region_name', 'city_name']
    writer = csv.DictWriter(f_csv,fieldnames=fields)
    writer.writeheader()
    for doc in cursor:
        ip = doc.get("ip")
        if ip and ip != last_ip:
            total_unique +=1
            last_ip = ip
            rec = ip_db.get_all(ip)
            c_code = rec.country_short if rec.country_short else '-'
            c_name = rec.country_long if rec.country_long else '-'
            r_name = rec.region if rec.region else '-'
            city = rec.city if rec.city else '-'

            if c_code != '-':
                valid_count += 1
            record = {
                'ip': ip,
                'country_code': c_code,
                'country_name': c_name,
                'region_name': r_name,
                'city_name': city
            }

            batch_records.append(record)
            writer.writerow(record)
            
            if len(batch_records) >= BATCH_SIZE:
                target_col.insert_many(batch_records,ordered=False)
                batch_records = []
                print(f" Đã xử lý {total_unique:,} IP duy nhất...")
    if batch_records:
        target_col.insert_many(batch_records, ordered=False)    

print("Đang tạo index trên 'ip' cho collection ip_locations...")
target_col.create_index("ip")

coverage = (valid_count / total_unique * 100) if total_unique > 0 else 0
print("\n" + "=" * 60)
print(" BÁO CÁO KẾT QUẢ IP GEOLOCATION (CHECKPOINT #8)")
print("=" * 60)
print(f"  Tổng số IP duy nhất       : {total_unique:,}")
print(f"  Số IP tra cứu thành công  : {valid_count:,}")
print(f"  Tỷ lệ phủ sóng (Coverage) : {coverage:.2f}% (Yêu cầu >= 80%)")
print(f"  Đã lưu vào MongoDB        : countly.ip_locations")
print(f"  Đã xuất file CSV          : {output_csv}")
print("=" * 60)