import psycopg2
import logging
import sys
import subprocess
from time import sleep 

import psycopg2.errorcodes

def createTable():
    myDb = 'tcgplayerdb'
    user = 'rmangana'
    password = 'password'
    host = 'localhost'
    port = 5432

    try:
        initConnection =  psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password, 
            host=host,
            port=port
        )
        initConnection.autocommit = True
        cursor = initConnection.cursor()

        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{myDb}';")
        exists = cursor.fetchone()
        logging.info(f"Database exists check result: {exists}")

        if not exists:
            logging.info(f"The database {myDb} does not exist, creating it...")
            cursor.execute(f"CREATE DATABASE {myDb};")
        else:
            logging.info(f"The database {myDb} exists, skipping creation.")
        
        cursor.close()
        initConnection.close()

        # Connect to the new/existing database
        newConnection =  psycopg2.connect(
                dbname=myDb,
                user=user,
                password=password, 
                host=host,
                port=port
            )
        cursor = newConnection.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                Date date,
                Card VARCHAR(100),
                Listing_Quantity INTEGER,
                Lowest_Price NUMERIC(10,2),
                Market_Price NUMERIC(10,2),
                Rarity VARCHAR(100),
                Card_Number VARCHAR(100),
                Set_Name VARCHAR(100),
                Link TEXT
            )               
        """)
        newConnection.commit()
        cursor.close()
        newConnection.close()
        logging.info("Table creation complete.")
        
    except psycopg2.OperationalError as e:
        logging.error(f"Connection error: {e}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Send logs to stdout
        ]
    )
    
    createTable()
