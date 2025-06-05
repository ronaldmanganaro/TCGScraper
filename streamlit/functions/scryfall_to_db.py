import psycopg2
import json
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import psycopg2.extras

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

# Load Scryfall JSON data
logging.info('Loading card data from scryfall_cards.json.')
with open('scryfall_cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)
logging.info(f'Loaded {len(cards)} card(s).')

columns = [
    "object", "id", "oracle_id", "multiverse_ids", "mtgo_id", "mtgo_foil_id", "tcgplayer_id", "cardmarket_id",
    "name", "lang", "released_at", "uri", "scryfall_uri", "layout", "highres_image", "image_status", "image_uris",
    "mana_cost", "cmc", "type_line", "oracle_text", "power", "toughness", "colors", "color_identity", "keywords",
    "legalities", "games", "reserved", "game_changer", "foil", "nonfoil", "finishes", "oversized", "promo",
    "reprint", "variation", "set_id", "set", "set_name", "set_type", "set_uri", "set_search_uri", "scryfall_set_uri",
    "rulings_uri", "prints_search_uri", "collector_number", "digital", "rarity", "flavor_text", "card_back_id",
    "artist", "artist_ids", "illustration_id", "border_color", "frame", "full_art", "textless", "booster",
    "story_spotlight", "edhrec_rank", "penny_rank", "prices", "related_uris", "purchase_uris"
]

# List of keys to convert to JSON
json_keys = {
    "multiverse_ids", "image_uris", "colors", "color_identity", "keywords", "legalities", "games",
    "finishes", "artist_ids", "prices", "related_uris", "purchase_uris"
}

# Prepare columns and placeholders
column_str = ", ".join(columns)
placeholder_str = ", ".join(["%s"] * len(columns))

# Insert cards into the table using batch insert for efficiency
batch_size = 500  # You can tune this value for your environment
all_values = []
for card in cards:
    values = [
        json.dumps(card.get(col, {} if col in json_keys else None)) if col in json_keys else card.get(col)
        for col in columns
    ]
    all_values.append(values)

sql = f"""
INSERT INTO scryfall ({column_str})
VALUES ({placeholder_str})
ON CONFLICT (id) DO NOTHING
"""

for i in range(0, len(all_values), batch_size):
    batch = all_values[i:i+batch_size]
    psycopg2.extras.execute_batch(cur, sql, batch)
    logging.info(f'Inserted batch {i//batch_size+1} ({len(batch)} cards)')
conn.commit()
# Close the cursor and connection
cur.close()
conn.close()
logging.info("All cards inserted successfully into the 'scryfall' database.")
