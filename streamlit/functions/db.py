import psycopg2
import logging
import sys
from datetime import datetime
from psycopg2.extensions import connection
import pandas as pd
import streamlit as st

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
        SELECT DISTINCT card, card_number
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
        SELECT date, lowest_price, market_price, listing_quantity
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
        print(result)
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
                       result[0], 999, lowest_price, market_price, result[4], card_number, result[6], result[7]))
        connection.commit()
        logging.info(
            f"Successfully added new price entry for card_number: {card_number}")

    except Exception as e:
        logging.error(f"Error in add_card_data: {e}")
        connection.rollback()
    finally:
        if connection:
            connection.close()
