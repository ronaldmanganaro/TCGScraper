import time
import re

import helper
import argparse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

# Set the minimum listing threshold
MIN_LISTINGS = 5
# TCGPlayer search URL
URL = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&view=grid&ProductTypeName=Cards&page=1&Condition=Near+Mint&Rarity=Ultra+Rare|Illustration+Rare|Special+Illustration+Rare|Hyper+Rare|Rare+BREAK|Amazing+Rare|Shiny+Ultra+Rare|Prism+Rare|Secret+Rare"

# Command-line argument for headless mode
def parse_args():
    parser = argparse.ArgumentParser(description="Scrape TCGPlayer listings")
    parser.add_argument('--headless', action='store_true', help="Run the script in headless mode")
    return parser.parse_args()

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

# Set up OAuth2 authentication with gspread
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Create a new sheet with the current date and time
now = datetime.now()
sheet_name = now.strftime("%Y-%m-%d_%H-%M-%S")
spreadsheet = client.create(sheet_name)
worksheet = spreadsheet.get_worksheet(0)  # Create a new worksheet

# Add header row to the sheet
headers = ["Product Name", "Number of Listings", "Lowest Price", "Market Price", "Rarity", "Card Number", "Set Name", "Product Link"]
worksheet.append_row?(headers)

# Share the sheet with your email (replace with your email address)
try:
    drive_service = build('drive', 'v3', credentials=creds)
    drive_service.permissions().create(
        fileId=spreadsheet.id,
        body={
            'type': 'user',
            'role': 'writer',  # You can change this to 'reader' if you only want view access
            'emailAddress': 'ronaldmanganaro@gmail.com'  # Replace with your email address
        }
    ).execute()

    print("Sheet shared successfully with ronaldmanganaro@gmail.com!")
except HttpError as error:
    print(f"An error occurred: {error}")

# Collect data in a list before sending it to Google Sheets
all_data = []

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

        except Exception as e:
            print(f"Error processing listing: {e}")

# Send all collected data to Google Sheets at once
if all_data:
    worksheet.append_rows(all_data)
    print("✅ Scraping complete. Data has been added to Google Sheets.")

# Close the WebDriver
driver.quit()
