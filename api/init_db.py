#!/usr/bin/env python3
"""
Database initialization script for TCG Scraper API
Creates all necessary tables and initial data
"""

import asyncio
import os
import logging
from services.database import DatabaseService
from services.auth import AuthService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQL for creating tables
CREATE_TABLES_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Sets table
CREATE TABLE IF NOT EXISTS sets (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    release_date DATE,
    block VARCHAR(100),
    type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cards table
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    set_name VARCHAR(255),
    set_code VARCHAR(10),
    rarity VARCHAR(50),
    tcg_player_id VARCHAR(50) UNIQUE,
    mana_cost VARCHAR(50),
    cmc INTEGER,
    type_line VARCHAR(255),
    oracle_text TEXT,
    power VARCHAR(10),
    toughness VARCHAR(10),
    colors TEXT[], -- Array of colors
    color_identity TEXT[], -- Array of color identity
    keywords TEXT[], -- Array of keywords
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (set_code) REFERENCES sets(code)
);

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    condition VARCHAR(20) NOT NULL DEFAULT 'NM',
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10,2),
    foil BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    foil_price DECIMAL(10,2),
    source VARCHAR(50) DEFAULT 'tcgplayer',
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    UNIQUE(card_id, date, source)
);

-- Watchlist table
CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    target_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    UNIQUE(user_id, card_id)
);

-- Sales data table
CREATE TABLE IF NOT EXISTS sales_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    sale_date DATE DEFAULT CURRENT_DATE,
    platform VARCHAR(50) DEFAULT 'tcgplayer',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cards_tcg_player_id ON cards(tcg_player_id);
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_set_code ON cards(set_code);
CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_card_id ON inventory(card_id);
CREATE INDEX IF NOT EXISTS idx_price_history_card_id ON price_history(card_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""

async def init_database():
    """Initialize the database with tables and default data"""
    logger.info("Starting database initialization...")
    
    db_service = DatabaseService()
    auth_service = AuthService()
    
    try:
        # Create tables
        logger.info("Creating database tables...")
        await db_service.execute_query(CREATE_TABLES_SQL, fetch_all=False)
        logger.info("✅ Database tables created successfully")
        
        # Check if admin user exists
        admin_user = await db_service.get_user_by_username('rmangana')
        if not admin_user:
            logger.info("Creating admin user...")
            admin_result = await auth_service.create_user('rmangana', 'admin@tcgscraper.com', 'admin123')
            if admin_result:
                # Make user admin
                await db_service.execute_query(
                    "UPDATE users SET is_admin = TRUE WHERE username = %s",
                    ('rmangana',),
                    fetch_all=False
                )
                logger.info("✅ Admin user created successfully")
            else:
                logger.error("❌ Failed to create admin user")
        else:
            logger.info("✅ Admin user already exists")
        
        # Add some sample sets if none exist
        sets_count = await db_service.execute_query("SELECT COUNT(*) as count FROM sets", fetch_one=True)
        if sets_count['count'] == 0:
            logger.info("Adding sample sets...")
            sample_sets = [
                ('DFT', 'Duskmourn: House of Horror', '2024-09-27', 'Duskmourn', 'expansion'),
                ('DSK', 'Duskmourn: House of Horror Commander', '2024-09-27', 'Duskmourn', 'commander'),
                ('BLB', 'Bloomburrow', '2024-08-02', 'Bloomburrow', 'expansion'),
                ('MH3', 'Modern Horizons 3', '2024-06-14', 'Modern Horizons 3', 'expansion'),
            ]
            
            for set_data in sample_sets:
                await db_service.execute_query(
                    "INSERT INTO sets (code, name, release_date, block, type) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (code) DO NOTHING",
                    set_data,
                    fetch_all=False
                )
            logger.info("✅ Sample sets added")
        
        logger.info("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(init_database())




