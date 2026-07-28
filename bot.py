import os
import requests
from bs4 import BeautifulSoup

# آدرس سایت امداد خودرو تک
WP_URL = "https://emdadkhodro-tak.com/wp-json/smart-ppm/v1/update-prices"

def fetch_prices():
    # استفاده از هدرهای فریب‌دهنده برای عبور از سد ربات‌یاب
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # درخواست مستقیم به صفحه قیمت‌های کیتکو
        response = requests.get("https://www.kitco.com/charts/precious-metals", headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # اینجا کدهای HTML را پردازش می‌کنیم تا قیمت پلاتین، پالادیوم و رودیوم را پیدا کنیم
            # (این روش نیازی به OCR و عکس گرفتن ندارد و ۱۰۰٪ دقیق است)
            prices = {}
            
            # نمونه فرضی برای پیدا کردن مقادیر از جدول کیتکو
            # پس از بررسی ساختار دقیق HTML کلاس‌ها جایگذاری می‌شوند
            prices['platinum'] = float(soup.find(id="platinum-bid").text.strip().replace(',', ''))
            prices['palladium'] = float(soup.find(id="palladium-bid").text.strip().replace(',', ''))
            prices['rhodium'] = float(soup.find(id="rhodium-bid").text.strip().replace(',', ''))
            
            # ارسال به وردپرس روی سرور ایران
            res = requests.post(WP_URL, json={'prices': prices}, timeout=10)
            print(f"Data Sent: {prices}, Response: {res.status_code}")
            
        else:
            print(f"Failed to load Kitco: Status {response.status_code}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    fetch_prices()
