import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from .database import DatabaseService
from models.schemas import RepricerFilterRequest, RepricerUpdateRequest

logger = logging.getLogger(__name__)

class RepricerService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def process_inventory_upload(
        self, 
        df: pd.DataFrame, 
        user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process uploaded inventory CSV file"""
        try:
            # Validate required columns
            required_columns = [
                "Product Name", "Set Name", "Rarity", "Total Quantity", 
                "TCG Marketplace Price", "TCG Market Price"
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    "success": False,
                    "message": f"Missing required columns: {', '.join(missing_columns)}",
                    "data_preview": [],
                    "total_rows": 0
                }
            
            # Clean and validate data
            df = self._clean_inventory_data(df)
            
            # Store in session or temporary storage if user is authenticated
            if user:
                await self._store_user_inventory_session(user['username'], df)
            
            # Return preview data
            preview_data = df.head(10).to_dict('records')
            
            return {
                "success": True,
                "message": f"Successfully processed {len(df)} inventory items",
                "data_preview": preview_data,
                "total_rows": len(df)
            }
        
        except Exception as e:
            logger.error(f"Inventory upload processing error: {e}")
            return {
                "success": False,
                "message": f"Failed to process inventory: {str(e)}",
                "data_preview": [],
                "total_rows": 0
            }
    
    def _clean_inventory_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate inventory data"""
        # Remove rows with missing essential data
        df = df.dropna(subset=["Product Name", "TCG Marketplace Price", "Total Quantity"])
        
        # Convert numeric columns
        numeric_columns = ["TCG Marketplace Price", "TCG Market Price", "Total Quantity"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with invalid prices or quantities
        df = df[(df["TCG Marketplace Price"] > 0) & (df["Total Quantity"] > 0)]
        
        # Fill missing TCG Market Price with Marketplace Price
        if "TCG Market Price" in df.columns:
            df["TCG Market Price"].fillna(df["TCG Marketplace Price"], inplace=True)
        else:
            df["TCG Market Price"] = df["TCG Marketplace Price"]
        
        return df
    
    async def filter_inventory(self, filter_data: RepricerFilterRequest) -> Dict[str, Any]:
        """Filter inventory data based on criteria"""
        try:
            # For now, we'll work with a sample dataset or user's uploaded data
            # In a real implementation, this would fetch from database
            df = await self._get_current_inventory_data()
            
            if df is None or df.empty:
                return {
                    "success": False,
                    "filtered_data": [],
                    "total_filtered": 0,
                    "filters_applied": {}
                }
            
            # Apply filters
            filtered_df = self._apply_filters(df, filter_data)
            
            return {
                "success": True,
                "filtered_data": filtered_df.to_dict('records'),
                "total_filtered": len(filtered_df),
                "filters_applied": filter_data.dict()
            }
        
        except Exception as e:
            logger.error(f"Inventory filtering error: {e}")
            return {
                "success": False,
                "filtered_data": [],
                "total_filtered": 0,
                "filters_applied": {}
            }
    
    def _apply_filters(self, df: pd.DataFrame, filters: RepricerFilterRequest) -> pd.DataFrame:
        """Apply filtering logic to dataframe"""
        filtered = df[
            (df["TCG Marketplace Price"] >= filters.min_price) &
            (df["TCG Marketplace Price"] <= filters.max_price) &
            (df["Total Quantity"] >= filters.min_listing) &
            (df["Total Quantity"] <= filters.max_listing)
        ]
        
        # Apply categorical filters
        if filters.product_line and filters.product_line != "All":
            filtered = filtered[filtered["Product Line"] == filters.product_line]
        
        if filters.set_name and filters.set_name != "All":
            filtered = filtered[filtered["Set Name"] == filters.set_name]
        
        if filters.rarity_filter and filters.rarity_filter != "All":
            filtered = filtered[filtered["Rarity"] == filters.rarity_filter]
        
        # Apply search text filter
        if filters.search_text:
            filtered = filtered[
                filtered["Product Name"].str.contains(
                    filters.search_text, case=False, na=False
                )
            ]
        
        return filtered
    
    async def update_prices(self, update_data: RepricerUpdateRequest) -> Dict[str, Any]:
        """Update prices for selected inventory items"""
        try:
            updated_items = []
            
            for update in update_data.updates:
                updated_item = await self._update_single_item_price(
                    update, 
                    update_data.update_method,
                    update_data.percentage_change,
                    update_data.fixed_price
                )
                if updated_item:
                    updated_items.append(updated_item)
            
            return {
                "success": True,
                "message": f"Successfully updated {len(updated_items)} items",
                "updated_count": len(updated_items),
                "updated_items": updated_items
            }
        
        except Exception as e:
            logger.error(f"Price update error: {e}")
            return {
                "success": False,
                "message": f"Failed to update prices: {str(e)}",
                "updated_count": 0,
                "updated_items": []
            }
    
    async def _update_single_item_price(
        self, 
        item: Dict[str, Any], 
        method: str,
        percentage_change: Optional[float] = None,
        fixed_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Update price for a single inventory item"""
        try:
            current_price = item.get("TCG Marketplace Price", 0)
            new_price = current_price
            
            if method == "percentage" and percentage_change is not None:
                new_price = current_price * (1 + percentage_change / 100)
            elif method == "fixed" and fixed_price is not None:
                new_price = fixed_price
            elif method == "market_price":
                new_price = item.get("TCG Market Price", current_price)
            
            # Round to 2 decimal places
            new_price = round(new_price, 2)
            
            # Update in database if item has an ID
            if item.get("id"):
                await self._update_inventory_item_price(item["id"], new_price)
            
            return {
                "id": item.get("id"),
                "product_name": item.get("Product Name"),
                "old_price": current_price,
                "new_price": new_price,
                "price_change": new_price - current_price,
                "percentage_change": ((new_price - current_price) / current_price * 100) if current_price > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Single item price update error: {e}")
            return None
    
    async def analyze_repricing_suggestions(
        self, 
        df: pd.DataFrame, 
        threshold: float = 10.0
    ) -> Dict[str, Any]:
        """Analyze inventory and suggest repricing opportunities"""
        try:
            analysis_df = df.copy()
            
            # Calculate percentage difference between marketplace and market price
            analysis_df["percentage_difference"] = (
                (analysis_df["TCG Marketplace Price"] - analysis_df["TCG Market Price"]) /
                analysis_df["TCG Market Price"] * 100
            ).round(2)
            
            # Suggest new prices based on threshold
            analysis_df["suggested_price"] = (
                analysis_df["TCG Market Price"] * (1 + threshold / 100)
            ).round(2)
            
            # Filter cards that exceed threshold
            suggested_repricing = analysis_df[
                analysis_df["percentage_difference"].abs() > threshold
            ]
            
            # Calculate potential profit/loss
            suggested_repricing["potential_change"] = (
                suggested_repricing["suggested_price"] - 
                suggested_repricing["TCG Marketplace Price"]
            ) * suggested_repricing["Total Quantity"]
            
            return {
                "success": True,
                "total_items_analyzed": len(analysis_df),
                "items_needing_repricing": len(suggested_repricing),
                "suggestions": suggested_repricing.to_dict('records'),
                "total_potential_change": suggested_repricing["potential_change"].sum(),
                "threshold_used": threshold
            }
        
        except Exception as e:
            logger.error(f"Repricing analysis error: {e}")
            return {
                "success": False,
                "total_items_analyzed": 0,
                "items_needing_repricing": 0,
                "suggestions": [],
                "total_potential_change": 0,
                "threshold_used": threshold
            }
    
    async def _get_current_inventory_data(self) -> Optional[pd.DataFrame]:
        """Get current inventory data (placeholder for actual implementation)"""
        # This would typically fetch from database or session storage
        # For now, return None - in real implementation, this would fetch user's inventory
        return None
    
    async def _store_user_inventory_session(self, username: str, df: pd.DataFrame) -> None:
        """Store user's inventory data in session/cache"""
        # Implementation would store in Redis, database, or other session storage
        pass
    
    async def _update_inventory_item_price(self, item_id: int, new_price: float) -> None:
        """Update inventory item price in database"""
        query = """
            UPDATE inventory 
            SET price = %s, updated_at = NOW() 
            WHERE id = %s
        """
        await self.db_service.execute_query(query, (new_price, item_id), fetch_all=False)
    
    async def get_inventory_summary(self, username: str) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        try:
            stats = await self.db_service.get_inventory_stats(username)
            
            return {
                "success": True,
                "total_items": stats.get("total_items", 0),
                "total_cards": stats.get("total_cards", 0),
                "total_value": float(stats.get("total_value", 0)),
                "average_price": float(stats.get("avg_price", 0))
            }
        
        except Exception as e:
            logger.error(f"Inventory summary error: {e}")
            return {
                "success": False,
                "total_items": 0,
                "total_cards": 0,
                "total_value": 0.0,
                "average_price": 0.0
            }
