import os
import re
import sys
import requests
from bs4 import BeautifulSoup

# تنظیمات وردپرس (از طریق Environment Variables در گیت‌هاب تنظیم شود)
WORDPRESS_API_URL = os.getenv(
    "WORDPRESS_API_URL",
    "https://www.sayadicatalyst.com/wp-json/smart-ppm/v1/update-prices"
)
WORDPRESS_SECURITY_KEY = os.getenv(
    "WORDPRESS_SECURITY_KEY",
    "sayadi-smart-ppm-2026"
)

# منابع استخراج قیمت
METALS = {
    "platinum": "https://www.kitco.com/charts/platinum",
    "palladium": "https://www.kitco.com/charts/palladium",
    "rhodium": "https://www.kitco.com/charts/rhodium",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def clean_price(text):
    """استخراج اولین عدد معتبر از متن (حذف ویرگول و کاراکترهای اضافه)"""
    if not text: return None
    match = re.search(r"(\d[\d,]*\.?\d*)", text)
    if not match: return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None

def fetch_kitco_price(metal, url):
    """تلاش برای یافتن قیمت در ساختار متغیر کیتکو"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # استراتژی ۱: استفاده از ID های استاندارد کیتکو
        for suffix in ["-bid", "_bid", "-price", "_price"]:
            element = soup.find(id=f"{metal}{suffix}")
            if element:
                price = clean_price(element.get_text())
                if price: return price
        
        # استراتژی ۲: جستجو در کلاس‌هایی که کلمه Bid یا Price دارند
        for node in soup.find_all(["span", "div"], class_=re.compile(r"price|bid", re.I)):
            price = clean_price(node.get_text())
            if price: return price

        return None
    except Exception as e:
        print(f"Error fetching {metal}: {e}")
        return None

def main():
    print("🚀 Starting Smart PPM Price Update...")
    
    extracted_data = {}
    for metal, url in METALS.items():
        print(f"🔍 Fetching {metal}...")
        price = fetch_kitco_price(metal, url)
        if price:
            extracted_data[metal] = price
            print(f"✅ Found {metal}: {price}")
        else:
            print(f"❌ Failed to find price for {metal}")

    if not extracted_data:
        print("⛔ No data extracted. Exiting.")
        sys.exit(1)

    # آماده‌سازی پکیج برای ارسال به وردپرس
    payload = {
        "security_key": WORDPRESS_SECURITY_KEY,
        "source": "kitco_bot",
        "prices": extracted_data
    }

    print(f"📤 Sending data to WordPress...")
    try:
        response = requests.post(
            WORDPRESS_API_URL, 
            json=payload, 
            timeout=20,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Server Status: {response.status_code}")
        print(f"📩 Server Response: {response.text}")

        if response.status_code == 200:
            print("🎉 Success! Prices updated in WordPress database.")
        else:
            print(f"⚠️ Failed to update. Check API logs.")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Connection Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
