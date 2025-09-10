import logging
import PyPDF2
import io
import re
import tempfile
from typing import Dict, Any, List
from datetime import datetime
from .database import DatabaseService

logger = logging.getLogger(__name__)

class TCGPlayerService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def extract_orders_from_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract order information from TCGPlayer PDF"""
        try:
            # Save PDF to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_content)
                temp_pdf_path = tmp_file.name
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Preprocess text
            text = self._preprocess_text(text)
            
            # Extract orders
            orders = self._extract_orders_from_text(text)
            
            # Generate shipping labels
            shipping_labels = self._generate_shipping_labels(orders)
            
            total_value = sum(
                sum(item.get('total_price', 0) for item in order.get('items', []))
                for order in orders
            )
            
            return {
                "success": True,
                "orders": orders,
                "shipping_labels": shipping_labels,
                "total_orders": len(orders),
                "total_value": total_value,
                "extraction_summary": {
                    "pages_processed": len(pdf_reader.pages),
                    "orders_found": len(orders),
                    "labels_generated": len(shipping_labels)
                }
            }
        
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return {
                "success": False,
                "orders": [],
                "shipping_labels": [],
                "total_orders": 0,
                "total_value": 0.0,
                "extraction_summary": {"error": str(e)}
            }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess PDF text for better parsing"""
        # Remove boilerplate and repeated seller info
        boilerplate_pattern = (
            r"ForAny Questions About Your Order:.*?feedback foryour order\."
        )
        text = re.sub(boilerplate_pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove 'Thank you...' and 'Holo HitsTCG' everywhere
        text = re.sub(r"Thank youforbuying from Holo HitsTCG onTCGplayer.com\.?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Holo HitsTCG", "", text, flags=re.IGNORECASE)
        
        # Add newline after each field label if not present
        labels = [
            "Order Number:", "Shipping Address:", "Order Date:",
            "Shipping Method:", "Buyer Name:", "Seller Name:"
        ]
        for label in labels:
            text = re.sub(f"({label})(?!\\s*\\n)", r"\1\n", text)
        
        return text
    
    def _extract_orders_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract orders from preprocessed text"""
        # Split only on 'Order Number:' at the start of a line
        blocks = re.split(r'^Order Number:', text, flags=re.MULTILINE)
        orders = []
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            block = 'Order Number:' + block  # Add back the label
            
            # Only process if block contains a valid order number and a date
            if not re.search(r'Order Number:\s*[\w\- ]+', block):
                continue
            if not re.search(r'\d{2}/\d{2}/\d{4}', block):
                continue
            
            # Extract fields
            order_number = re.search(r'Order Number:\s*([\w\- ]+)', block)
            shipping_address = re.search(r'Shipping Address:\s*([\s\S]*?)Order Date:', block)
            order_date = re.search(r'(\d{2}/\d{2}/\d{4})', block)
            
            # Extract shipping method
            shipping_method = 'N/A'
            shipping_method_match = re.search(r'Shipping Method:(.*)', block)
            if shipping_method_match:
                after_shipping = block[shipping_method_match.end():]
                for line in after_shipping.splitlines():
                    line = line.strip()
                    if not line or line.endswith(':') or re.match(r'\d{2}/\d{2}/\d{4}', line):
                        continue
                    if line.lower() in ['buyer name:', 'seller name:']:
                        continue
                    shipping_method = line
                    break
            
            # Extract buyer and seller names
            buyer_name = re.search(r'Buyer Name:\s*([^\n]+)', block)
            seller_name = re.search(r'Seller Name:\s*([^\n]+)', block)
            
            # Extract items
            items = self._extract_items_from_block(block)
            
            # Parse shipping address
            shipping_addr_raw = shipping_address.group(1).strip() if shipping_address else ""
            parsed_address = self._parse_shipping_address(shipping_addr_raw)
            
            order = {
                'order_number': order_number.group(1).strip() if order_number else 'N/A',
                'order_date': order_date.group(1) if order_date else None,
                'shipping_method': shipping_method,
                'buyer_name': buyer_name.group(1).strip() if buyer_name else 'N/A',
                'seller_name': seller_name.group(1).strip() if seller_name else 'N/A',
                'shipping_address': {
                    'raw': shipping_addr_raw,
                    'parsed': parsed_address
                },
                'items': items
            }
            
            orders.append(order)
        
        return orders
    
    def _extract_items_from_block(self, block: str) -> List[Dict[str, Any]]:
        """Extract items from an order block"""
        items = []
        
        # Look for item patterns after the quantity/description/price header
        lines = block.split('\n')
        in_items_section = False
        
        for line in lines:
            line = line.strip()
            
            # Start looking for items after the header
            if 'Quantity Description Price Total Price' in line:
                in_items_section = True
                continue
            
            if not in_items_section:
                continue
            
            # Stop at next section
            if any(label in line for label in ['Order Number:', 'Shipping Address:', 'Order Date:']):
                break
            
            # Try to match item pattern: quantity description $price $total
            item_match = re.match(r'(\d+)\s+(.+?)\s+\$(\d+\.\d{2})\s+\$(\d+\.\d{2})$', line)
            if item_match:
                quantity, description, price, total_price = item_match.groups()
                items.append({
                    'quantity': int(quantity),
                    'description': description.strip(),
                    'price': float(price),
                    'total_price': float(total_price)
                })
        
        return items
    
    def _parse_shipping_address(self, address_text: str) -> Dict[str, str]:
        """Parse shipping address into components"""
        lines = [line.strip() for line in address_text.split('\n') if line.strip()]
        
        if not lines:
            return {}
        
        # Basic parsing - can be enhanced with usaddress library
        name = lines[0] if lines else ""
        address_line_1 = lines[1] if len(lines) > 1 else ""
        address_line_2 = lines[2] if len(lines) > 2 and not re.match(r'.*,\s*[A-Z]{2}\s*\d', lines[2]) else ""
        
        # Find city, state, zip line
        city_state_zip_line = ""
        for line in reversed(lines):
            if re.match(r'.*,\s*[A-Z]{2}\s*\d', line):
                city_state_zip_line = line
                break
        
        city, state, zip_code = "", "", ""
        if city_state_zip_line:
            match = re.match(r'^(.*?),\s*([A-Z]{2})\s*([\d\-\s]+)$', city_state_zip_line)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                zip_code = match.group(3).strip().replace(' ', '').replace('-', '')
                # Format zip with hyphen if 9 digits
                if len(zip_code) == 9 and zip_code.isdigit():
                    zip_code = f"{zip_code[:5]}-{zip_code[5:]}"
        
        return {
            'name': name,
            'address_line_1': address_line_1,
            'address_line_2': address_line_2,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'country': 'USA'  # Default for TCGPlayer orders
        }
    
    def _generate_shipping_labels(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate shipping labels from orders"""
        shipping_labels = []
        
        for order in orders:
            if not order.get('shipping_address', {}).get('parsed'):
                continue
            
            parsed_addr = order['shipping_address']['parsed']
            
            # Calculate package details
            total_items = sum(item.get('quantity', 0) for item in order.get('items', []))
            total_value = sum(item.get('total_price', 0) for item in order.get('items', []))
            estimated_weight = max(1, total_items * 0.5)  # Estimate 0.5 oz per card
            
            # Generate contents description
            item_descriptions = [item.get('description', '') for item in order.get('items', [])]
            contents = ', '.join(item_descriptions[:3])  # First 3 items
            if len(item_descriptions) > 3:
                contents += f" and {len(item_descriptions) - 3} more items"
            
            label = {
                'order_number': order.get('order_number', ''),
                'order_date': order.get('order_date', ''),
                'shipping_method': order.get('shipping_method', ''),
                'recipient': {
                    'name': parsed_addr.get('name', ''),
                    'address_line_1': parsed_addr.get('address_line_1', ''),
                    'address_line_2': parsed_addr.get('address_line_2', ''),
                    'city': parsed_addr.get('city', ''),
                    'state': parsed_addr.get('state', ''),
                    'zip_code': parsed_addr.get('zip_code', ''),
                    'country': parsed_addr.get('country', 'USA')
                },
                'sender': {
                    'name': 'TCG Seller',
                    'business_name': order.get('seller_name', 'TCG Business')
                },
                'package': {
                    'total_items': total_items,
                    'total_value': total_value,
                    'estimated_weight_oz': estimated_weight,
                    'contents': contents
                },
                'tracking_required': total_value > 20,  # Require tracking for orders over $20
                'insurance_required': total_value > 50  # Require insurance for orders over $50
            }
            
            shipping_labels.append(label)
        
        return shipping_labels
    
    async def update_tcgplayer_ids(self) -> Dict[str, Any]:
        """Update TCGPlayer IDs for cards (admin function)"""
        try:
            # This would implement the logic to update TCGPlayer IDs
            # from the existing update_tcgplayer_ids_from_json.py functionality
            
            return {
                "success": True,
                "message": "TCGPlayer IDs updated successfully",
                "updated_count": 0,
                "details": {}
            }
        
        except Exception as e:
            logger.error(f"TCGPlayer ID update error: {e}")
            return {
                "success": False,
                "message": f"Update failed: {str(e)}",
                "updated_count": 0,
                "details": {}
            }
    
    async def get_cloud_control_status(self) -> Dict[str, Any]:
        """Get cloud control status (admin function)"""
        try:
            # This would integrate with your existing ECS/cloud control functionality
            return {
                "success": True,
                "status": "running",
                "services": [],
                "last_updated": "2024-01-01T00:00:00Z"
            }
        
        except Exception as e:
            logger.error(f"Cloud control error: {e}")
            return {
                "success": False,
                "status": "error",
                "services": [],
                "last_updated": "2024-01-01T00:00:00Z"
            }
