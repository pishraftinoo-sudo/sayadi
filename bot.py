import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

KITCO_URLS = {
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
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

OUTPUT_FILE = os.getenv("OUTPUT_FILE", "prices.json").strip()


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


def find_price_node(soup, metal):
    candidate_ids = [
        f"{metal}-bid",
        f"{metal}_bid",
        f"{metal}-price",
        f"{metal}_price",
        f"{metal}Bid",
        f"{metal}Price",
    ]

    for element_id in candidate_ids:
        node = soup.find(id=element_id)
        if node and node.get_text(" ", strip=True):
            return node

    candidate_selectors = [
        f".{metal}-bid",
        f".{metal}_bid",
        f".{metal}-price",
        f".{metal}_price",
        f"[data-metal='{metal}']",
        f"[data-symbol='{metal}']",
    ]

    for selector in candidate_selectors:
        try:
            node = soup.select_one(selector)
            if node and node.get_text(" ", strip=True):
                return node
        except Exception:
            pass

    for node in soup.find_all(["span", "div", "td", "li"]):
        classes = " ".join(node.get("class", [])) if node.get("class") else ""
        text = node.get_text(" ", strip=True)

        if not text:
            continue

        if classes and any(k in classes.lower() for k in ["price", "bid", "quote"]):
            if extract_first_price(text) is not None:
                return node

    for node in soup.find_all(["span", "div", "td", "li"]):
        text = node.get_text(" ", strip=True)
        if extract_first_price(text) is not None:
            return node

    return None


def fetch_metal_price(metal, url):
    print(f"Fetching {metal} from {url}...")
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    node = find_price_node(soup, metal)

    if node is None:
        raise RuntimeError(f"Could not locate price node for {metal}")

    raw_text = node.get_text(" ", strip=True)
    price = extract_first_price(raw_text)

    if price is None:
        fallback_text = soup.get_text(" ", strip=True)
        price = extract_first_price(fallback_text)

    if price is None:
        raise RuntimeError(f"Could not parse price for {metal}")

    print(f"Found {metal}: {price}")
    return price


def get_prices_from_kitco():
    prices = {}

    for metal, url in KITCO_URLS.items():
        try:
            prices[metal] = fetch_metal_price(metal, url)
        except Exception as exc:
            print(f"Failed to fetch {metal}: {exc}")

    return prices


def write_json_file(prices):
    payload = {
        "source": "kitco",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "prices": prices,
    }

    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved JSON to {OUTPUT_FILE}")


def main():
    print("Starting price extraction process...")

    prices = get_prices_from_kitco()
    print(f"Final extracted prices: {prices}")

    if not prices:
        print("Error: No price data could be extracted.")
        sys.exit(1)

    write_json_file(prices)
    print("Done.")


if __name__ == "__main__":
    main()
