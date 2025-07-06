import psycopg2
import logging
import sys 
from datetime import datetime
from psycopg2.extensions import connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Send logs to stdout
    ]
)

def connectDB() -> connection: 

    dbname = 'tcgplayerdb'
    user = 'rmangana'
    password = 'password'
    host = '52.73.212.127'
    port = 5432

    try:
        newConnection =  psycopg2.connect(
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

