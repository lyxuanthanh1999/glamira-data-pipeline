import re
import csv 
from pathlib import Path
def clean_number(num_str:str):
    """"""
    if not num_str:
        return None
    # Xóa sạch mọi loại khoảng trắng (kể cả non-breaking space \xa0, \u202f) và dấu nháy đơn
    s = re.sub(r"[\s\u00a0\u200b\u202f]+", "", num_str).replace("’", "").replace("'", "").strip()
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".","").replace(",",".")
        else:
            s = s.replace(",","")
    elif "," in s: 
        parts = s.split(",")
        if len(parts)==2 and len(parts[1])==2:
                 s = parts[0] + "." + parts[1]
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

def detect_currency(text: str) -> str:
    if "AU $" in text or "AUD" in text:
        return "AUD"
    for c in ["EUR", "CHF", "USD", "GBP", "CAD", "AED", "ZAR", "SEK", "PLN", "TRY", "DKK", "NOK"]:
        if c in text:
            return c
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"
    if "$" in text:
        return "USD"
    if "Kr" in text:
        return "SEK"
    if "zł" in text:
        return "PLN"
    return "UNKNOWN"
    
def parse_glamira_price(raw_price:str):
    
    if not raw_price or raw_price == "N/A":
        return None,None,0.0,"N/A"
    text = raw_price.replace("Why our price is better","").replace("›", "").strip()
    if "Regular Price" in text:
        disc_match = re.search(r"(\d+)%\s*OFF", text, re.IGNORECASE)
        discount_pct  = float(disc_match.group(1)) if disc_match else 0.0

        parts = text.split("Regular Price")
        sp_part = parts[0]
        reg_part = parts[1]

        reg_num = re.search(r"([\d][\d.,\s\u00a0’\']*)", reg_part)
        original_price = clean_number(reg_num.group(1)) if reg_num else None
        if "Special Price" in sp_part:
            sp_sub = sp_part.split("Special Price")[1]
            sp_num = re.search(r"([\d][\d.,\s\u00a0’\']*)", sp_sub)
            discounted_price = clean_number(sp_num.group(1)) if sp_num else original_price
        else:
            discounted_price = original_price
        currency = detect_currency(text)
        return original_price, discounted_price, discount_pct, currency

    num_match = re.search(r"([\d][\d.,\s\u00a0’\']*)", text)
    if num_match:
        val = clean_number(num_match.group(1))
        currency = detect_currency(text)
        return val, val, 0.0, currency
    return None, None, 0.0, "N/A"

    


def main():
    input_file = Path("output/products_full.csv")
    output_file = Path("output/products_cleaned.csv")
    if not input_file.exists():
        print(f"File nguồn {input_file} không tồn tại.")
        return
    print("Đang làm sạch dữ liệu sản phẩm...")
    total = 0
    cleaned_count = 0
    with open(input_file, mode="r", encoding="utf-8") as infile, \
        open(output_file, mode="w", encoding="utf-8", newline="") as outfile:

        reader = csv.DictReader(infile)
        fieldnames = [
            "product_id", "product_name", "category",
            "original_price", "discounted_price", "discount_percent", "currency",
            "url", "crawled_at", "status", "description", "sku"
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            total+=1
            raw_p = row.get("price","")
            orig_p, disc_p, disc_pct, curr = parse_glamira_price(raw_p)

            if orig_p is not None:
                cleaned_count +=1
            writer.writerow({
                "product_id": row.get("product_id"),
                "product_name": row.get("product_name"),
                "category": row.get("category"),
                "original_price": orig_p,
                "discounted_price": disc_p,
                "discount_percent": disc_pct,
                "currency": curr,
                "url": row.get("url"),
                "crawled_at": row.get("crawled_at"),
                "status": row.get("status"),
                "description": row.get("description"),
                "sku": row.get("sku")
            })
    print(f"Hoàn thành làm sạch {cleaned_count}/{total} sản phẩm.")
    print(f"File kết quả đã lưu tại: {output_file}")



if __name__ == "__main__":
    main()