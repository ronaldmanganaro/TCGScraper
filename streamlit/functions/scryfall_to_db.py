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
logging.info('Dropping and recreating scryfall table.')
cur.execute("DROP TABLE IF EXISTS scryfall;")
# Create table with all fields from the sample card
cur.execute("""
CREATE TABLE IF NOT EXISTS scryfall (
    object TEXT,
    id TEXT PRIMARY KEY,
    oracle_id TEXT,
    multiverse_ids JSONB,
    mtgo_id INT,
    mtgo_foil_id INT,
    tcgplayer_id INT,
    cardmarket_id INT,
    name TEXT,
    lang TEXT,
    released_at DATE,
    uri TEXT,
    scryfall_uri TEXT,
    layout TEXT,
    highres_image BOOLEAN,
    image_status TEXT,
    image_uris JSONB,
    mana_cost TEXT,
    cmc FLOAT,
    type_line TEXT,
    oracle_text TEXT,
    power TEXT,
    toughness TEXT,
    colors JSONB,
    color_identity JSONB,
    keywords JSONB,
    legalities JSONB,
    games JSONB,
    reserved BOOLEAN,
    game_changer BOOLEAN,
    foil BOOLEAN,
    nonfoil BOOLEAN,
    finishes JSONB,
    oversized BOOLEAN,
    promo BOOLEAN,
    reprint BOOLEAN,
    variation BOOLEAN,
    set_id TEXT,
    set TEXT,
    set_name TEXT,
    set_type TEXT,
    set_uri TEXT,
    set_search_uri TEXT,
    scryfall_set_uri TEXT,
    rulings_uri TEXT,
    prints_search_uri TEXT,
    collector_number TEXT,
    digital BOOLEAN,
    rarity TEXT,
    flavor_text TEXT,
    card_back_id TEXT,
    artist TEXT,
    artist_ids JSONB,
    illustration_id TEXT,
    border_color TEXT,
    frame TEXT,
    full_art BOOLEAN,
    textless BOOLEAN,
    booster BOOLEAN,
    story_spotlight BOOLEAN,
    edhrec_rank INT,
    penny_rank INT,
    prices JSONB,
    related_uris JSONB,
    purchase_uris JSONB
);
""")
conn.commit()
logging.info('Table created.')

# Directory containing all set JSON files
data_dir = os.path.join(os.path.dirname(__file__), '../data/cards_by_set')
json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]

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
INSERT INTO scryfall ({column_str})
VALUES ({placeholder_str})
ON CONFLICT (id) DO UPDATE SET
    foil = EXCLUDED.foil,
    nonfoil = EXCLUDED.nonfoil,
    finishes = EXCLUDED.finishes
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
