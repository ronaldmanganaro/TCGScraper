import random
import json
import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from .database import DatabaseService
from models.schemas import BoxSimulationRequest, PreconEVRequest

logger = logging.getLogger(__name__)

class EVToolsService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.data_path = os.path.join(os.path.dirname(__file__), '../../streamlit/data')
    
    async def simulate_booster_box(self, set_code: str, boxes_to_open: int) -> Dict[str, Any]:
        """Simulate opening booster boxes and calculate EV"""
        try:
            # Load card data for the set
            cards_data = await self._load_set_cards(set_code)
            if not cards_data:
                return {
                    "success": False,
                    "message": f"No card data found for set: {set_code}",
                    "set_code": set_code,
                    "boxes_opened": 0,
                    "total_ev": 0.0,
                    "average_ev_per_box": 0.0,
                    "pulls": [],
                    "simulation_details": {}
                }
            
            total_ev = 0.0
            all_pulls = []
            box_evs = []
            
            # Simulate each box
            for box_num in range(boxes_to_open):
                box_ev, box_pulls = await self._simulate_single_box(cards_data)
                total_ev += box_ev
                box_evs.append(box_ev)
                all_pulls.extend([{**pull, "box_number": box_num + 1} for pull in box_pulls])
            
            average_ev = total_ev / boxes_to_open if boxes_to_open > 0 else 0
            
            # Calculate statistics
            simulation_details = {
                "min_box_ev": min(box_evs) if box_evs else 0,
                "max_box_ev": max(box_evs) if box_evs else 0,
                "median_box_ev": sorted(box_evs)[len(box_evs)//2] if box_evs else 0,
                "total_packs_opened": boxes_to_open * 15,  # Assuming 15 packs per box
                "valuable_pulls": [pull for pull in all_pulls if pull.get("price", 0) > 5.0],
                "rarity_breakdown": self._calculate_rarity_breakdown(all_pulls)
            }
            
            return {
                "success": True,
                "set_code": set_code,
                "boxes_opened": boxes_to_open,
                "total_ev": round(total_ev, 2),
                "average_ev_per_box": round(average_ev, 2),
                "pulls": all_pulls,
                "simulation_details": simulation_details
            }
        
        except Exception as e:
            logger.error(f"Box simulation error: {e}")
            return {
                "success": False,
                "message": f"Simulation failed: {str(e)}",
                "set_code": set_code,
                "boxes_opened": 0,
                "total_ev": 0.0,
                "average_ev_per_box": 0.0,
                "pulls": [],
                "simulation_details": {}
            }
    
    async def _simulate_single_box(self, cards_data: List[Dict]) -> tuple[float, List[Dict]]:
        """Simulate opening a single booster box"""
        box_ev = 0.0
        box_pulls = []
        
        # Simulate 15 packs per box
        for pack_num in range(15):
            pack_pulls = self._open_booster_pack(cards_data)
            pack_ev = self._calculate_pack_ev(pack_pulls)
            box_ev += pack_ev
            
            # Add pack info to pulls
            for pull in pack_pulls:
                box_pulls.append({
                    **pull,
                    "pack_number": pack_num + 1,
                    "price": self._get_card_price(pull)
                })
        
        return box_ev, box_pulls
    
    def _open_booster_pack(self, cards: List[Dict]) -> List[Dict]:
        """Simulate opening a single booster pack"""
        booster_pack = []
        
        # Add commons (10) based on probability
        commons = [card for card in cards if card.get('rarity') == 'common']
        if commons:
            commons_weights = [card.get('estimated_pull_probability', 1) for card in commons]
            booster_pack.extend(random.choices(commons, weights=commons_weights, k=10))
        
        # Add uncommons (3) based on probability
        uncommons = [card for card in cards if card.get('rarity') == 'uncommon']
        if uncommons:
            uncommons_weights = [card.get('estimated_pull_probability', 1) for card in uncommons]
            booster_pack.extend(random.choices(uncommons, weights=uncommons_weights, k=3))
        
        # Add rare/mythic rare (1) based on probability
        rare_or_mythic = [card for card in cards if card.get('rarity') in ['rare', 'mythic']]
        if rare_or_mythic:
            rare_or_mythic_weights = [card.get('estimated_pull_probability', 1) for card in rare_or_mythic]
            booster_pack.append(random.choices(rare_or_mythic, weights=rare_or_mythic_weights, k=1)[0])
        
        # Add a foil card (random foil, could be any rarity)
        foil_cards = [card for card in cards if card.get('foil', False)]
        if foil_cards:
            foil_weights = [card.get('estimated_pull_probability', 1) for card in foil_cards]
            booster_pack.append(random.choices(foil_cards, weights=foil_weights, k=1)[0])
        elif cards:
            # If no foil cards, choose randomly from all cards
            booster_pack.append(random.choice(cards))
        
        return booster_pack
    
    def _calculate_pack_ev(self, booster_pack: List[Dict]) -> float:
        """Calculate the expected value of a booster pack"""
        pack_ev = 0.0
        
        for card in booster_pack:
            price = self._get_card_price(card)
            pack_ev += price
        
        return pack_ev
    
    def _get_card_price(self, card: Dict) -> float:
        """Extract price from card data"""
        try:
            prices = card.get('prices', {})
            price_str = prices.get('usd', '0')
            return float(price_str) if price_str else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_rarity_breakdown(self, pulls: List[Dict]) -> Dict[str, int]:
        """Calculate breakdown of pulls by rarity"""
        breakdown = {}
        for pull in pulls:
            rarity = pull.get('rarity', 'unknown')
            breakdown[rarity] = breakdown.get(rarity, 0) + 1
        return breakdown
    
    async def calculate_precon_ev(self, precon_data: PreconEVRequest) -> Dict[str, Any]:
        """Calculate expected value of a preconstructed deck"""
        try:
            # Load precon decklist
            decklist = await self._load_precon_decklist(precon_data.precon_name, precon_data.set_code)
            if not decklist:
                return {
                    "success": False,
                    "message": f"Precon decklist not found: {precon_data.precon_name}",
                    "precon_name": precon_data.precon_name,
                    "total_ev": 0.0,
                    "card_values": [],
                    "summary": {}
                }
            
            total_ev = 0.0
            card_values = []
            
            for card_entry in decklist:
                card_name = card_entry.get('name', '')
                quantity = card_entry.get('quantity', 1)
                
                # Get card price from database or API
                card_price = await self._get_card_market_price(card_name, precon_data.set_code)
                card_total_value = card_price * quantity
                total_ev += card_total_value
                
                if precon_data.calculate_singles or card_price > 1.0:  # Only include valuable cards if not calculating all singles
                    card_values.append({
                        "name": card_name,
                        "quantity": quantity,
                        "unit_price": round(card_price, 2),
                        "total_value": round(card_total_value, 2),
                        "rarity": card_entry.get('rarity', 'unknown')
                    })
            
            # Sort by total value descending
            card_values.sort(key=lambda x: x['total_value'], reverse=True)
            
            summary = {
                "total_cards": sum(card.get('quantity', 1) for card in decklist),
                "unique_cards": len(decklist),
                "valuable_cards": len([c for c in card_values if c['total_value'] > 5.0]),
                "most_valuable_card": card_values[0] if card_values else None,
                "average_card_value": round(total_ev / len(decklist), 2) if decklist else 0
            }
            
            return {
                "success": True,
                "precon_name": precon_data.precon_name,
                "total_ev": round(total_ev, 2),
                "card_values": card_values,
                "summary": summary
            }
        
        except Exception as e:
            logger.error(f"Precon EV calculation error: {e}")
            return {
                "success": False,
                "message": f"Failed to calculate precon EV: {str(e)}",
                "precon_name": precon_data.precon_name,
                "total_ev": 0.0,
                "card_values": [],
                "summary": {}
            }
    
    async def _load_set_cards(self, set_code: str) -> Optional[List[Dict]]:
        """Load card data for a specific set"""
        try:
            # Try to load from JSON file first
            json_file = os.path.join(self.data_path, 'cards_by_set', f'{set_code}_cards.json')
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    return json.load(f)
            
            # Try to load from CSV file
            csv_file = os.path.join(self.data_path, 'cards_by_set', f'{set_code}_cards.csv')
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                return df.to_dict('records')
            
            # If no local data, try to fetch from database
            cards = await self.db_service.search_cards(set_name=set_code)
            return cards
        
        except Exception as e:
            logger.error(f"Error loading set cards for {set_code}: {e}")
            return None
    
    async def _load_precon_decklist(self, precon_name: str, set_code: str) -> Optional[List[Dict]]:
        """Load preconstructed deck decklist"""
        try:
            # Look for precon file
            precon_file = os.path.join(self.data_path, 'precons', set_code.upper(), f'{precon_name}.txt')
            if not os.path.exists(precon_file):
                return None
            
            decklist = []
            with open(precon_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse line like "4 Lightning Bolt" or "1x Jace, the Mind Sculptor"
                        parts = line.split(' ', 1)
                        if len(parts) >= 2:
                            quantity_str = parts[0].replace('x', '')
                            try:
                                quantity = int(quantity_str)
                                card_name = parts[1]
                                decklist.append({
                                    'name': card_name,
                                    'quantity': quantity
                                })
                            except ValueError:
                                continue
            
            return decklist
        
        except Exception as e:
            logger.error(f"Error loading precon decklist {precon_name}: {e}")
            return None
    
    async def _get_card_market_price(self, card_name: str, set_code: str = None) -> float:
        """Get current market price for a card"""
        try:
            # Search for card in database
            cards = await self.db_service.search_cards(search_term=card_name, set_name=set_code, limit=1)
            if cards:
                # Get latest price from price history
                card_id = cards[0]['id']
                price_history = await self.db_service.get_card_price_history(card_id, days=1)
                if price_history:
                    return float(price_history[0].get('price', 0))
            
            return 0.0
        
        except Exception as e:
            logger.error(f"Error getting card price for {card_name}: {e}")
            return 0.0
    
    async def get_set_list(self) -> List[Dict[str, Any]]:
        """Get list of available sets for simulation"""
        try:
            sets = await self.db_service.get_sets()
            return [
                {
                    "code": s['code'],
                    "name": s['name'],
                    "release_date": s.get('release_date'),
                    "card_count": s.get('card_count', 0)
                }
                for s in sets
            ]
        except Exception as e:
            logger.error(f"Error getting set list: {e}")
            return []
