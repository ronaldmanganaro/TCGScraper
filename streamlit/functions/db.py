import psycopg2
import logging
import sys
from datetime import datetime
from psycopg2.extensions import connection
import requests

# Configure logging
logging.basicConfig(
    # Set log level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Send logs to stdout
    ]
)

def connectDB(isTest=False) -> connection:

    if isTest:
        # Test database connection
        dbname = 'tcgplayerdbtest'
    else:
        dbname = 'tcgplayerdb'
    user = 'rmangana'
    password = 'password'
    host = '52.73.212.127'
    port = 5432

    try:
        newConnection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = newConnection.cursor()
    except Exception as e:
        if cursor:
            logging.error(f"unexpected error cursor {e}")
            cursor.close()
        if newConnection:
            logging.error(f"unexpected error connection {e}")
            connection.close()

    return newConnection

def connectDB(dbname, isTest=False) -> connection:

    user = 'rmangana'
    password = 'password'
    host = '52.73.212.127'
    port = 5432

    try:
        newConnection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = newConnection.cursor()
    except Exception as e:
        if cursor:
            logging.error(f"unexpected error cursor {e}")
            cursor.close()
        if newConnection:
            logging.error(f"unexpected error connection {e}")
            connection.close()

    return newConnection

def writeDB(connection: connection, databaseEntries):
    today = datetime.now()  # Keeps full timestamp

    cursor = connection.cursor()

    for entry in databaseEntries:
        cleaned_rarity = entry.rarity.replace(',', '')

        insert_query = """INSERT INTO public.prices  
            (card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link, date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        values = (
            entry.card, entry.listing_quantity, entry.lowest_price,
            entry.market_price, cleaned_rarity, entry.card_number,
            entry.set_name, entry.link, today
        )

        try:
            cursor.execute(insert_query, values)
            connection.commit()
        except Exception as e:
            print("Error inserting data:", e)
            connection.rollback()

    cursor.close()

def get_cards_by_listing_quantity(connection: connection, min_quantity: int):
    cursor = connection.cursor()
    query = """
        SELECT DISTINCT card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link, date
        FROM public.prices
        WHERE listing_quantity <= %s
        ORDER BY card ASC
    """
    try:
        cursor.execute(query, (min_quantity,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        logging.error(f"Error querying cards by listing quantity: {e}")
        return []
    finally:
        cursor.close()

def get_card_name(connection: connection, min_quantity: int):
    cursor = connection.cursor()
    query = """
        SELECT DISTINCT p.card, p.card_number, p.link, p.listing_quantity
        FROM public.prices p
        INNER JOIN (
            SELECT card, MAX(date) AS latest_date
            FROM public.prices
            WHERE listing_quantity <= %s
            GROUP BY card
        ) latest ON p.card = latest.card AND p.date = latest.latest_date
        WHERE p.listing_quantity <= %s
        ORDER BY p.card ASC;
    """
    try:
        cursor.execute(query, (min_quantity, min_quantity))
        results = cursor.fetchall()
        return results
    except Exception as e:
        logging.error(f"Error querying cards by listing quantity: {e}")
        return []
    finally:
        cursor.close()


def get_card_data(connection: connection, card_name, card_number):
    cursor = connection.cursor()
    query = """
        SELECT date, card, listing_quantity, lowest_price, market_price, link, rarity, card_number, set_name
        FROM public.prices
        WHERE card = %s AND card_number = %s
       ORDER BY date DESC
        LIMIT 1 
    """
    try:
        cursor.execute(query, (card_name, card_number,))
        result = cursor.fetchall()
        return result
    except Exception as e:
        logging.error(f"Error querying card data: {e}")
        return []
    finally:
        cursor.close()


def get_price_date(connection: connection, card_name, card_number):
    cursor = connection.cursor()
    query = """
        SELECT date, lowest_price, market_price, listing_quantity, velocity 
        FROM public.prices
        WHERE card = %s AND card_number = %s
        ORDER BY date DESC
    """
    try:
        cursor.execute(query, (card_name, card_number,))
        result = cursor.fetchall()
        return result
    except Exception as e:
        logging.error(f"Error querying price date: {e}")
        return None
    finally:
        logging.info(f"Finished querying price date for card: {card_name}")
        cursor.close()


def estimate_velocity(connection: connection, card_name, card_number):
    cursor = connection.cursor()
    query = """
        SELECT 
        date,
        listing_quantity,
        -- Calculate velocity sold as the drop in listing quantity from previous day
        COALESCE(
            LAG(listing_quantity) OVER (ORDER BY date) - listing_quantity,
            0
        ) AS velocity_sold
        FROM public.prices
        WHERE card = %s AND card_number = %s
        ORDER BY date DESC
    """
    try:
        cursor.execute(query, (card_name, card_number,))
        result = cursor.fetchall()
        return result
    except Exception as e:
        logging.error(f"Error estimating velocity: {e}")
        return None
    finally:
        cursor.close()


def add_card_data(converted_date, card_number, market_price, lowest_price):
    connection = connectDB()
    if not connection:
        logging.error("Failed to connect to the database.")
        return

    try:
        cursor = connection.cursor()

        # Pull data for card already in DB
        query = """
            SELECT card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link
            FROM public.prices
            WHERE card_number ILIKE %s
            ORDER BY date DESC
            LIMIT 1
        """
        cursor.execute(query, (card_number,))
        result = cursor.fetchone()
        logging.info(f"Querying for card_number: {card_number} {result}")

        if result is None:
            logging.error(
                f"No existing card found in DB for card_number: {card_number}. Cannot insert new price entry.")
            return  # or handle as needed

        # Insert new price entry
        insert_query = """
            INSERT INTO public.prices (date, card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (converted_date,
                                      result[0], None, lowest_price, market_price, result[4], card_number, result[6], result[7]))
        connection.commit()
        logging.info(
            f"Successfully added new price entry for card_number: {card_number}")

    except Exception as e:
        logging.error(f"Error in add_card_data: {e}")
        connection.rollback()
    finally:
        if connection:
            connection.close()

def get_tcgplayer_id_from_db(scryfall_id):
    conn = connectDB("scryfall")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tcgplayer_id FROM scryfall
            WHERE id = %s
            LIMIT 1
        """, (scryfall_id,))
        result = cur.fetchone()
        return result[0] if result and result[0] is not None else None
    finally:
        cur.close()
        conn.close()

def get_tcgplayer_id_from_db(scryfall_id):
    conn = connectDB("scryfall")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tcgplayer_id FROM scryfall
            WHERE id = %s
            LIMIT 1
        """, (scryfall_id,))
        result = cur.fetchone()
        return result[0] if result and result[0] is not None else None
    finally:
        cur.close()
        conn.close()

def get_tcgplayer_id_from_scryfall_id(scryfall_id, foil=False):
    """
    Given a Scryfall card ID, fetch the card from the Scryfall API and return its TCGplayer ID.
    If foil=True, prefer tcgplayer_foil_id. If foil=False, prefer tcgplayer_nonfoil_id.
    Fallback to tcgplayer_id if specific field is missing.
    """
    url = f"https://api.scryfall.com/cards/{scryfall_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if foil:
                tcg_id = data.get("tcgplayer_foil_id")
                if tcg_id is not None:
                    return tcg_id
            else:
                tcg_id = data.get("tcgplayer_nonfoil_id")
                if tcg_id is not None:
                    return tcg_id
            # Fallback
            return data.get("tcgplayer_id")
    except Exception as e:
        logging.warning(
            f"Error fetching Scryfall card by id {scryfall_id}: {e}")
    return None

def get_tcgplayer_id(card_name, set_name):
    tcg_id = get_tcgplayer_id_from_db()
    if tcg_id:
        return tcg_id
    return get_tcgplayer_id_from_scryfall_id(card_name, set_name)

def batch_get_tcgplayer_ids_by_name_collector_set(card_info_list):
    """
    card_info_list: List of (name, collector_number, set)
    Returns: dict mapping (name, collector_number, set) -> tcgplayer_card_id
    """

    conn = connectDB("scryfall")
    cur = conn.cursor()
    try:
        # Build WHERE clause for batch query
        print(f"{len(card_info_list)} cards to process")
        # Query by (name, collector_number, set_name) only, ignore foil in SQL
        format_strings = ','.join(['(%s,%s,%s)'] * len(card_info_list))
        params = []
        for name, collector_number, set_name, foil in card_info_list:
            params.extend([name, collector_number, set_name])
        query = f"""
            SELECT name, collector_number, set_name, tcgplayer_id_normal, tcgplayer_id_foil FROM scryfall
            WHERE (name, collector_number, set_name) IN ({format_strings})
        """
        cur.execute(query, params)
        results = cur.fetchall()
        # Build a lookup for quick access
        result_dict = {(n, c, s): (normal, foil) for n, c, s, normal, foil in results}
        lookup = {}
        for name, collector_number, set_name, foil in card_info_list:
            ids = result_dict.get((name, collector_number, set_name))
            if ids:
                tcg_id = ids[1] if foil else ids[0]
                if tcg_id is not None:
                    lookup[(name, collector_number, set_name, foil)] = tcg_id
        return lookup
    finally:
        cur.close()
        conn.close()