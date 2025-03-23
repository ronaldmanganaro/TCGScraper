import psycopg2
import logging
import sys 
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

    dbname = 'TCGPlayerDB'
    user = 'rmangana'
    password = 'password'
    host = 'localhost'
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
        
def writeDB(connection: connection, data):
    insert_query = f"INSERT INTO public.prices (card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link) VALUES ({data}, {data})"    
    cursor = connection.cursor()
    
    try:    
        cursor.execute(insert_query, data)
        connection.commit()
            
    except Exception as e:
        if cursor:
            logging.error(f"unexpected error cursor {e}")
            cursor.close()
        if connection:
            logging.error(f"unexpected error connection {e}")
            connection.close()
    exit 