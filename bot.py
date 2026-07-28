import os
import re
import sys
import requests
from bs4 import BeautifulSoup

WORDPRESS_API_URL = os.getenv(
    "WORDPRESS_API_URL",
    "https://www.sayadicatalyst.com/wp-admin/admin-ajax.php"
)
WORDPRESS_SECURITY_KEY = os.getenv(
    "WORDPRESS_SECURITY_KEY",
    "sayadi-smart-ppm-2026"
)

METALS = {
    "platinum": "https://www.kitco.com/charts/platinum",
    "palladium": "https://www.kitco.com/charts/palladium",
    "rhodium": "https://www.kitco.com/charts/rhodium",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def extract_first_price(text):
    if not text:
        return None
    match = re.search(r"(\d[\d,]*\.?\d*)", text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None

def find_price_element(soup, metal):
    candidates = [
        f"{metal}-bid",
        f"{metal}_bid",
        f"{metal}-price",
        f"{metal}_price",
    ]

    for element_id in candidates:
        node = soup.find(id=element_id)
        if node and node.get_text(strip=True):
            return node

    for node in soup.find_all(["span", "div", "td"]):
        classes = " ".join(node.get("class", [])) if node.get("class") else ""
        if classes and ("price" in classes.lower() or "bid" in classes.lower()):
            if any(ch.isdigit() for ch in node.get_text(" ", strip=True)):
                return node

    for node in soup.find_all(["span", "div", "td", "li"]):
        text = node.get_text(" ", strip=True)
        if extract_first_price(text) is not None:
            return node

    return None

def get_prices_from_kitco():
    prices = {}

    for metal, url in METALS.items():
        try:
            print(f"Fetching {metal} from {url}...")
            response = requests.get(url, headers=HEADERS, timeout=20)

            if response.status_code != 200:
                print(f"Failed to load {metal}. Status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            price_node = find_price_element(soup, metal)

            if not price_node:
                print(f"Could not find HTML element for {metal}")
                continue

            raw_text = price_node.get_text(" ", strip=True)
            price_val = extract_first_price(raw_text)

            if price_val is None:
                print(f"Could not parse price for {metal} from text: {raw_text}")
                continue

            prices[metal] = price_val
            print(f"Successfully found {metal}: {price_val}")

        except Exception as e:
            print(f"Exception occurred while fetching {metal}: {e}")

    return prices

def send_to_wordpress(prices):
    payload = {
        "action": "smart_ppm_update_prices",
        "security_key": WORDPRESS_SECURITY_KEY,
        "source": "kitco",
        "platinum": prices.get("platinum", 0),
        "palladium": prices.get("palladium", 0),
        "rhodium": prices.get("rhodium", 0),
    }

    try:
        print("Sending data to WordPress...")
        response = requests.post(WORDPRESS_API_URL, data=payload, timeout=20)

        print(f"WordPress Response Code: {response.status_code}")
        print(f"WordPress Response Text: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"Error sending data to WordPress: {e}")
        return False

def main():
    print("Starting price extraction process...")

    extracted_prices = get_prices_from_kitco()
    print(f"Final extracted prices: {extracted_prices}")

    if not extracted_prices:
        print("Error: No price data could be extracted from any source.")
        sys.exit(1)

    success = send_to_wordpress(extracted_prices)
    if not success:
        sys.exit(1)

    print("Done.")

if __name__ == "__main__":
    main()
