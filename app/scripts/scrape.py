from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re
import requests
import db
import sys
import argparse
import logging
import os

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def send_discord_alert(message, webhook_url):
    data = {"content": message}
    requests.post(webhook_url, json=data)

# Logging and startup message
start = datetime.now()
msg = f"Started Scraping {start.strftime('%Y-%m-%d %I:%M:%S %p')}"
send_discord_alert(msg, DISCORD_WEBHOOK)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

class Data:
    def __init__(self, card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link):
        self.card = card
        self.listing_quantity = listing_quantity
        self.lowest_price = lowest_price
        self.market_price = market_price
        self.rarity = rarity
        self.card_number = card_number
        self.set_name = set_name
        self.link = link

URL_TEMPLATE = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&view=grid&ProductTypeName=Cards&page={page}&Condition=Near+Mint&Rarity=Ultra+Rare|Illustration+Rare|Special+Illustration+Rare|Hyper+Rare|Rare+BREAK|Amazing+Rare|Shiny+Ultra+Rare|Prism+Rare|Secret+Rare&inStock=true&Language=English&ListingType=standard"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true')
    return parser.parse_args()

args = parse_args()

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("blink-settings=imagesEnabled=false")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# Determine total pages
driver.get(URL_TEMPLATE.format(page=1))
try:
    pagination = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-pagination")))
    total_pages = int(pagination.find_elements(By.TAG_NAME, "a")[-2].text)
except:
    total_pages = 1
print(f"Total pages detected: {total_pages}")

# Scrape each page sequentially
all_data = []

# Inside your scraping loop
for page in range(1, total_pages + 1):
    page_start = datetime.now()
    print(f"Scraping page {page}")
    driver.get(URL_TEMPLATE.format(page=page))

    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-result")))
    except:
        print(f"No listings on page {page}")
        continue

    listings = driver.find_elements(By.CLASS_NAME, "search-result")
    for listing in listings:
        try:
            name = listing.find_element(By.CSS_SELECTOR, "[class*='product-card__title']").text.strip()
            listing_count_text = listing.find_element(By.XPATH, ".//span[contains(@class, 'inventory__listing-count')]").text.strip()
            listing_count = int(re.search(r"\d+", listing_count_text).group())

            lowest_price = listing.find_element(By.XPATH, ".//span[contains(@class, 'inventory__price-with-shipping')]").text.strip().replace("$", "")
            rarity_section = listing.find_element(By.CLASS_NAME, "product-card__rarity__variant")
            rarity_parts = rarity_section.find_elements(By.TAG_NAME, "span")
            rarity = rarity_parts[0].text.strip() if len(rarity_parts) > 0 else "Unknown"
            card_number = rarity_parts[1].text.strip() if len(rarity_parts) > 1 else "Unknown"

            set_name = listing.find_element(By.CLASS_NAME, "product-card__set-name__variant").text.strip()
            market_price = listing.find_element(By.XPATH, ".//span[contains(@class, 'product-card__market-price--value')]").text.strip().replace("$", "")

            link_el = listing.find_element(By.XPATH, ".//a[contains(@data-testid, 'product-card__image')]")
            product_link = link_el.get_attribute("href")
            if not product_link.startswith("http"):
                product_link = "https://www.tcgplayer.com" + product_link

            all_data.append(Data(name, listing_count, lowest_price, market_price, rarity, card_number, set_name, product_link))
        except Exception as e:
            print(f"Error on page {page}: {e}")
    
    # Print time taken for this page
    page_end = datetime.now()
    page_elapsed = page_end - page_start
    p_min, p_sec = divmod(page_elapsed.total_seconds(), 60)
    print(f"Finished page {page} in {int(p_min)} min {int(p_sec)} sec")


driver.quit()

if all_data:
    db.writeDB(db.connectDB(), all_data)

end = datetime.now()
elapsed = end - start
minutes, seconds = divmod(elapsed.total_seconds(), 60)
msg = f"Finished Scraping {end.strftime('%Y-%m-%d %I:%M:%S %p')}\nTime elapsed: {int(minutes)} min {int(seconds)} sec"
send_discord_alert(msg, DISCORD_WEBHOOK)
