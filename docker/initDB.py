import psycopg2
import logging 

def createTable():
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TCGPlayerNew (
                Card VARCHAR(100),
                Listing_Quantity INT,
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
        
    except Exception as e:
        print("ad")

if __name__ == "__main__":
    createTable()
    