-- Add inventory changes tracking table
CREATE TABLE IF NOT EXISTS inventory_changes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    snapshot_id INTEGER REFERENCES inventory_snapshots(id) ON DELETE CASCADE,
    change_date DATE NOT NULL,
    
    -- Previous snapshot comparison
    previous_snapshot_id INTEGER REFERENCES inventory_snapshots(id),
    
    -- Overall changes
    total_items_change INTEGER DEFAULT 0,
    total_cards_change INTEGER DEFAULT 0,
    total_value_change DECIMAL(12, 2) DEFAULT 0.00,
    avg_card_value_change DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Percentage changes
    total_items_percent_change DECIMAL(5, 2) DEFAULT 0.00,
    total_cards_percent_change DECIMAL(5, 2) DEFAULT 0.00,
    total_value_percent_change DECIMAL(5, 2) DEFAULT 0.00,
    
    -- Detailed changes
    items_added INTEGER DEFAULT 0,
    items_removed INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    
    -- New cards vs existing cards
    new_cards_added INTEGER DEFAULT 0,
    existing_cards_updated INTEGER DEFAULT 0,
    
    -- Value analysis
    value_added DECIMAL(12, 2) DEFAULT 0.00,
    value_removed DECIMAL(12, 2) DEFAULT 0.00,
    
    -- Time period since last change
    days_since_last_change INTEGER DEFAULT 0,
    
    -- Metadata for additional tracking
    change_type VARCHAR(50) DEFAULT 'sync', -- 'sync', 'manual', 'bulk_add', etc.
    source_file VARCHAR(255),
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, snapshot_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_inventory_changes_user_date ON inventory_changes(user_id, change_date);
CREATE INDEX IF NOT EXISTS idx_inventory_changes_snapshot ON inventory_changes(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_inventory_changes_user_id ON inventory_changes(user_id);

-- Add updated_at column to inventory_snapshots if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='inventory_snapshots' AND column_name='updated_at') THEN
        ALTER TABLE inventory_snapshots ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add updated_at column to inventory if it doesn't exist  
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='inventory' AND column_name='updated_at') THEN
        ALTER TABLE inventory ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;
