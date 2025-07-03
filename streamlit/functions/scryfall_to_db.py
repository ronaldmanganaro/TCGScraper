import psycopg2
import json
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import psycopg2.extras
import os

# Database connection parameters
user = 'rmangana'
password = 'password'
host = '52.73.212.127'
port = 5432
scryfall_db = 'scryfall'

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logging.info('Starting Scryfall DB import script.')

# Step 1: Connect to default 'postgres' database to check/create 'scryfall' database
conn = psycopg2.connect(
    dbname='postgres',
    user=user,
    password=password,
    host=host,
    port=port
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (scryfall_db,))
exists = cur.fetchone()
if not exists:
    cur.execute(f'CREATE DATABASE {scryfall_db}')
cur.close()
conn.close()

# Step 2: Connect to 'scryfall' database
conn = psycopg2.connect(
    dbname=scryfall_db,
    user=user,
    password=password,
    host=host,
    port=port
)
cur = conn.cursor()

# Drop the scryfall table if it exists to ensure schema matches
logging.info('Dropping and recreating scryfall_to_tcgplayer table.')
cur.execute("DROP TABLE IF EXISTS scryfall_to_tcgplayer;")
# Create table with all fields from the sample card
cur.execute("""
CREATE TABLE IF NOT EXISTS scryfall_to_tcgplayer (
    id TEXT PRIMARY KEY,
    tcgplayer_id INT,
    name TEXT,
    released_at DATE,
    set TEXT,
    set_name TEXT,
    collector_number TEXT,
    rarity TEXT,
    frame TEXT,
    full_art BOOLEAN,
    prices JSONB,
    tcgplayer_id_normal INT,
    tcgplayer_id_foil INT
);
""")
conn.commit()
logging.info('Table created.')

# Directory containing all set JSON files
data_dir = os.path.join(os.path.dirname(__file__), '../data/cards_by_set')
json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]

columns = [
    "id", "tcgplayer_id", "name", "released_at", "set", "set_name", "collector_number",
    "rarity", "frame", "full_art", "prices", "tcgplayer_id_normal", "tcgplayer_id_foil"
]
json_keys = ["prices"]
column_str = ", ".join(columns)
placeholder_str = ", ".join(["%s"] * len(columns))

all_values = []
for json_file in json_files:
    file_path = os.path.join(data_dir, json_file)
    logging.info(f'Loading card data from {file_path}.')
    with open(file_path, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    logging.info(f'Loaded {len(cards)} card(s) from {json_file}.')
    for card in cards:
        values = [
            json.dumps(card.get(col, {} if col in json_keys else None)) if col in json_keys else card.get(col)
            for col in columns
        ]
        all_values.append(values)

sql = f"""
INSERT INTO scryfall_to_tcgplayer ({column_str})
VALUES ({placeholder_str})
ON CONFLICT (id) DO UPDATE SET
    tcgplayer_id = EXCLUDED.tcgplayer_id,
    name = EXCLUDED.name,
    released_at = EXCLUDED.released_at,
    set = EXCLUDED.set,
    set_name = EXCLUDED.set_name,
    collector_number = EXCLUDED.collector_number,
    rarity = EXCLUDED.rarity,
    frame = EXCLUDED.frame,
    full_art = EXCLUDED.full_art,
    prices = EXCLUDED.prices,
    tcgplayer_id_normal = EXCLUDED.tcgplayer_id_normal,
    tcgplayer_id_foil = EXCLUDED.tcgplayer_id_foil
"""

batch_size = 500
for i in range(0, len(all_values), batch_size):
    batch = all_values[i:i+batch_size]
    psycopg2.extras.execute_batch(cur, sql, batch)
    logging.info(f'Inserted batch {i//batch_size+1} ({len(batch)} cards)')
conn.commit()
# Close the cursor and connection
cur.close()
conn.close()
logging.info("All cards inserted successfully into the 'scryfall' database.")
