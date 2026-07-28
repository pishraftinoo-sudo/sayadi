import requests
from bs4 import BeautifulSoup
import json
import sys

# آدرس وب‌سایت وردپرسی شما برای ارسال قیمت‌ها
WORDPRESS_API_URL = "https://emdadkhodro-tak.com/wp-json/smart-ppm/v1/update-prices"

def get_prices_from_kitco():
    """
    استخراج قیمت‌ها از صفحات رسمی کیتکو
    """
    prices = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    # ۱. استخراج قیمت پلاتین و پالادیوم
    try:
        url_pt_pd = "https://www.kitco.com/charts/platinum"
        response = requests.get(url_pt_pd, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # پیدا کردن قیمت‌ها بر اساس ساختار تگ‌های کیتکو
            # (در صورت تغییر ساختار سایت، این بخش‌ها نیاز به آپدیت دارند)
            # به عنوان نمونه تگ‌های قیمت لحظه‌ای:
            platinum_bid = soup.find(id="platinum-bid")
            palladium_bid = soup.find(id="palladium-bid")
            
            if platinum_bid:
                prices['platinum'] = float(platinum_bid.text.replace(',', '').strip())
            if palladium_bid:
                prices['palladium'] = float(palladium_bid.text.replace(',', '').strip())
    except Exception as e:
        print(f"Error fetching Platinum/Palladium: {e}")

    # ۲. استخراج قیمت رودیوم (از صفحه مرجع رودیوم کیتکو)
    try:
        url_rh = "https://www.kitco.com/charts/rhodium"
        response = requests.get(url_rh, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rhodium_bid = soup.find(id="rhodium-bid")
            if rhodium_bid:
                prices['rhodium'] = float(rhodium_bid.text.replace(',', '').strip())
    except Exception as e:
        print(f"Error fetching Rhodium: {e}")

    return prices

def get_prices_backup():
    """
    منبع پشتیبان (مثلاً استفاده از یک API رایگان یا منبع جایگزین در صورت بروز خطا در کیتکو)
    """
    # در صورتی که کیتکو تغییر ساختار داد، این بخش به عنوان پشتیبان عمل می‌کند
    try:
        # برای مثال استفاده از یک API عمومی جایگزین برای پلاتین و پالادیوم
        response = requests.get("https://api.metals.dev/v1/latest?api_key=FREE_KEY", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "platinum": data['rates'].get('platinum'),
                "palladium": data['rates'].get('palladium'),
                # رودیوم معمولاً در APIهای رایگان نیست و باید از کیتکو اسکرپ شود
            }
    except:
        pass
    return {}

def send_to_wordpress(prices):
    """
    ارسال داده‌های نهایی به Endpoint سایت وردپرسی شما
    """
    payload = {
        "prices": prices,
        "security_key": "YOUR_SECRET_TOKEN" # برای امنیت بیشتر و جلوگیری از درخواست‌های فیک
    }
    
    try:
        response = requests.post(WORDPRESS_API_URL, json=payload, timeout=20)
        print(f"WordPress Response Code: {response.status_code}")
        print(f"WordPress Response Text: {response.text}")
        if response.status_code == 200:
            print("Prices successfully synced to WordPress database!")
            return True
        else:
            print("Failed to sync with WordPress.")
            return False
    except Exception as e:
        print(f"Error sending data to WordPress: {e}")
        return False

if __name__ == "__main__":
    print("Starting price extraction...")
    extracted_prices = get_prices_from_kitco()
    
    # اگر برخی قیمت‌ها خالی بودند، از متد پشتیبان استفاده کن
    if not extracted_prices.get('platinum') or not extracted_prices.get('rhodium'):
        print("Using backup source for missing values...")
        backup = get_prices_backup()
        for metal, val in backup.items():
            if val and not extracted_prices.get(metal):
                extracted_prices[metal] = val

    print(f"Final extracted prices: {extracted_prices}")
    
    # ارسال به سایت اگر حداقل یکی از قیمت‌ها موجود بود
    if extracted_prices:
        success = send_to_wordpress(extracted_prices)
        if not success:
            sys.exit(1)
    else:
        print("No price data extracted. Exiting.")
        sys.exit(1)
