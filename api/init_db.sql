-- Create database schema for TCG Scraper

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sets table
CREATE TABLE IF NOT EXISTS sets (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    release_date DATE,
    card_count INTEGER,
    type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cards table
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    set_id INTEGER REFERENCES sets(id),
    set_name VARCHAR(100),
    set_code VARCHAR(10),
    rarity VARCHAR(50),
    tcg_player_id VARCHAR(50),
    scryfall_id VARCHAR(50),
    game VARCHAR(50) DEFAULT 'magic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    card_id INTEGER REFERENCES cards(id),
    condition VARCHAR(20) DEFAULT 'NM',
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES cards(id),
    price DECIMAL(10, 2) NOT NULL,
    foil_price DECIMAL(10, 2),
    source VARCHAR(50) DEFAULT 'tcgplayer',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(card_id, date, source)
);

-- Price alerts table
CREATE TABLE IF NOT EXISTS price_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    card_id INTEGER REFERENCES cards(id),
    target_price DECIMAL(10, 2) NOT NULL,
    alert_type VARCHAR(20) DEFAULT 'below',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory snapshots table for tracking daily inventory summaries
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_items INTEGER NOT NULL DEFAULT 0,
    total_cards INTEGER NOT NULL DEFAULT 0,
    total_value DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    avg_card_value DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    file_name VARCHAR(255),
    file_size INTEGER,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    UNIQUE(user_id, snapshot_date)
);

-- Inventory uploads table for tracking PDF uploads
CREATE TABLE IF NOT EXISTS inventory_uploads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processed_items INTEGER DEFAULT 0,
    error_message TEXT,
    snapshot_id INTEGER REFERENCES inventory_snapshots(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_set_code ON cards(set_code);
CREATE INDEX IF NOT EXISTS idx_cards_tcg_player_id ON cards(tcg_player_id);
CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_price_history_card_id ON price_history(card_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_user_date ON inventory_snapshots(user_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_inventory_uploads_user_id ON inventory_uploads(user_id);

-- Insert default admin user (password: 'admin123' hashed with bcrypt)
INSERT INTO users (username, email, password_hash, is_admin) 
VALUES ('rmangana', 'admin@tcgscraper.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3z5.8EhCWa', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Insert some sample sets
INSERT INTO sets (code, name, release_date, card_count, type) VALUES
('dft', 'Dominaria United', '2022-09-09', 281, 'expansion'),
('dsk', 'Duskmourn: House of Horror', '2024-09-27', 276, 'expansion'),
('tdc', 'The Dark Crystal', '2023-01-01', 200, 'expansion')
ON CONFLICT (code) DO NOTHING;

-- Insert some sample cards
INSERT INTO cards (name, set_id, set_name, set_code, rarity, game) VALUES
('Lightning Bolt', 1, 'Dominaria United', 'dft', 'common', 'magic'),
('Black Lotus', 1, 'Dominaria United', 'dft', 'mythic', 'magic'),
('Pikachu', 2, 'Duskmourn: House of Horror', 'dsk', 'rare', 'pokemon')
ON CONFLICT DO NOTHING;
