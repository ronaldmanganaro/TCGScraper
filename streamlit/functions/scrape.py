#!/usr/bin/env python3

import time
import re
import db
import argparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape TCGPlayer listings")
    parser.add_argument('--headless', action='store_true', help="Run the script in headless mode")
    parser.add_argument('--sheets', action='store_true')
    return parser.parse_args()

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

def scrape_tcgplayer():
    # TCGPlayer search URL
    URL = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&view=grid&ProductTypeName=Cards&page=1&Condition=Near+Mint&Rarity=Ultra+Rare|Illustration+Rare|Special+Illustration+Rare|Hyper+Rare|Rare+BREAK|Amazing+Rare|Shiny+Ultra+Rare|Prism+Rare|Secret+Rare"
    # URL for teesting
    #URL = "https://www.tcgplayer.com/search/pokemon/product?Condition=Near+Mint&productLineName=pokemon&q=break&view=grid&Rarity=Rare+BREAK&page=1"
    # Command-line argument for headless mode

    # Initialize command-line arguments
    args = parse_args()

    # Set headless mode based on the flag
    options = webdriver.ChromeOptions()
    if args.headless:
        options.add_argument("--headless")
    else:
        options.add_argument("--start-maximized")

    # Initialize Selenium WebDriver
    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Get the total number of pages
    try:
        pagination = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-pagination")))
        total_pages = int(pagination.find_elements(By.TAG_NAME, "a")[-2].text)
    except:
        total_pages = 1  # If no pagination is found, assume only one page

    print(f"Total pages detected: {total_pages}")

    # Collect data in a list before sending it to Google Sheets
    all_data = []
    databaseEntries: Data = []

    # Scraping loop for each page
    for page in range(1, total_pages + 1):
        print(f"Scraping page {page} of {total_pages}...")
        driver.get(URL.replace("page=1", f"page={page}"))
        time.sleep(3)

        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-result")))
        except:
            print(f"Skipping page {page}, no listings found.")
            continue

        listings = driver.find_elements(By.CLASS_NAME, "search-result")
        for listing in listings:
            try:
                name = WebDriverWait(listing, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='product-card__title']"))
                ).text.strip()

                listing_count_text = listing.find_element(By.XPATH, ".//span[contains(@class, 'inventory__listing-count')]").text.strip()
                listing_count = int(re.search(r"\d+", listing_count_text).group())

                lowest_price = listing.find_element(By.XPATH, ".//span[contains(@class, 'inventory__price-with-shipping')]").text.strip().replace("$", "")

                rarity_section = listing.find_element(By.CLASS_NAME, "product-card__rarity__variant")
                rarity_parts = rarity_section.find_elements(By.TAG_NAME, "span")
                rarity = rarity_parts[0].text.strip() if len(rarity_parts) > 0 else "Unknown"
                card_number = rarity_parts[1].text.strip() if len(rarity_parts) > 1 else "Unknown"

                set_name = listing.find_element(By.CLASS_NAME, "product-card__set-name__variant").text.strip()  
                market_price = listing.find_element(By.XPATH, ".//span[contains(@class, 'product-card__market-price--value')]").text.strip().replace("$", "")

                product_link_element = listing.find_element(By.XPATH, ".//a[contains(@data-testid, 'product-card__image')]")
                product_link = product_link_element.get_attribute("href")
                if product_link and not product_link.startswith("http"):
                    product_link = "https://www.tcgplayer.com" + product_link

                # Store data in the list
                all_data.append([name, listing_count, lowest_price, market_price, rarity, card_number, set_name, product_link])
                
                entry = Data(name, listing_count, lowest_price, market_price, rarity, card_number, set_name, product_link)
                databaseEntries.append(entry)
            except Exception as e:
                print(f"Error processing listing: {e}")

    # Send all collected data to Google Sheets at once
    if databaseEntries:
        db.writeDB(db.connectDB(), databaseEntries)

    # Close the WebDriver
    driver.quit()

scrape_tcgplayer()