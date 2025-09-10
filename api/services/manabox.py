import pandas as pd
import logging
from typing import Dict, Any, List
from .database import DatabaseService

logger = logging.getLogger(__name__)

class ManaboxService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def convert_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert Manabox CSV format"""
        try:
            # Expected Manabox columns and their mappings
            manabox_mapping = {
                'Card Name': 'name',
                'Set': 'set_name',
                'Quantity': 'quantity',
                'Condition': 'condition',
                'Foil': 'foil',
                'Language': 'language'
            }
            
            # Check for required columns
            required_cols = ['Card Name', 'Set', 'Quantity']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return {
                    "success": False,
                    "message": f"Missing required columns: {', '.join(missing_cols)}",
                    "converted_data": [],
                    "conversion_stats": {}
                }
            
            # Convert to standard format
            converted_data = []
            stats = {
                "total_cards": 0,
                "unique_cards": len(df),
                "sets_found": len(df['Set'].unique()) if 'Set' in df.columns else 0,
                "foils": 0,
                "conditions": {}
            }
            
            for _, row in df.iterrows():
                converted_card = {
                    "name": row.get('Card Name', ''),
                    "set_name": row.get('Set', ''),
                    "quantity": int(row.get('Quantity', 1)),
                    "condition": row.get('Condition', 'NM'),
                    "foil": row.get('Foil', False),
                    "language": row.get('Language', 'English')
                }
                
                # Update stats
                stats["total_cards"] += converted_card["quantity"]
                if converted_card["foil"]:
                    stats["foils"] += 1
                
                condition = converted_card["condition"]
                stats["conditions"][condition] = stats["conditions"].get(condition, 0) + 1
                
                converted_data.append(converted_card)
            
            return {
                "success": True,
                "message": f"Successfully converted {len(converted_data)} card entries",
                "converted_data": converted_data,
                "conversion_stats": stats
            }
        
        except Exception as e:
            logger.error(f"Manabox conversion error: {e}")
            return {
                "success": False,
                "message": f"Conversion failed: {str(e)}",
                "converted_data": [],
                "conversion_stats": {}
            }
