import requests
from bs4 import BeautifulSoup
import sys

WORDPRESS_API_URL = "https://emdadkhodro-tak.com/wp-json/smart-ppm/v1/update-prices"

def clean_price(price_str):
    """پاکسازی متن قیمت و تبدیل آن به عدد اعشاری"""
    if not price_str:
        return None
    try:
        # حذف کاما، علامت دلار و فضاهای خالی
        clean_str = price_str.replace(',', '').replace('$', '').strip()
        return float(clean_str)
    except ValueError:
        return None

def get_prices_from_kitco():
    prices = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    # لیست فلزات و صفحات متناظر در کیتکو
    metals = {
        'platinum': 'https://www.kitco.com/charts/platinum',
        'palladium': 'https://www.kitco.com/charts/palladium',
        'rhodium': 'https://www.kitco.com/charts/rhodium'
    }

    for metal, url in metals.items():
        try:
            print(f"Fetching {metal} from {url}...")
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # روش اول: تلاش برای پیدا کردن از روی شناسه (ID) سنتی
                bid_element = soup.find(id=f"{metal}-bid") or soup.find(id=f"{metal}_bid")
                
                # روش دوم: در صورت تغییر ID، جستجو در تگ‌های جدول یا کلاس‌های قیمت لحظه‌ای (جدید)
                if not bid_element:
                    # به دنبال کلاس‌هایی که حاوی قیمت‌های Bid یا لایو هستند می‌گردد
                    bid_element = soup.find(class_=lambda x: x and all(k in x.lower() for k in ['price', 'bid']))
                
                # روش سوم: جستجو بر اساس ساختار متنی درون صفحه
                if not bid_element:
                    for td in soup.find_all(['td', 'span', 'div']):
                        if td.text and 'bid' in td.text.lower() and len(td.text) < 50:
                            # بررسی تگ بعدی که معمولاً حاوی مقدار عددی قیمت است
                            sibling = td.find_next()
                            if sibling and any(char.isdigit() for char in sibling.text):
                                bid_element = sibling
                                break

                if bid_element:
                    price_val = clean_price(bid_element.text)
                    if price_val:
                        prices[metal] = price_val
                        print(f"Successfully found {metal}: {price_val}")
                    else:
                        print(f"Could not parse price value for {metal} from text: {bid_element.text}")
                else:
                    print(f"Could not find HTML element for {metal}")
            else:
                print(f"Failed to load page for {metal}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Exception occurred while fetching {metal}: {e}")

    return prices

def send_to_wordpress(prices):
    payload = {
        "prices": prices,
        "security_key": "YOUR_SECRET_TOKEN" 
    }
    
    try:
        print(f"Sending data to WordPress: {prices}")
        response = requests.post(WORDPRESS_API_URL, json=payload, timeout=20)
        print(f"WordPress Response Code: {response.status_code}")
        print(f"WordPress Response Text: {response.text}")
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Error sending data to WordPress: {e}")
        return False

if __name__ == "__main__":
    print("Starting price extraction process...")
    extracted_prices = get_prices_from_kitco()
    
    print(f"Final extracted prices: {extracted_prices}")
    
    if extracted_prices:
        success = send_to_wordpress(extracted_prices)
        if not success:
            sys.exit(1)
    else:
        print("Error: No price data could be extracted from any source.")
        sys.exit(1)
