import psycopg2
import logging
import sys 
from psycopg2 import sql 

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Send logs to stdout
    ]
)

def writeDB():

    dbname = 'TCGPlayerDB'
    user = 'rmangana'
    password = 'password'
    host = 'localhost'
    port = 5432

    try:
        connection =  psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password, 
            host=host,
            port=port
        )
        
        cursor = connection.cursor()
        
        insert_query = "INSERT INTO test (column1, column2) VALUES (%s, %s)"
        
        data = ('test1', 'test2')
        
        cursor.execute(insert_query, data)
        
        connection.commit()
        
    except Exception as e:
        if cursor:
            logging.error(f"unexpected error cursor {e}")
            cursor.close()
        if connection:
            logging.error(f"unexpected error connection {e}")
            connection.close()
            
    exit()
        
        