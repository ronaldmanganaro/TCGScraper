from playwright.sync_api import sync_playwright
import logging
import sys
import os

from db import connectDB

def scrape_add_to_cart_id(url):
    """
    Scrape the AddToCart ID from the given TCGPlayer product page.

    Args:
        url (str): The URL of the TCGPlayer product page.

    Returns:
        str: The AddToCart ID (e.g., '5522523') if found, else None.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        # Wait for the AddToCart button to load
        page.wait_for_selector("button[id^='btnAddToCart_FS_']")

        # Extract the button's ID
        button_id = page.locator("button[id^='btnAddToCart_FS_']").get_attribute("id")

        browser.close()

        if button_id:
            # Extract only the numeric part of the ID
            return button_id.split('_')[2].split('-')[0]

        return None

def add_tcgplayer_card_id_to_db(scryfall_id, tcgplayer_card_id):
    """
    Connect to the Scryfall database and insert/update the tcgplayer_card_id column.

    Args:
        scryfall_id (str): The Scryfall ID of the card.
        tcgplayer_card_id (str): The TCGplayer card ID to insert.
    """
    conn = connectDB('scryfall')
    cur = conn.cursor()
    try:
        cur.execute("""
            ALTER TABLE scryfall ADD COLUMN IF NOT EXISTS tcgplayer_card_id TEXT;
            UPDATE scryfall
            SET tcgplayer_card_id = %s
            WHERE id = %s;
        """, (tcgplayer_card_id, scryfall_id))
        conn.commit()
    except Exception as e:
        logging.warning("Failed to update tcgplayer_card_id for %s: %s", scryfall_id, e)
    finally:
        cur.close()
        conn.close()

def get_scryfall_id_by_card_details(name, set_name, collector_number):
    """
    Retrieve the Scryfall ID for a card based on its name, set, and collector number.

    Args:
        name (str): The name of the card.
        set_name (str): The name of the set.
        collector_number (str): The collector number of the card.

    Returns:
        str: The Scryfall ID if found, else None.
    """
    conn = connectDB('scryfall')
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT name, set_name, collector_number FROM scryfall
            WHERE name ILIKE %s AND set_name ILIKE %s AND collector_number = %s;
        """, (name, set_name, collector_number))
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as e:
        logging.warning("Failed to retrieve Scryfall ID for %s (%s, %s): %s", name, set_name, collector_number, e)
        return None
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    url = "https://www.tcgplayer.com/product/269069/magic-streets-of-new-capenna-sewer-crocodile?page=1&Language=English"
    add_to_cart_id = scrape_add_to_cart_id(url)
    print(f"AddToCart ID: {add_to_cart_id}")

    if add_to_cart_id:
        name = "Sewer Crocodile"  # Replace with actual card name
        set_name = "Streets of New Capenna"  # Replace with actual set name
        collector_number = "60"  # Replace with actual collector number

        scryfall_id = get_scryfall_id_by_card_details(name, set_name, collector_number)
        if scryfall_id:
            add_tcgplayer_card_id_to_db(scryfall_id, add_to_cart_id)
            print(f"Successfully added AddToCart ID {add_to_cart_id} to the database for Scryfall ID {scryfall_id}.")
        else:
            print("Failed to retrieve Scryfall ID for the card.")
