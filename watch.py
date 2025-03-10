import time
import re
import argparse
import gspread

import requests

from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Listing:
    def __init__(self, cardName, seller, price, quantity):
        self.cardName = cardName
        self.seller = seller
        self.price = price
        self.quantity = quantity
    
    def display(self):
        return f"Seller Name: {self.seller} \nCard Price: {self.price} \nQuantity {self.quantity} \nCard Name: {self.cardName}"

cards = [
    "117889/pokemon-xy-fates-collide-alakazam-ex-full-art",
    #"117854/pokemon-xy-fates-collide-lugia-break",
    "121949/pokemon-xy-promos-ho-oh-break",
    "147234/pokemon-jumbo-cards-ho-oh-break-xy154-xy-black-star-promo",
    "131869/pokemon-jumbo-cards-arcanine-break-xy180-xy-black-star-promos",
    "481762/pokemon-world-championship-decks-greninja-break-2016-cody-walinski",
    #"111548/pokemon-xy-breakpoint-greninja-break",
    #"165780/pokemon-sm-forbidden-light-lucario-gx-full-art",
    "96044/pokemon-xy-primal-clash-camerupt-ex-146-full-art",
    #"107272/pokemon-xy-breakthrough-houndoom-ex-full-art",
    "92174/pokemon-xy-furious-fists-m-heracross-ex",
    "94157/pokemon-xy-phantom-forces-m-manectric-ex",
    "96413/pokemon-xy-promos-kingdra-xy39-prerelease",
    "131006/pokemon-sm-guardians-rising-sylveon-gx"
]

card = "117889/pokemon-xy-fates-collide-alakazam-ex-full-art"

def send_discord_alert(message, webhook_url):
    data = {"content": message}
    requests.post(webhook_url, json=data)

# Command-line argument for headless mode
def parse_args():
    parser = argparse.ArgumentParser(description="Scrape TCGPlayer listings")
    parser.add_argument('--headless', action='store_true', help="Run the script in headless mode")
    return parser.parse_args

# Initialize command-line arguments
args = parse_args() 

# Set headless mode based on the flag
options = webdriver.ChromeOptions()
#options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
for card in cards:
    url = f"https://www.tcgplayer.com/product/{card}?Language=English&Condition=Near+Mint&page=1"
    driver.get(url)
    
    wait = WebDriverWait(driver, 15)
    # Wait for the page to load
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.add-to-cart__available")))
    sections = driver.find_elements(By.CSS_SELECTOR, "section.listing-item")  # Replace with actual section selector

    listings = []

    for section in sections:
        div = section.find_element(By.CLASS_NAME, "listing-item__listing-data")
        sellerInfo = div.find_element(By.CLASS_NAME, "listing-item__listing-data__seller")
        sellerName = sellerInfo.find_element(By.CLASS_NAME, "seller-info__name").text
        
        cardInfo = div.find_element(By.CLASS_NAME, "listing-item__listing-data__info")
        cardPrice = cardInfo.find_element(By.CLASS_NAME, "listing-item__listing-data__info__price").text

        quantityInfo = div.find_element(By.CLASS_NAME, "listing-item__listing-data__add")
        cardQuantity = quantityInfo.find_element(By.CSS_SELECTOR, "span.add-to-cart__available").text.replace("of ", "")
        
        newListing = Listing(card.split('/')[1], sellerName, cardPrice, cardQuantity)
        listings.append(newListing) 
        print(f"{sellerName} {cardPrice} {cardQuantity}")

    if listings[0].seller  == "Holo Hits TCG":
        print("You are the cheapest listing")
    else:
        myPrice = 0
        for listing in listings:
            if listing.seller == "Holo Hits TCG":
                myPrice = listing.price + '\n'
        print("ALERT CHEAPER CARD!")
        msg = listings[0].display() + f"\nMy Price: {myPrice}" + "\nLINK: " + url + "\nSeller Link: " + f"https://store.tcgplayer.com/admin/product/manage/{card.split("/")[0]}?OnlyMyInventory=false&CategoryId=3&SetNameId=0&Rarity=0&DidSearch=true"
        
        send_discord_alert( msg, "https://discord.com/api/webhooks/1348736048066461788/7cLvt3ajZ9-hX7ZIFjurWyNyv87ka44-eViI3U2eWXEdAogqMehev5hIsGduUCbdkudV")
