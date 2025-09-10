import logging
import re
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from .database import DatabaseService
import PyPDF2
import pandas as pd
import asyncio

logger = logging.getLogger(__name__)

# In-memory progress tracking
upload_progress = {}

class InventoryService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def _update_progress(self, upload_id: int, progress: int, status: str):
        """Update upload progress"""
        upload_progress[upload_id] = {
            'progress': progress,
            'status': status,
            'timestamp': datetime.now()
        }
    
    def _get_progress(self, upload_id: int) -> Dict[str, Any]:
        """Get upload progress"""
        return upload_progress.get(upload_id, {
            'progress': 0,
            'status': 'Starting...',
            'timestamp': datetime.now()
        })
    
    def _clear_progress(self, upload_id: int):
        """Clear upload progress"""
        if upload_id in upload_progress:
            del upload_progress[upload_id]
    
    async def get_user_inventory(self, username: str) -> Dict[str, Any]:
        """Get user's complete inventory"""
        try:
            inventory_items = await self.db_service.get_user_inventory(username)
            stats = await self.db_service.get_inventory_stats(username)
            
            return {
                "success": True,
                "inventory": [
                    {
                        "id": item['id'],
                        "product_name": item['name'],
                        "set_name": item['set_name'],
                        "rarity": item['rarity'],
                        "condition": item['condition'],
                        "quantity": item['quantity'],
                        "price": float(item['price']) if item['price'] is not None else 0.0,
                        "tcg_player_id": item.get('tcg_player_id'),
                        "game": item.get('game', 'magic')  # Default to 'magic' if not specified
                    }
                    for item in inventory_items
                ],
                "total_items": stats.get("total_items", 0),
                "total_value": float(stats.get("total_value", 0)) if stats.get("total_value") is not None else 0.0
            }
        
        except Exception as e:
            logger.error(f"Inventory retrieval error: {e}")
            return {
                "success": False,
                "inventory": [],
                "total_items": 0,
                "total_value": 0.0
            }
    
    async def get_inventory_snapshots(self, username: str) -> Dict[str, Any]:
        """Get user's inventory snapshots"""
        try:
            snapshots = await self.db_service.get_inventory_snapshots(username)
            
            return {
                "success": True,
                "snapshots": [
                    {
                        "id": snapshot['id'],
                        "snapshot_date": snapshot['snapshot_date'].strftime('%Y-%m-%d'),
                        "total_items": snapshot['total_items'],
                        "total_cards": snapshot['total_cards'],
                        "total_value": float(snapshot['total_value']) if snapshot['total_value'] is not None else 0.0,
                        "avg_card_value": float(snapshot['avg_card_value']) if snapshot['avg_card_value'] is not None else 0.0,
                        "file_name": snapshot.get('file_name'),
                        "file_size": snapshot.get('file_size'),
                        "upload_timestamp": snapshot.get('upload_timestamp'),
                        "metadata": snapshot.get('metadata')
                    }
                    for snapshot in snapshots
                ],
                "total_snapshots": len(snapshots)
            }
        
        except Exception as e:
            logger.error(f"Snapshots retrieval error: {e}")
            return {
                "success": False,
                "snapshots": [],
                "total_snapshots": 0
            }
    
    async def upload_inventory_pdf(
        self, 
        username: str, 
        file_content: bytes, 
        filename: str
    ) -> Dict[str, Any]:
        """Upload and process inventory PDF"""
        try:
            # Create upload record
            upload_record = await self.db_service.create_inventory_upload(
                username=username,
                file_name=filename,
                file_size=len(file_content),
                file_type="application/pdf"
            )
            
            upload_id = upload_record['id']
            
            try:
                # Process PDF
                processed_data = await self._process_inventory_pdf(file_content)
                
                if not processed_data['success']:
                    await self.db_service.update_inventory_upload_status(
                        upload_id, 
                        "failed", 
                        error_message=processed_data.get('error', 'PDF processing failed')
                    )
                    return processed_data
                
                # Create inventory snapshot
                today = date.today().strftime('%Y-%m-%d')
                
                snapshot = await self.db_service.create_inventory_snapshot(
                    username=username,
                    snapshot_date=today,
                    total_items=processed_data['total_items'],
                    total_cards=processed_data['total_cards'],
                    total_value=processed_data['total_value'],
                    avg_card_value=processed_data['avg_card_value'],
                    file_name=filename,
                    file_size=len(file_content),
                    metadata=processed_data.get('metadata', {})
                )
                
                # Update upload status
                await self.db_service.update_inventory_upload_status(
                    upload_id,
                    "completed",
                    processed_items=processed_data['total_items'],
                    snapshot_id=snapshot['id']
                )
                
                return {
                    "success": True,
                    "message": f"Successfully processed {processed_data['total_items']} items from PDF",
                    "upload_id": upload_id,
                    "snapshot_id": snapshot['id'],
                    "processed_items": processed_data['total_items']
                }
            
            except Exception as processing_error:
                await self.db_service.update_inventory_upload_status(
                    upload_id, 
                    "failed", 
                    error_message=str(processing_error)
                )
                raise processing_error
        
        except Exception as e:
            logger.error(f"PDF upload error: {e}")
            return {
                "success": False,
                "message": f"Failed to process PDF: {str(e)}",
                "upload_id": None,
                "processed_items": 0
            }
    
    async def upload_inventory_csv(
        self, 
        username: str, 
        file_content: bytes, 
        filename: str,
        replace_all: bool = False
    ) -> Dict[str, Any]:
        """Upload and process inventory CSV"""
        try:
            # Create upload record
            upload_record = await self.db_service.create_inventory_upload(
                username=username,
                file_name=filename,
                file_size=len(file_content),
                file_type="text/csv"
            )
            
            upload_id = upload_record['id']
            self._update_progress(upload_id, 5, "Starting upload...")
            
            try:
                # Process CSV
                self._update_progress(upload_id, 15, "Reading CSV file...")
                processed_data = await self._process_inventory_csv(file_content, upload_id)
                
                if not processed_data['success']:
                    await self.db_service.update_inventory_upload_status(
                        upload_id, 
                        "failed", 
                        error_message=processed_data.get('error', 'CSV processing failed')
                    )
                    return processed_data
                
                # Save inventory items to database using sync method
                self._update_progress(upload_id, 70, "Saving to database...")
                sync_result = await self.db_service.sync_inventory_items(
                    username=username,
                    inventory_items=processed_data['inventory_data'],
                    replace_all=replace_all,
                    upload_id=upload_id,
                    progress_callback=lambda progress, status: self._update_progress(upload_id, 70 + int(progress * 0.2), status)
                )
                
                # Create inventory snapshot
                today = date.today().strftime('%Y-%m-%d')
                
                snapshot = await self.db_service.create_inventory_snapshot(
                    username=username,
                    snapshot_date=today,
                    total_items=processed_data['total_items'],
                    total_cards=processed_data['total_cards'],
                    total_value=processed_data['total_value'],
                    avg_card_value=processed_data['avg_card_value'],
                    metadata={
                        **processed_data.get('metadata', {}),
                        'sync_result': {
                            'items_added': sync_result.get('total_added', 0),
                            'items_updated': sync_result.get('total_updated', 0),
                            'errors': sync_result.get('total_errors', 0),
                            'replace_all': replace_all
                        }
                    }
                )
                
                # Create inventory change record for tracking
                change_record = await self._create_inventory_change_record(
                    username=username,
                    snapshot_id=snapshot['id'],
                    sync_result=sync_result,
                    filename=filename,
                    replace_all=replace_all,
                    current_totals={
                        'total_items': processed_data['total_items'],
                        'total_cards': processed_data['total_cards'],
                        'total_value': processed_data['total_value'],
                        'avg_card_value': processed_data['avg_card_value']
                    }
                )
                
                # Update upload status
                await self.db_service.update_inventory_upload_status(
                    upload_id,
                    "completed",
                    processed_items=processed_data['total_items'],
                    snapshot_id=snapshot['id']
                )
                
                # Build success message
                message_parts = []
                if sync_result.get('total_added', 0) > 0:
                    message_parts.append(f"{sync_result['total_added']} items added")
                if sync_result.get('total_updated', 0) > 0:
                    message_parts.append(f"{sync_result['total_updated']} items updated")
                if sync_result.get('total_errors', 0) > 0:
                    message_parts.append(f"{sync_result['total_errors']} errors")
                
                message = "Successfully processed: " + ", ".join(message_parts) if message_parts else "No changes made"
                
                return {
                    "success": True,
                    "message": message,
                    "upload_id": upload_id,
                    "snapshot_id": snapshot['id'],
                    "total_items": processed_data['total_items'],
                    "total_cards": processed_data['total_cards'],
                    "total_value": processed_data['total_value'],
                    "items_added": sync_result.get('total_added', 0),
                    "items_updated": sync_result.get('total_updated', 0),
                    "errors": sync_result.get('errors', []),
                    "replace_all": replace_all
                }
                
            except Exception as processing_error:
                await self.db_service.update_inventory_upload_status(
                    upload_id, 
                    "failed", 
                    error_message=str(processing_error)
                )
                logger.error(f"CSV processing error: {processing_error}")
                return {
                    "success": False,
                    "message": f"Failed to process CSV: {str(processing_error)}",
                    "upload_id": upload_id,
                    "processed_items": 0
                }
                
        except Exception as e:
            logger.error(f"CSV upload error: {e}")
            return {
                "success": False,
                "message": f"Failed to upload CSV: {str(e)}",
                "upload_id": None,
                "processed_items": 0
            }
    
    async def _process_inventory_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Process PDF content and extract inventory data"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            # Extract text from all pages
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            # Parse inventory data from text
            inventory_data = self._parse_inventory_text(text_content)
            
            if not inventory_data:
                return {
                    "success": False,
                    "error": "No inventory data found in PDF"
                }
            
            # Calculate statistics
            total_items = len(inventory_data)
            total_cards = sum(item.get('quantity', 1) for item in inventory_data)
            total_value = sum(item.get('quantity', 1) * item.get('price', 0) for item in inventory_data)
            avg_card_value = total_value / max(total_cards, 1)
            
            return {
                "success": True,
                "total_items": total_items,
                "total_cards": total_cards,
                "total_value": total_value,
                "avg_card_value": avg_card_value,
                "inventory_data": inventory_data,
                "metadata": {
                    "pages_processed": len(pdf_reader.pages),
                    "text_length": len(text_content)
                }
            }
        
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}"
            }
    
    def _parse_inventory_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse inventory data from extracted PDF text"""
        inventory_items = []
        
        # Common patterns for inventory data
        # This is a basic implementation - you may need to customize based on your PDF format
        
        # Pattern for lines like: "Card Name | Set | Quantity | Price"
        line_pattern = re.compile(
            r'([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*\$?(\d+\.?\d*)',
            re.IGNORECASE
        )
        
        # Pattern for table-like data
        table_pattern = re.compile(
            r'(\w+(?:\s+\w+)*)\s+(\w+(?:\s+\w+)*)\s+(\d+)\s+\$?(\d+\.?\d*)',
            re.IGNORECASE
        )
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try pipe-separated format
            match = line_pattern.search(line)
            if match:
                card_name, set_name, quantity, price = match.groups()
                inventory_items.append({
                    'product_name': card_name.strip(),
                    'set_name': set_name.strip(),
                    'quantity': int(quantity),
                    'price': float(price),
                    'condition': 'NM',  # Default condition
                    'rarity': 'Unknown'  # Default rarity
                })
                continue
            
            # Try space-separated format
            match = table_pattern.search(line)
            if match:
                card_name, set_name, quantity, price = match.groups()
                inventory_items.append({
                    'product_name': card_name.strip(),
                    'set_name': set_name.strip(),
                    'quantity': int(quantity),
                    'price': float(price),
                    'condition': 'NM',
                    'rarity': 'Unknown'
                })
        
        return inventory_items
    
    async def _process_inventory_csv(self, csv_content: bytes, upload_id: int = None) -> Dict[str, Any]:
        """Process CSV content and extract inventory data"""
        try:
            # Decode CSV content
            if upload_id:
                self._update_progress(upload_id, 20, "Decoding CSV content...")
            csv_text = csv_content.decode('utf-8')
            
            # Read CSV into pandas DataFrame
            if upload_id:
                self._update_progress(upload_id, 25, "Reading CSV data...")
            df = pd.read_csv(io.StringIO(csv_text))
            
            # Keep original column names but create a mapping for TCGPlayer format
            # Clean column names (remove extra spaces but keep original case)
            df.columns = df.columns.str.strip()
            
            # TCGPlayer CSV standard columns (exact match)
            tcgplayer_columns = {
                'product_name': 'Product Name',
                'set_name': 'Set Name', 
                'quantity': 'Total Quantity',
                'price': 'TCG Marketplace Price',
                'condition': 'Condition',
                'rarity': 'Rarity',
                'tcg_player_id': 'TCGplayer Id'
            }
            
            # Find actual column names in the DataFrame (case-insensitive)
            actual_columns = {}
            df_columns_lower = [col.lower() for col in df.columns]
            
            for standard_name, tcg_column in tcgplayer_columns.items():
                # First try exact TCGPlayer column name
                if tcg_column in df.columns:
                    actual_columns[standard_name] = tcg_column
                # Then try case-insensitive match
                elif tcg_column.lower() in df_columns_lower:
                    idx = df_columns_lower.index(tcg_column.lower())
                    actual_columns[standard_name] = df.columns[idx]
                # Fallback to common variations
                else:
                    variations = {
                        'product_name': ['product name', 'card name', 'name', 'card', 'title'],
                        'set_name': ['set name', 'set', 'expansion', 'product line'],
                        'quantity': ['quantity', 'qty', 'count', 'total quantity', 'add to quantity'],
                        'price': ['price', 'unit price', 'tcg market price', 'market price', 'value', 'tcg low price'],
                        'condition': ['condition', 'cond'],
                        'rarity': ['rarity', 'rare'],
                        'tcg_player_id': ['tcgplayer id', 'id', 'tcg player id']
                    }
                    
                    for variation in variations.get(standard_name, []):
                        if variation in df_columns_lower:
                            idx = df_columns_lower.index(variation)
                            actual_columns[standard_name] = df.columns[idx]
                            break
            
            # Debug logging
            logger.info(f"CSV columns found: {list(df.columns)}")
            logger.info(f"Column mapping result: {actual_columns}")
            
            # Validate required columns
            required_columns = ['product_name', 'quantity']
            missing_columns = []
            for col in required_columns:
                if col not in actual_columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return {
                    "success": False,
                    "message": f"Missing required columns: {', '.join(missing_columns)}. Available columns: {', '.join(df.columns)}. Mapped columns: {actual_columns}",
                    "processed_items": 0
                }
            
            # Process inventory data
            if upload_id:
                self._update_progress(upload_id, 30, "Processing inventory data...")
            inventory_data = []
            total_rows = len(df)
            logger.info(f"Starting to process {total_rows} rows from CSV")
            
            for idx, (_, row) in enumerate(df.iterrows(), 1):
                try:
                    # Skip empty rows - safer approach
                    product_name = row.get(actual_columns.get('product_name')) if 'product_name' in actual_columns else None
                    if pd.isna(product_name) or str(product_name).strip() == '':
                        continue
                    
                    # Convert to native Python string
                    product_name = str(product_name).strip()
                    
                    # Get quantity safely
                    quantity_raw = row.get(actual_columns.get('quantity')) if 'quantity' in actual_columns else None
                    if pd.isna(quantity_raw):
                        continue
                    
                    try:
                        quantity = int(float(str(quantity_raw)))  # Handle decimal quantities
                        if quantity <= 0:
                            continue
                    except (ValueError, TypeError):
                        continue
                    
                    # Extract data with safe defaults - ensure all values are native Python types
                    item = {
                        'product_name': product_name,  # Already converted to string above
                        'quantity': int(quantity),     # Ensure it's a native Python int
                        'set_name': 'Unknown',
                        'price': 0.0,
                        'condition': 'NM',
                        'rarity': 'Unknown',
                        'tcg_player_id': None
                    }
                    
                    # Safely extract optional fields - convert all to native Python types
                    if 'set_name' in actual_columns:
                        set_val = row.get(actual_columns['set_name'])
                        if pd.notna(set_val):
                            item['set_name'] = str(set_val).strip()
                    
                    if 'price' in actual_columns:
                        price_val = row.get(actual_columns['price'])
                        if pd.notna(price_val):
                            try:
                                # Remove $ and convert to native Python float
                                price_str = str(price_val).replace('$', '').replace(',', '').strip()
                                if price_str:
                                    item['price'] = float(price_str)
                            except (ValueError, TypeError):
                                pass
                    
                    if 'condition' in actual_columns:
                        cond_val = row.get(actual_columns['condition'])
                        if pd.notna(cond_val):
                            item['condition'] = str(cond_val).strip()
                    
                    if 'rarity' in actual_columns:
                        rarity_val = row.get(actual_columns['rarity'])
                        if pd.notna(rarity_val):
                            item['rarity'] = str(rarity_val).strip()
                    
                    if 'tcg_player_id' in actual_columns:
                        tcg_val = row.get(actual_columns['tcg_player_id'])
                        if pd.notna(tcg_val) and str(tcg_val).strip():
                            # Convert to string, handle potential numeric TCG IDs
                            tcg_id_str = str(int(float(tcg_val))) if str(tcg_val).replace('.', '').isdigit() else str(tcg_val)
                            item['tcg_player_id'] = tcg_id_str.strip()
                    
                    # Determine game type based on product name and set name
                    item['game'] = self._detect_game_type(item['product_name'], item.get('set_name', ''))
                    
                    inventory_data.append(item)
                    
                    # Log progress every 100 items or at key milestones
                    if idx % 100 == 0 or idx in [10, 50, total_rows]:
                        logger.info(f"Processed {idx}/{total_rows} rows ({len(inventory_data)} valid items so far)")
                        # Update progress for large files
                        if upload_id and total_rows > 100:
                            progress = 30 + int((idx / total_rows) * 40)  # 30-70% range
                            self._update_progress(upload_id, progress, f"Processing row {idx} of {total_rows}...")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid row {idx}: {e}")
                    continue
            
            logger.info(f"CSV processing complete: {len(inventory_data)} valid items from {total_rows} rows")
            
            if not inventory_data:
                return {
                    "success": False,
                    "message": f"No valid inventory data found in CSV. Processed {total_rows} rows but found no valid items.",
                    "processed_items": 0
                }
            
            # Calculate statistics
            total_items = len(inventory_data)
            total_cards = sum(item.get('quantity', 1) for item in inventory_data)
            total_value = sum(item.get('quantity', 1) * item.get('price', 0) for item in inventory_data)
            avg_card_value = total_value / max(total_cards, 1)
            
            return {
                "success": True,
                "total_items": total_items,
                "total_cards": total_cards,
                "total_value": total_value,
                "avg_card_value": avg_card_value,
                "inventory_data": inventory_data,
                "metadata": {
                    "rows_processed": len(df),
                    "valid_items": total_items,
                    "columns_found": list(actual_columns.keys()),
                    "original_columns": list(df.columns)
                }
            }
        
        except pd.errors.EmptyDataError:
            return {
                "success": False,
                "message": "CSV file is empty",
                "processed_items": 0
            }
        except pd.errors.ParserError as e:
            return {
                "success": False,
                "message": f"CSV parsing error: {str(e)}",
                "processed_items": 0
            }
        except Exception as e:
            logger.error(f"CSV processing error: {e}")
            return {
                "success": False,
                "message": f"CSV processing failed: {str(e)}",
                "processed_items": 0
            }
    
    def _detect_game_type(self, product_name: str, set_name: str) -> str:
        """Detect TCG game type based on product name and set name"""
        product_lower = product_name.lower()
        set_lower = set_name.lower()
        
        # Pokemon detection
        pokemon_keywords = [
            'pikachu', 'charizard', 'blastoise', 'venusaur', 'pokemon', 'pokémon',
            'ash', 'team rocket', 'gym leader', 'elite four', 'champion',
            'bulbasaur', 'squirtle', 'charmander', 'mew', 'mewtwo', 'lugia',
            'ho-oh', 'rayquaza', 'groudon', 'kyogre', 'arceus', 'dialga',
            'palkia', 'giratina', 'reshiram', 'zekrom', 'kyurem'
        ]
        
        pokemon_sets = [
            'base set', 'jungle', 'fossil', 'team rocket', 'gym heroes',
            'gym challenge', 'neo genesis', 'neo discovery', 'neo revelation',
            'neo destiny', 'expedition', 'aquapolis', 'skyridge', 'ex ruby',
            'ex sapphire', 'ex sandstorm', 'ex dragon', 'ex team magma',
            'ex hidden legends', 'ex fire red', 'ex leaf green', 'ex emerald',
            'ex unseen forces', 'ex delta species', 'ex legend maker',
            'ex holon phantoms', 'ex crystal guardians', 'ex dragon frontiers',
            'ex power keepers', 'diamond & pearl', 'mysterious treasures',
            'secret wonders', 'great encounters', 'majestic dawn',
            'legends awakened', 'stormfront', 'platinum', 'rising rivals',
            'supreme victors', 'arceus', 'heartgold soulsilver', 'unleashed',
            'und\'aunted', 'triumphant', 'call of legends', 'black & white',
            'emerging powers', 'noble victories', 'next destinies',
            'dark explorers', 'dragons exalted', 'boundaries crossed',
            'plasma storm', 'plasma freeze', 'plasma blast', 'legendary treasures',
            'xy', 'flashfire', 'furious fists', 'phantom forces',
            'primal clash', 'roaring skies', 'ancient origins', 'breakthrough',
            'breakpoint', 'fates collide', 'steam siege', 'evolutions',
            'sun & moon', 'guardians rising', 'burning shadows',
            'crimson invasion', 'ultra prism', 'forbidden light',
            'celestial storm', 'lost thunder', 'team up', 'detective pikachu',
            'unbroken bonds', 'unified minds', 'hidden fates', 'cosmic eclipse',
            'sword & shield', 'rebel clash', 'darkness ablaze', 'vivid voltage',
            'battle styles', 'chilling reign', 'evolving skies', 'fusion strike',
            'brilliant stars', 'astral radiance', 'lost origin', 'silver tempest',
            'crown zenith', 'scarlet & violet', 'paldea evolved', 'obsidian flames',
            '151', 'paradox rift', 'paldean fates', 'temporal forces',
            'twilight masquerade', 'shrouded fable', 'ancient roar',
            'future flash', 'shrouded fable', 'ancient roar', 'future flash'
        ]
        
        # Magic: The Gathering detection
        magic_keywords = [
            'planeswalker', 'mana', 'creature', 'instant', 'sorcery',
            'enchantment', 'artifact', 'land', 'tribal', 'legendary',
            'jace', 'chandra', 'liliana', 'garruk', 'ajani', 'teferi',
            'karn', 'urza', 'yawgmoth', 'bolas', 'niv-mizzet',
            'gideon', 'nissa', 'sorin', 'kiora', 'ashiok', 'tamiyo'
        ]
        
        magic_sets = [
            'alpha', 'beta', 'unlimited', 'revised', 'fourth edition',
            'fifth edition', 'sixth edition', 'seventh edition', 'eighth edition',
            'ninth edition', 'tenth edition', 'core set', 'masters',
            'arabian nights', 'antiquities', 'legends', 'the dark',
            'fallen empires', 'homelands', 'ice age', 'alliances',
            'mirage', 'visions', 'weatherlight', 'tempest', 'stronghold',
            'exodus', 'urza\'s saga', 'urza\'s legacy', 'urza\'s destiny',
            'mercadian masques', 'nemesis', 'prophecy', 'invasion',
            'planeshift', 'apocalypse', 'odyssey', 'torment', 'judgment',
            'onslaught', 'legions', 'scourge', 'mirrodin', 'darksteel',
            'fifth dawn', 'champions of kamigawa', 'betrayers of kamigawa',
            'saviors of kamigawa', 'ravnica', 'guildpact', 'dissension',
            'time spiral', 'planar chaos', 'future sight', 'lorwyn',
            'morningtide', 'shadowmoor', 'eventide', 'shards of alara',
            'conflux', 'alara reborn', 'zendikar', 'worldwake',
            'rise of the eldrazi', 'scars of mirrodin', 'mirrodin besieged',
            'new phyrexia', 'innistrad', 'dark ascension', 'avacyn restored',
            'return to ravnica', 'gatecrash', 'dragon\'s maze',
            'theros', 'born of the gods', 'journey into nyx',
            'khans of tarkir', 'fate reforged', 'dragons of tarkir',
            'battle for zendikar', 'oath of the gatewatch', 'shadows over innistrad',
            'eldritch moon', 'kaladesh', 'aether revolt', 'amonkhet',
            'hour of devastation', 'ixalan', 'rivals of ixalan',
            'dominaria', 'core set 2019', 'guilds of ravnica',
            'ravnica allegiance', 'war of the spark', 'core set 2020',
            'throne of eldraine', 'theros beyond death', 'ikoria',
            'core set 2021', 'zendikar rising', 'kaldheim',
            'strixhaven', 'adventures in the forgotten realms',
            'innistrad: midnight hunt', 'innistrad: crimson vow',
            'kamigawa neon dynasty', 'streets of new capenna',
            'dungeons & dragons: adventures in the forgotten realms',
            'dominaria united', 'the brothers\' war', 'phyrexia: all will be one',
            'march of the machine', 'wilds of eldraine', 'the lost caverns of ixalan',
            'murders at karlov manor', 'outlaws of thunder junction',
            'bloomburrow', 'duskmourn: house of horror'
        ]
        
        # Yu-Gi-Oh! detection
        yugioh_keywords = [
            'yugioh', 'yu-gi-oh', 'duel', 'monster', 'spell', 'trap',
            'blue-eyes', 'dark magician', 'red-eyes', 'exodia', 'kuriboh',
            'kaiba', 'yugi', 'joey', 'mako', 'pegasus', 'marik',
            'bakura', 'mokuba', 'ishizu', 'odion', 'marcus', 'alexis',
            'chazz', 'bastion', 'tyler', 'syrus', 'zane', 'atticus',
            'blair', 'jaden', 'chumley', 'vellian', 'crowler', 'bonaparte',
            'sartorius', 'camula', 'titan', 'don zaloog', 'nightshroud',
            'yubel', 'jesse', 'axel', 'jim', 'adrian', 'trueman',
            'yusei', 'jack', 'crow', 'akiza', 'leo', 'luna', 'kalin',
            'carly', 'mikage', 'sherry', 'bruno', 'halldor', 'jean',
            'primo', 'placido', 'lucciano', 'jose', 'australis', 'z-one',
            'yuma', 'kotori', 'bronk', 'caswell', 'cathy', 'tori',
            'shark', 'kite', 'quattro', 'tron', 'nelson', 'alito',
            'gilag', 'mizar', 'vector', 'don thousand', 'nash',
            'yuto', 'yugo', 'yuri', 'reiji', 'sawatari', 'gong',
            'dennis', 'serena', 'obelisk force', 'academia', 'fusion',
            'synchro', 'xyz', 'pendulum', 'link', 'ritual', 'tribute',
            'summon', 'special summon', 'normal summon', 'flip summon',
            'tribute summon', 'fusion summon', 'synchro summon',
            'xyz summon', 'pendulum summon', 'link summon'
        ]
        
        # Check for Pokemon
        for keyword in pokemon_keywords:
            if keyword in product_lower:
                return 'pokemon'
        
        for set_name_check in pokemon_sets:
            if set_name_check in set_lower:
                return 'pokemon'
        
        # Check for Yu-Gi-Oh!
        for keyword in yugioh_keywords:
            if keyword in product_lower:
                return 'yugioh'
        
        # Check for Magic: The Gathering
        for keyword in magic_keywords:
            if keyword in product_lower:
                return 'magic'
        
        for set_name_check in magic_sets:
            if set_name_check in set_lower:
                return 'magic'
        
        # Default to Magic: The Gathering if no specific game detected
        return 'magic'
    
    async def _create_inventory_change_record(
        self,
        username: str,
        snapshot_id: int,
        sync_result: Dict[str, Any],
        filename: str,
        replace_all: bool,
        current_totals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a detailed inventory change record"""
        
        # Get previous snapshot for comparison
        previous_snapshot = await self.db_service.get_previous_inventory_snapshot(username, snapshot_id)
        
        if not previous_snapshot:
            # First inventory upload - everything is new
            change_data = {
                'change_date': date.today().strftime('%Y-%m-%d'),
                'total_items_change': current_totals['total_items'],
                'total_cards_change': current_totals['total_cards'],
                'total_value_change': current_totals['total_value'],
                'avg_card_value_change': current_totals['avg_card_value'],
                'total_items_percent_change': 100.0,
                'total_cards_percent_change': 100.0,
                'total_value_percent_change': 100.0,
                'items_added': sync_result.get('total_added', 0),
                'items_removed': 0,
                'items_updated': sync_result.get('total_updated', 0),
                'new_cards_added': sync_result.get('total_added', 0),
                'existing_cards_updated': sync_result.get('total_updated', 0),
                'value_added': current_totals['total_value'],
                'value_removed': 0.0,
                'days_since_last_change': 0,
                'change_type': 'initial_upload' if not replace_all else 'replace_all',
                'source_file': filename,
                'metadata': {
                    'sync_result': sync_result,
                    'replace_all': replace_all,
                    'first_upload': True
                }
            }
        else:
            # Calculate changes from previous snapshot
            prev_items = previous_snapshot.get('total_items', 0)
            prev_cards = previous_snapshot.get('total_cards', 0)
            prev_value = float(previous_snapshot.get('total_value', 0)) if previous_snapshot.get('total_value') is not None else 0.0
            prev_avg_value = float(previous_snapshot.get('avg_card_value', 0)) if previous_snapshot.get('avg_card_value') is not None else 0.0
            
            items_change = current_totals['total_items'] - prev_items
            cards_change = current_totals['total_cards'] - prev_cards
            value_change = current_totals['total_value'] - prev_value
            avg_value_change = current_totals['avg_card_value'] - prev_avg_value
            
            # Calculate percentage changes
            items_percent = (items_change / prev_items * 100) if prev_items > 0 else 0
            cards_percent = (cards_change / prev_cards * 100) if prev_cards > 0 else 0
            value_percent = (value_change / prev_value * 100) if prev_value > 0 else 0
            
            # Calculate days since last change
            prev_date = previous_snapshot.get('snapshot_date')
            if prev_date:
                if isinstance(prev_date, str):
                    prev_date = datetime.strptime(prev_date, '%Y-%m-%d').date()
                days_diff = (date.today() - prev_date).days
            else:
                days_diff = 0
            
            change_data = {
                'change_date': date.today().strftime('%Y-%m-%d'),
                'total_items_change': items_change,
                'total_cards_change': cards_change,
                'total_value_change': value_change,
                'avg_card_value_change': avg_value_change,
                'total_items_percent_change': round(items_percent, 2),
                'total_cards_percent_change': round(cards_percent, 2),
                'total_value_percent_change': round(value_percent, 2),
                'items_added': sync_result.get('total_added', 0),
                'items_removed': 0 if not replace_all else max(0, -items_change),
                'items_updated': sync_result.get('total_updated', 0),
                'new_cards_added': sync_result.get('total_added', 0),
                'existing_cards_updated': sync_result.get('total_updated', 0),
                'value_added': max(0, value_change),
                'value_removed': max(0, -value_change),
                'days_since_last_change': days_diff,
                'change_type': 'replace_all' if replace_all else 'sync',
                'source_file': filename,
                'metadata': {
                    'sync_result': sync_result,
                    'replace_all': replace_all,
                    'previous_totals': {
                        'total_items': prev_items,
                        'total_cards': prev_cards,
                        'total_value': prev_value,
                        'avg_card_value': prev_avg_value
                    },
                    'current_totals': current_totals
                }
            }
        
        return await self.db_service.create_inventory_change_record(
            username=username,
            snapshot_id=snapshot_id,
            change_data=change_data
        )
    
    async def get_inventory_analytics(
        self,
        username: str,
        period: str = 'month'
    ) -> Dict[str, Any]:
        """Get inventory analytics and growth statistics"""
        return await self.db_service.get_inventory_growth_stats(username, period)
