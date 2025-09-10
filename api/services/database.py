import psycopg2
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._connection_params = self._get_connection_params()
    
    def _get_connection_params(self) -> Dict[str, str]:
        """Get database connection parameters from environment or defaults"""
        return {
            'dbname': os.getenv('DB_NAME', 'tcgplayerdb'),
            'user': os.getenv('DB_USER', 'rmangana'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'host': os.getenv('DB_HOST', '52.73.212.127'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def _create_connection(self, is_test: bool = False) -> connection:
        """Create a new database connection"""
        params = self._connection_params.copy()
        if is_test:
            params['dbname'] = 'tcgplayerdbtest'
        
        try:
            conn = psycopg2.connect(**params)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    @contextmanager
    def get_connection(self, is_test: bool = False):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self._create_connection(is_test)
            yield conn
            # Commit the transaction if no exceptions occurred
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
        is_test: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute a database query asynchronously"""
        def _execute():
            with self.get_connection(is_test) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        return dict(result) if result else None
                    elif fetch_all:
                        results = cursor.fetchall()
                        return [dict(row) for row in results]
                    else:
                        conn.commit()
                        return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _execute)
    
    async def execute_many(
        self,
        query: str,
        params_list: List[Tuple],
        is_test: bool = False
    ) -> None:
        """Execute a query with multiple parameter sets"""
        def _execute():
            with self.get_connection(is_test) as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    conn.commit()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _execute)
    
    # User management methods
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        query = """
            SELECT username, email, password_hash, is_admin, created_at, last_login
            FROM users 
            WHERE username = %s
        """
        return await self.execute_query(query, (username,), fetch_one=True)
    
    async def create_user(self, username: str, email: str, password_hash: str) -> Dict[str, Any]:
        """Create a new user"""
        query = """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING username, email, is_admin, created_at
        """
        return await self.execute_query(
            query, 
            (username, email, password_hash), 
            fetch_one=True
        )
    
    async def update_last_login(self, username: str) -> None:
        """Update user's last login timestamp"""
        query = "UPDATE users SET last_login = NOW() WHERE username = %s"
        await self.execute_query(query, (username,), fetch_all=False)
    
    # Inventory methods
    async def get_user_inventory(self, username: str) -> List[Dict[str, Any]]:
        """Get user's inventory"""
        query = """
            SELECT i.*, c.name, c.set_name, c.rarity, c.tcg_player_id, c.game
            FROM inventory i
            JOIN cards c ON i.card_id = c.id
            WHERE i.user_id = (SELECT id FROM users WHERE username = %s)
            ORDER BY c.name
        """
        return await self.execute_query(query, (username,))
    
    async def add_inventory_item(
        self, 
        username: str, 
        card_id: int, 
        condition: str, 
        quantity: int, 
        price: float
    ) -> Dict[str, Any]:
        """Add item to user's inventory"""
        query = """
            INSERT INTO inventory (user_id, card_id, condition, quantity, price, created_at)
            VALUES (
                (SELECT id FROM users WHERE username = %s),
                %s, %s, %s, %s, NOW()
            )
            RETURNING *
        """
        return await self.execute_query(
            query, 
            (username, card_id, condition, quantity, price), 
            fetch_one=True
        )
    
    async def add_to_inventory(
        self, 
        username: str, 
        card_id: int, 
        condition: str, 
        quantity: int, 
        price: float
    ) -> Dict[str, Any]:
        """Alias for add_inventory_item - Add item to user's inventory"""
        return await self.add_inventory_item(username, card_id, condition, quantity, price)
    
    async def bulk_add_inventory_items(
        self, 
        username: str, 
        inventory_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk add inventory items, creating cards as needed"""
        added_items = []
        errors = []
        
        for item in inventory_items:
            try:
                # Find or create card
                card = await self.find_or_create_card(
                    name=item['product_name'],
                    set_name=item['set_name'],
                    rarity=item.get('rarity', 'Unknown'),
                    tcg_player_id=item.get('tcg_player_id')
                )
                
                # Add to inventory
                inventory_item = await self.add_to_inventory(
                    username=username,
                    card_id=card['id'],
                    condition=item.get('condition', 'NM'),
                    quantity=item['quantity'],
                    price=item.get('price', 0.0)
                )
                
                added_items.append({
                    'card_name': item['product_name'],
                    'set_name': item['set_name'],
                    'quantity': item['quantity'],
                    'price': item.get('price', 0.0),
                    'inventory_id': inventory_item['id']
                })
                
            except Exception as e:
                errors.append({
                    'item': item['product_name'],
                    'error': str(e)
                })
        
        return {
            'added_items': added_items,
            'errors': errors,
            'total_added': len(added_items),
            'total_errors': len(errors)
        }
    
    async def sync_inventory_items(
        self, 
        username: str, 
        inventory_items: List[Dict[str, Any]],
        replace_all: bool = False,
        upload_id: int = None,
        progress_callback = None
    ) -> Dict[str, Any]:
        """Sync inventory items - update existing, add new ones"""
        if replace_all:
            # Clear existing inventory first
            await self.clear_user_inventory(username)
            return await self.bulk_add_inventory_items(username, inventory_items)
        
        # Smart sync - update existing, add new
        updated_items = []
        added_items = []
        errors = []
        total_items = len(inventory_items)
        logger.info(f"Starting database sync for {total_items} inventory items")
        
        for idx, item in enumerate(inventory_items, 1):
            # Update progress every 50 items or at key milestones
            if progress_callback and (idx % 50 == 0 or idx in [1, 10, total_items]):
                progress = int((idx / total_items) * 100)
                progress_callback(progress, f"Processing item {idx} of {total_items}...")
            try:
                # Debug logging for the first few items
                if idx <= 3:
                    logger.info(f"Processing item {idx}: {item}")
                    logger.info(f"Item types: product_name={type(item.get('product_name'))}, set_name={type(item.get('set_name'))}, rarity={type(item.get('rarity'))}, tcg_player_id={type(item.get('tcg_player_id'))}, game={type(item.get('game'))}")
                
                # Find or create card
                card = await self.find_or_create_card(
                    name=item['product_name'],
                    set_name=item['set_name'],
                    rarity=item.get('rarity', 'Unknown'),
                    tcg_player_id=item.get('tcg_player_id'),
                    game=item.get('game', 'magic')
                )
                
                # Check if user already has this card in inventory
                existing_inventory = await self.get_user_inventory_item(
                    username=username,
                    card_id=card['id'],
                    condition=item.get('condition', 'NM')
                )
                
                if existing_inventory:
                    # Update existing inventory item
                    updated_item = await self.update_inventory_item(
                        inventory_id=existing_inventory['id'],
                        quantity=item['quantity'],
                        price=item.get('price', 0.0)
                    )
                    updated_items.append({
                        'card_name': item['product_name'],
                        'set_name': item['set_name'],
                        'quantity': item['quantity'],
                        'price': item.get('price', 0.0),
                        'inventory_id': updated_item['id'],
                        'action': 'updated'
                    })
                else:
                    # Add new inventory item
                    inventory_item = await self.add_to_inventory(
                        username=username,
                        card_id=card['id'],
                        condition=item.get('condition', 'NM'),
                        quantity=item['quantity'],
                        price=item.get('price', 0.0)
                    )
                    added_items.append({
                        'card_name': item['product_name'],
                        'set_name': item['set_name'],
                        'quantity': item['quantity'],
                        'price': item.get('price', 0.0),
                        'inventory_id': inventory_item['id'],
                        'action': 'added'
                    })
                
            except Exception as e:
                errors.append({
                    'item': item['product_name'],
                    'error': str(e)
                })
            
            # Log progress every 50 items or at key milestones
            if idx % 50 == 0 or idx in [10, 25, total_items]:
                logger.info(f"Database sync progress: {idx}/{total_items} items ({len(added_items)} added, {len(updated_items)} updated, {len(errors)} errors)")
        
        logger.info(f"Database sync complete: {len(added_items)} added, {len(updated_items)} updated, {len(errors)} errors from {total_items} items")
        
        return {
            'updated_items': updated_items,
            'added_items': added_items,
            'errors': errors,
            'total_updated': len(updated_items),
            'total_added': len(added_items),
            'total_errors': len(errors)
        }
    
    async def get_user_inventory_item(
        self, 
        username: str, 
        card_id: int, 
        condition: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific inventory item for user"""
        query = """
            SELECT i.* FROM inventory i
            JOIN users u ON u.id = i.user_id
            WHERE u.username = %s AND i.card_id = %s AND i.condition = %s
        """
        return await self.execute_query(
            query, (username, card_id, condition), fetch_one=True
        )
    
    async def update_inventory_item(
        self, 
        inventory_id: int, 
        quantity: int, 
        price: float
    ) -> Dict[str, Any]:
        """Update existing inventory item"""
        query = """
            UPDATE inventory 
            SET quantity = %s, price = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        return await self.execute_query(
            query, (quantity, price, inventory_id), fetch_one=True
        )
    
    async def clear_user_inventory(self, username: str) -> Dict[str, Any]:
        """Clear all inventory for a user"""
        query = """
            DELETE FROM inventory 
            WHERE user_id = (SELECT id FROM users WHERE username = %s)
        """
        result = await self.execute_query(query, (username,))
        return {"success": True, "message": "Inventory cleared"}
    
    # Inventory change tracking methods
    async def create_inventory_change_record(
        self,
        username: str,
        snapshot_id: int,
        change_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a record of inventory changes"""
        # Get the previous snapshot for comparison
        previous_snapshot = await self.get_previous_inventory_snapshot(username, snapshot_id)
        
        query = """
            INSERT INTO inventory_changes (
                user_id, snapshot_id, change_date, previous_snapshot_id,
                total_items_change, total_cards_change, total_value_change, avg_card_value_change,
                total_items_percent_change, total_cards_percent_change, total_value_percent_change,
                items_added, items_removed, items_updated,
                new_cards_added, existing_cards_updated,
                value_added, value_removed, days_since_last_change,
                change_type, source_file, metadata
            ) VALUES (
                (SELECT id FROM users WHERE username = %s),
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) 
            ON CONFLICT (user_id, snapshot_id) 
            DO UPDATE SET 
                change_date = EXCLUDED.change_date,
                previous_snapshot_id = EXCLUDED.previous_snapshot_id,
                total_items_change = EXCLUDED.total_items_change,
                total_cards_change = EXCLUDED.total_cards_change,
                total_value_change = EXCLUDED.total_value_change,
                avg_card_value_change = EXCLUDED.avg_card_value_change,
                total_items_percent_change = EXCLUDED.total_items_percent_change,
                total_cards_percent_change = EXCLUDED.total_cards_percent_change,
                total_value_percent_change = EXCLUDED.total_value_percent_change,
                items_added = EXCLUDED.items_added,
                items_removed = EXCLUDED.items_removed,
                items_updated = EXCLUDED.items_updated,
                new_cards_added = EXCLUDED.new_cards_added,
                existing_cards_updated = EXCLUDED.existing_cards_updated,
                value_added = EXCLUDED.value_added,
                value_removed = EXCLUDED.value_removed,
                days_since_last_change = EXCLUDED.days_since_last_change,
                change_type = EXCLUDED.change_type,
                source_file = EXCLUDED.source_file,
                metadata = EXCLUDED.metadata,
                created_at = NOW()
            RETURNING *
        """
        
        import json
        metadata_json = json.dumps(change_data.get('metadata', {}))
        
        return await self.execute_query(
            query,
            (
                username,
                snapshot_id,
                change_data['change_date'],
                previous_snapshot['id'] if previous_snapshot else None,
                change_data.get('total_items_change', 0),
                change_data.get('total_cards_change', 0),
                change_data.get('total_value_change', 0.0),
                change_data.get('avg_card_value_change', 0.0),
                change_data.get('total_items_percent_change', 0.0),
                change_data.get('total_cards_percent_change', 0.0),
                change_data.get('total_value_percent_change', 0.0),
                change_data.get('items_added', 0),
                change_data.get('items_removed', 0),
                change_data.get('items_updated', 0),
                change_data.get('new_cards_added', 0),
                change_data.get('existing_cards_updated', 0),
                change_data.get('value_added', 0.0),
                change_data.get('value_removed', 0.0),
                change_data.get('days_since_last_change', 0),
                change_data.get('change_type', 'sync'),
                change_data.get('source_file', ''),
                metadata_json
            ),
            fetch_one=True
        )
    
    async def get_previous_inventory_snapshot(
        self,
        username: str,
        current_snapshot_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get the previous inventory snapshot for comparison"""
        query = """
            SELECT s.* FROM inventory_snapshots s
            JOIN users u ON u.id = s.user_id
            WHERE u.username = %s AND s.id < %s
            ORDER BY s.snapshot_date DESC, s.id DESC
            LIMIT 1
        """
        return await self.execute_query(
            query, (username, current_snapshot_id), fetch_one=True
        )
    
    async def get_inventory_changes(
        self,
        username: str,
        days_back: int = 30,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get inventory changes for a user within a time period"""
        query = """
            SELECT 
                ic.*,
                s.snapshot_date,
                s.total_items as current_total_items,
                s.total_cards as current_total_cards,
                s.total_value as current_total_value,
                ps.total_items as previous_total_items,
                ps.total_cards as previous_total_cards,
                ps.total_value as previous_total_value
            FROM inventory_changes ic
            JOIN users u ON u.id = ic.user_id
            JOIN inventory_snapshots s ON s.id = ic.snapshot_id
            LEFT JOIN inventory_snapshots ps ON ps.id = ic.previous_snapshot_id
            WHERE u.username = %s 
            AND ic.change_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY ic.change_date DESC, ic.created_at DESC
            LIMIT %s
        """
        return await self.execute_query(query, (username, days_back, limit))
    
    async def get_inventory_growth_stats(
        self,
        username: str,
        period: str = 'month'  # 'week', 'month', 'year'
    ) -> Dict[str, Any]:
        """Get inventory growth statistics for different time periods"""
        period_map = {
            'week': 7,
            'month': 30,
            'year': 365
        }
        days = period_map.get(period, 30)
        
        # Get changes in the specified period
        changes = await self.get_inventory_changes(username, days_back=days)
        
        if not changes:
            return {
                'period': period,
                'total_changes': 0,
                'items_growth': 0,
                'cards_growth': 0,
                'value_growth': 0.0,
                'avg_items_change': 0,
                'avg_cards_change': 0,
                'avg_value_change': 0.0
            }
        
        # Calculate aggregated statistics
        total_items_change = sum(c.get('total_items_change', 0) for c in changes)
        total_cards_change = sum(c.get('total_cards_change', 0) for c in changes)
        total_value_change = sum(float(c.get('total_value_change', 0)) for c in changes)
        
        return {
            'period': period,
            'total_changes': len(changes),
            'items_growth': total_items_change,
            'cards_growth': total_cards_change,
            'value_growth': total_value_change,
            'avg_items_change': total_items_change / len(changes) if changes else 0,
            'avg_cards_change': total_cards_change / len(changes) if changes else 0,
            'avg_value_change': total_value_change / len(changes) if changes else 0.0,
            'changes': changes[:10]  # Include recent changes for details
        }
    
    # Card methods
    async def search_cards(
        self, 
        search_term: Optional[str] = None,
        set_name: Optional[str] = None,
        rarity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for cards with filters"""
        conditions = []
        params = []
        
        if search_term:
            conditions.append("name ILIKE %s")
            params.append(f"%{search_term}%")
        
        if set_name:
            conditions.append("set_name = %s")
            params.append(set_name)
        
        if rarity:
            conditions.append("rarity = %s")
            params.append(rarity)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        
        query = f"""
            SELECT * FROM cards 
            {where_clause}
            ORDER BY name
            LIMIT %s
        """
        
        return await self.execute_query(query, tuple(params))
    
    async def get_card_by_tcg_id(self, tcg_player_id: str) -> Optional[Dict[str, Any]]:
        """Get card by TCGPlayer ID"""
        query = "SELECT * FROM cards WHERE tcg_player_id = %s"
        return await self.execute_query(query, (tcg_player_id,), fetch_one=True)
    
    async def find_or_create_card(
        self, 
        name: str, 
        set_name: str, 
        rarity: str = 'Unknown',
        tcg_player_id: Optional[str] = None,
        game: str = 'magic'
    ) -> Dict[str, Any]:
        """Find existing card or create new one"""
        # First try to find existing card by name and set
        query = """
            SELECT * FROM cards 
            WHERE LOWER(name) = LOWER(%s) AND LOWER(set_name) = LOWER(%s)
        """
        existing_card = await self.execute_query(
            query, (name, set_name), fetch_one=True
        )
        
        if existing_card:
            return existing_card
        
        # If not found, create new card
        insert_query = """
            INSERT INTO cards (name, set_name, rarity, tcg_player_id, game, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING *
        """
        return await self.execute_query(
            insert_query, 
            (name, set_name, rarity, tcg_player_id, game), 
            fetch_one=True
        )
    
    # Price tracking methods
    async def get_card_price_history(
        self, 
        card_id: int, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get price history for a card"""
        query = """
            SELECT * FROM price_history 
            WHERE card_id = %s 
            AND date >= NOW() - INTERVAL '%s days'
            ORDER BY date DESC
        """
        return await self.execute_query(query, (card_id, days))
    
    async def add_price_data(
        self, 
        card_id: int, 
        price: float, 
        foil_price: Optional[float] = None,
        source: str = 'tcgplayer'
    ) -> None:
        """Add price data for a card"""
        query = """
            INSERT INTO price_history (card_id, price, foil_price, source, date)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (card_id, date, source) 
            DO UPDATE SET price = EXCLUDED.price, foil_price = EXCLUDED.foil_price
        """
        await self.execute_query(
            query, 
            (card_id, price, foil_price, source), 
            fetch_all=False
        )
    
    # Set methods
    async def get_sets(self) -> List[Dict[str, Any]]:
        """Get all sets"""
        query = "SELECT * FROM sets ORDER BY release_date DESC"
        return await self.execute_query(query)
    
    async def get_set_by_code(self, set_code: str) -> Optional[Dict[str, Any]]:
        """Get set by code"""
        query = "SELECT * FROM sets WHERE code = %s"
        return await self.execute_query(query, (set_code,), fetch_one=True)
    
    # Statistics methods
    async def get_inventory_stats(self, username: str) -> Dict[str, Any]:
        """Get inventory statistics for a user"""
        query = """
            SELECT 
                COUNT(*) as total_items,
                SUM(quantity) as total_cards,
                SUM(quantity * price) as total_value,
                AVG(price) as avg_price
            FROM inventory i
            WHERE i.user_id = (SELECT id FROM users WHERE username = %s)
        """
        result = await self.execute_query(query, (username,), fetch_one=True)
        return result or {}
    
    # Inventory snapshot methods
    async def create_inventory_snapshot(
        self, 
        username: str, 
        snapshot_date: str,
        total_items: int,
        total_cards: int,
        total_value: float,
        avg_card_value: float,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an inventory snapshot"""
        query = """
            INSERT INTO inventory_snapshots 
            (user_id, snapshot_date, total_items, total_cards, total_value, avg_card_value, 
             file_name, file_size, metadata)
            VALUES (
                (SELECT id FROM users WHERE username = %s),
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_id, snapshot_date) 
            DO UPDATE SET 
                total_items = EXCLUDED.total_items,
                total_cards = EXCLUDED.total_cards,
                total_value = EXCLUDED.total_value,
                avg_card_value = EXCLUDED.avg_card_value,
                file_name = EXCLUDED.file_name,
                file_size = EXCLUDED.file_size,
                metadata = EXCLUDED.metadata,
                upload_timestamp = NOW()
            RETURNING *
        """
        import json
        metadata_json = json.dumps(metadata) if metadata else None
        return await self.execute_query(
            query, 
            (username, snapshot_date, total_items, total_cards, total_value, 
             avg_card_value, file_name, file_size, metadata_json), 
            fetch_one=True
        )
    
    async def get_inventory_snapshots(
        self, 
        username: str, 
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get inventory snapshots for a user"""
        query = """
            SELECT * FROM inventory_snapshots
            WHERE user_id = (SELECT id FROM users WHERE username = %s)
            ORDER BY snapshot_date DESC
            LIMIT %s
        """
        return await self.execute_query(query, (username, limit))
    
    async def create_inventory_upload(
        self,
        username: str,
        file_name: str,
        file_size: int,
        file_type: str
    ) -> Dict[str, Any]:
        """Create an inventory upload record"""
        query = """
            INSERT INTO inventory_uploads (user_id, file_name, file_size, file_type)
            VALUES (
                (SELECT id FROM users WHERE username = %s),
                %s, %s, %s
            )
            RETURNING *
        """
        return await self.execute_query(
            query, 
            (username, file_name, file_size, file_type), 
            fetch_one=True
        )
    
    async def update_inventory_upload_status(
        self,
        upload_id: int,
        status: str,
        processed_items: Optional[int] = None,
        error_message: Optional[str] = None,
        snapshot_id: Optional[int] = None
    ) -> None:
        """Update inventory upload processing status"""
        query = """
            UPDATE inventory_uploads 
            SET processing_status = %s,
                processed_items = COALESCE(%s, processed_items),
                error_message = %s,
                snapshot_id = COALESCE(%s, snapshot_id)
            WHERE id = %s
        """
        await self.execute_query(
            query, 
            (status, processed_items, error_message, snapshot_id, upload_id), 
            fetch_all=False
        )
    
    # Cleanup methods
    async def cleanup_old_data(self, days: int = 90) -> None:
        """Clean up old data"""
        query = """
            DELETE FROM price_history 
            WHERE date < NOW() - INTERVAL '%s days'
        """
        await self.execute_query(query, (days,), fetch_all=False)
    
    async def close(self):
        """Close the executor"""
        self.executor.shutdown(wait=True)
