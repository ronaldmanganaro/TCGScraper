import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .database import DatabaseService

logger = logging.getLogger(__name__)

class PokemonTrackerService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def get_prices(self, set_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Pokemon card prices"""
        try:
            # Search for Pokemon cards
            cards = await self.db_service.search_cards(
                set_name=set_name,
                limit=1000
            )
            
            # Filter for Pokemon cards (assuming we have a game field)
            pokemon_cards = [card for card in cards if 'pokemon' in card.get('game', '').lower()]
            
            # Get recent price data for each card
            prices = []
            for card in pokemon_cards:
                price_history = await self.db_service.get_card_price_history(card['id'], days=7)
                if price_history:
                    latest_price = price_history[0]
                    prices.append({
                        "name": card['name'],
                        "set_name": card['set_name'],
                        "rarity": card.get('rarity'),
                        "price": latest_price['price'],
                        "foil_price": latest_price.get('foil_price'),
                        "last_updated": latest_price['date'],
                        "tcg_player_id": card.get('tcg_player_id')
                    })
            
            return {
                "success": True,
                "prices": prices,
                "last_updated": datetime.utcnow(),
                "set_filter": set_name
            }
        
        except Exception as e:
            logger.error(f"Pokemon price tracking error: {e}")
            return {
                "success": False,
                "prices": [],
                "last_updated": datetime.utcnow(),
                "set_filter": set_name
            }
