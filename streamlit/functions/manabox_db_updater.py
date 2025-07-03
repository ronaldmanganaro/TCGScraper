from playwright.sync_api import sync_playwright
from functions import db
import logging
import sys
import os
import requests
from psycopg2 import sql

def scrape_tcgplayer_id(url):
    """
    Scrape the AddToCart ID from the given TCGPlayer product page.

    Args:
        url (str): The URL of the TCGPlayer product page.

    Returns:
        str: The AddToCart ID (e.g., '5522523') if found, else None.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

def add_tcgplayer_card_id_to_db(scryfall_id, tcgplayer_card_id, is_foil):
    """
    Connect to the Scryfall database and insert/update the tcgplayer_card_id column.

    Args:
        scryfall_id (str): The Scryfall ID of the card.
        tcgplayer_card_id (str): The TCGplayer card ID to insert.
        is_foil (bool): Whether this is a foil card.
    """
    conn = db.connectDB('scryfall')
    cur = conn.cursor()
    print(f"Adding TCGPlayer ID {tcgplayer_card_id} for Scryfall ID {scryfall_id} (Foil: {is_foil})")
    column_name = "tcgplayer_id_foil" if is_foil else "tcgplayer_id_normal"
    try:
        # Add the column if it doesn't exist
        cur.execute(f"ALTER TABLE scryfall_to_tcgplayer ADD COLUMN IF NOT EXISTS {column_name} TEXT;")
        # Update the value
        cur.execute(
            f"UPDATE scryfall_to_tcgplayer SET {column_name} = %s WHERE id = %s;",
            (tcgplayer_card_id, scryfall_id)
        )
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
            SELECT name, set_name, collector_number FROM scryfall_to_tcgplayer
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

def get_scryfall_card_info(name, set_symbol, collector_number):
    """
    Get card json from Scryfall using API, add the card to the database if not present, and return the scryfall_id.

    Args:
        name (str): The name of the card.
        set_name (str): The set code (not full set name, e.g., 'snc' for Streets of New Capenna).
        collector_number (str): The collector number of the card.

    Returns:
        str: The Scryfall ID if found and inserted, else None.
    """
    
    # Scryfall API expects set code, not full set name
    api_url = f"https://api.scryfall.com/cards/{set_symbol.lower()}/{collector_number}"
    response = requests.get(api_url)
    if response.status_code != 200:
        logging.warning(f"Scryfall API request failed: {response.status_code} {response.text}")
        return None
    card_json = response.json()
    scryfall_id = card_json.get('id')
    if not scryfall_id:
        logging.warning("No Scryfall ID found in API response.")
        return None

    # Insert card into DB if not present
    conn = db.connectDB('scryfall')
    cur = conn.cursor()
    try:
        # Check if card already exists
        cur.execute("SELECT id FROM scryfall_to_tcgplayer WHERE id = %s", (scryfall_id,))
        if not cur.fetchone():
            # Insert minimal card info (expand as needed)
            cur.execute(
                sql.SQL("""
                    INSERT INTO scryfall_to_tcgplayer (id, name, set_name, collector_number, json_data)
                    VALUES (%s, %s, %s, %s, %s)
                """),
                (scryfall_id, card_json.get('name'), card_json.get('set'), card_json.get('collector_number'), card_json)
            )
            conn.commit()
    except Exception as e:
        logging.warning(f"Failed to insert card into scryfall DB: {e}")
        scryfall_id = None
    finally:
        cur.close()
        conn.close()
    return scryfall_id

def get_tcgplayerid_from_scryfall(set_code, collector_number, lang='en'):
    """
    Fetch a single card from Scryfall API by set code and collector number, and add it to the scryfall table in the database.
    Args:
        set_code (str): The Scryfall set code (e.g., 'snc').
        collector_number (str): The card's collector number (e.g., '60').
        lang (str): Language code (default 'en').
    """
    import requests
    import json
    columns = [
        'object', 'id', 'oracle_id', 'multiverse_ids', 'mtgo_id', 'mtgo_foil_id', 'tcgplayer_id', 'cardmarket_id', 'name', 'lang', 'released_at', 'uri', 'scryfall_uri', 'layout', 'highres_image', 'image_status', 'image_uris', 'mana_cost', 'cmc', 'type_line', 'oracle_text', 'power', 'toughness', 'colors', 'color_identity', 'keywords', 'legalities', 'games', 'reserved', 'game_changer', 'foil', 'nonfoil', 'finishes', 'oversized', 'promo', 'reprint', 'variation', 'set_id', 'set', 'set_name', 'set_type', 'set_uri', 'set_search_uri', 'scryfall_set_uri', 'rulings_uri', 'prints_search_uri', 'collector_number', 'digital', 'rarity', 'flavor_text', 'card_back_id', 'artist', 'artist_ids', 'illustration_id', 'border_color', 'frame', 'full_art', 'textless', 'booster', 'story_spotlight', 'edhrec_rank', 'penny_rank', 'prices', 'related_uris', 'purchase_uris', 'tcgplayer_card_id'
    ]
    url = f"https://api.scryfall.com/cards/{set_code}/{collector_number}?lang={lang}"
    print(f"scryfall url: {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.warning(f"Scryfall API request failed: {resp.status_code} {resp.text}")
        return False
    card = resp.json()
    values = []
    for col in columns:
        val = card.get(col)
        if isinstance(val, (dict, list)):
            val = json.dumps(val)
        values.append(val)
    placeholders = ','.join(['%s'] * len(columns))
    insert_query = f"""
        INSERT INTO scryfall_to_tcgplayer ({','.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE SET
        {', '.join([f'{col}=EXCLUDED.{col}' for col in columns if col != 'id'])}
    """
    conn = db.connectDB('scryfall')
    cur = conn.cursor()
    try:
        cur.execute(insert_query, values)
        conn.commit()
        logging.info(f"Inserted/updated card {card.get('name')} ({set_code} {collector_number}) in DB.")
        return card.get("tcgplayer_id")
    except Exception as e:
        logging.warning(f"Failed to insert/update card {card.get('id')}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

