import psycopg2
import logging
import sys

import psycopg2.errorcodes

def createTable():
    myDb = 'TCGPlayerDB'
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

        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = 'postgres';")
        exists = cursor.fetchone

        if not exists:
            logging.info(f"The {myDb} does not exist executing query")
            cursor.execute(f"CRAETE DATABASE '{myDb}';")
        else:
            logging.info(f"The {myDb} exists skipping query")
        
        newConnection =  psycopg2.connect(
                dbname=myDb,
                user=user,
                password=password, 
                host=host,
                port=port
            )
        cursor = newConnection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TCGPlayerNew (
                Card VARCHAR(100),
                Listing_Quantity integer,
                Lowest_Price MONEY,
                Market_Price MONEY,
                Rarity VARCHAR(100),
                Card_Number VARCHAR(100),
                Set_Name VARCHAR(100),
                Link TEXT
            )               
        """)
        newConnection.commit()
        cursor.close()
        newConnection.close()
        
    except psycopg2.OperationalError as e:
        logging.info(f"Connection error: {e.pgcode}")

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Send logs to stdout
        ]
    )

    createTable()