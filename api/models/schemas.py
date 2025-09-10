from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Authentication schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    username: str
    email: Optional[str] = None
    is_admin: bool = False

# Repricer schemas
class RepricerFilterRequest(BaseModel):
    min_price: float = Field(default=0.0, ge=0)
    max_price: float = Field(default=1000.0, ge=0)
    min_listing: int = Field(default=0, ge=0)
    max_listing: int = Field(default=1000, ge=0)
    product_line: Optional[str] = None
    set_name: Optional[str] = None
    rarity_filter: Optional[str] = None
    search_text: Optional[str] = None

class RepricerUploadResponse(BaseModel):
    success: bool
    message: str
    data_preview: List[Dict[str, Any]]
    total_rows: int

class RepricerFilterResponse(BaseModel):
    success: bool
    filtered_data: List[Dict[str, Any]]
    total_filtered: int
    filters_applied: Dict[str, Any]

class RepricerUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]]
    update_method: str = Field(default="percentage")  # "percentage", "fixed", "market_price"
    percentage_change: Optional[float] = None
    fixed_price: Optional[float] = None

class RepricerUpdateResponse(BaseModel):
    success: bool
    message: str
    updated_count: int
    updated_items: List[Dict[str, Any]]

# EV Tools schemas
class BoxSimulationRequest(BaseModel):
    set_code: str = Field(..., min_length=3, max_length=10)
    boxes_to_open: int = Field(..., ge=1, le=100)

class BoxSimulationResponse(BaseModel):
    success: bool
    set_code: str
    boxes_opened: int
    total_ev: float
    average_ev_per_box: float
    pulls: List[Dict[str, Any]]
    simulation_details: Dict[str, Any]

class PreconEVRequest(BaseModel):
    precon_name: str
    set_code: str
    calculate_singles: bool = True

class PreconEVResponse(BaseModel):
    success: bool
    precon_name: str
    total_ev: float
    card_values: List[Dict[str, Any]]
    summary: Dict[str, Any]

# Pokemon Price Tracker schemas
class PokemonPricesResponse(BaseModel):
    success: bool
    prices: List[Dict[str, Any]]
    last_updated: datetime
    set_filter: Optional[str] = None

# Manabox schemas
class ManaboxConvertResponse(BaseModel):
    success: bool
    message: str
    converted_data: List[Dict[str, Any]]
    conversion_stats: Dict[str, int]

# Inventory Management schemas
class InventoryItem(BaseModel):
    id: Optional[int] = None
    product_name: str
    set_name: str
    rarity: str
    condition: str
    quantity: int
    price: float
    tcg_player_id: Optional[str] = None

class InventoryResponse(BaseModel):
    success: bool
    inventory: List[InventoryItem]
    total_items: int
    total_value: float

class InventorySnapshot(BaseModel):
    id: Optional[int] = None
    snapshot_date: str
    total_items: int
    total_cards: int
    total_value: float
    avg_card_value: float
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    upload_timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class InventorySnapshotsResponse(BaseModel):
    success: bool
    snapshots: List[InventorySnapshot]
    total_snapshots: int

class InventoryUploadRequest(BaseModel):
    file_name: str
    file_size: int
    file_type: str = "application/pdf"

class InventoryUploadResponse(BaseModel):
    success: bool
    message: str
    upload_id: int
    processing_status: str

class InventoryPDFProcessResponse(BaseModel):
    success: bool
    message: str
    upload_id: Optional[int] = None
    snapshot_id: Optional[int] = None
    total_items: Optional[int] = None
    total_cards: Optional[int] = None
    total_value: Optional[float] = None
    items_added: Optional[int] = None
    items_updated: Optional[int] = None
    errors: List[str] = []
    replace_all: Optional[bool] = None

# TCGPlayer schemas
class TCGPlayerOrdersResponse(BaseModel):
    success: bool
    orders: List[Dict[str, Any]]
    shipping_labels: List[Dict[str, Any]]
    total_orders: int
    total_value: float
    extraction_summary: Dict[str, Any]

# Admin schemas
class AdminUpdateResponse(BaseModel):
    success: bool
    message: str
    updated_count: int
    details: Dict[str, Any]

class CloudControlResponse(BaseModel):
    success: bool
    status: str
    services: List[Dict[str, Any]]
    last_updated: datetime

# Generic response schemas
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

# File upload schemas
class FileUploadResponse(BaseModel):
    success: bool
    filename: str
    size: int
    content_type: str
    message: str

# Pagination schemas
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=1000)

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    page: int
    page_size: int
    total_pages: int
    total_items: int

# Filter and sort schemas
class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class SortParams(BaseModel):
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.asc

# Card-specific schemas
class CardInfo(BaseModel):
    name: str
    set_code: str
    set_name: str
    rarity: str
    tcg_player_id: Optional[str] = None
    scryfall_id: Optional[str] = None
    price: Optional[float] = None
    foil_price: Optional[float] = None

class SetInfo(BaseModel):
    code: str
    name: str
    release_date: Optional[datetime] = None
    card_count: Optional[int] = None
    type: Optional[str] = None  # "expansion", "core", "masters", etc.

# Price tracking schemas
class PriceHistory(BaseModel):
    card_id: str
    date: datetime
    price: float
    foil_price: Optional[float] = None
    source: str = "tcgplayer"

class PriceAlert(BaseModel):
    id: Optional[int] = None
    user_id: int
    card_id: str
    target_price: float
    alert_type: str = "below"  # "below", "above", "change"
    is_active: bool = True
    created_at: Optional[datetime] = None
