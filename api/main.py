from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import logging
import sys
from contextlib import asynccontextmanager

# Import our existing functions
from services.database import DatabaseService
from services.repricer import RepricerService
from services.ev_tools import EVToolsService
from services.pokemon_tracker import PokemonTrackerService
from services.manabox import ManaboxService
from services.inventory import InventoryService, upload_progress
from services.tcgplayer import TCGPlayerService
from services.auth import AuthService
from models.schemas import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database tables on startup"""
    logger.info("Initializing database...")
    
    # SQL for creating tables - read from init_db.sql
    try:
        import os
        init_sql_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
        if os.path.exists(init_sql_path):
            with open(init_sql_path, 'r') as f:
                create_tables_sql = f.read()
        else:
            # Fallback to basic users table if init_db.sql not found
            create_tables_sql = """
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """
        
        # Also add inventory_changes table
        inventory_changes_sql_path = os.path.join(os.path.dirname(__file__), 'add_inventory_changes_table.sql')
        if os.path.exists(inventory_changes_sql_path):
            with open(inventory_changes_sql_path, 'r') as f:
                create_tables_sql += "\n\n" + f.read()
        
    except Exception as e:
        logger.warning(f"Could not read SQL files: {e}")
        # Fallback to basic users table
        create_tables_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """
    
    try:
        await db_service.execute_query(create_tables_sql, fetch_all=False)
        
        # Check if admin user exists, create if not
        admin_user = await db_service.get_user_by_username('rmangana')
        if not admin_user:
            logger.info("Creating admin user...")
            admin_result = await auth_service.create_user('rmangana', 'admin@tcgscraper.com', 'admin123')
            if admin_result:
                # Make user admin
                await db_service.execute_query(
                    "UPDATE users SET is_admin = TRUE WHERE username = %s",
                    ('rmangana',),
                    fetch_all=False
                )
                logger.info("✅ Admin user created successfully")
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up TCG Scraper API...")
    
    # Initialize database tables
    try:
        await init_database()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down TCG Scraper API...")
    await db_service.close()

app = FastAPI(
    title="TCG Scraper API",
    description="API for TCG inventory management, price tracking, and EV calculation tools",
    version="1.0.0"
    # lifespan=lifespan  # Temporarily disabled for testing
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Explicitly allow frontend origins
    allow_credentials=True,  # Allow credentials for specific origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
db_service = DatabaseService()
auth_service = AuthService()
repricer_service = RepricerService(db_service)
ev_tools_service = EVToolsService(db_service)
pokemon_tracker_service = PokemonTrackerService(db_service)
manabox_service = ManaboxService(db_service)
inventory_service = InventoryService(db_service)
tcgplayer_service = TCGPlayerService(db_service)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = await auth_service.verify_token_async(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Optional authentication for public endpoints
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if not credentials:
        return None
    return await get_current_user(credentials)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TCG Scraper API"}

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    try:
        result = await auth_service.authenticate_user(login_data.username, login_data.password)
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return result
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/auth/register", response_model=UserResponse)
async def register(register_data: RegisterRequest):
    try:
        # Check if username already exists
        existing_user = await db_service.get_user_by_username(register_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        result = await auth_service.create_user(
            register_data.username, 
            register_data.email, 
            register_data.password
        )
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        return UserResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# Repricer endpoints
@app.post("/repricer/upload", response_model=RepricerUploadResponse)
async def upload_inventory_file(
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        result = await repricer_service.process_inventory_upload(df, current_user)
        return result
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@app.post("/repricer/filter", response_model=RepricerFilterResponse)
async def filter_inventory(
    filter_data: RepricerFilterRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        result = await repricer_service.filter_inventory(filter_data)
        return result
    except Exception as e:
        logger.error(f"Filter error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to filter inventory: {str(e)}")

@app.post("/repricer/update-prices", response_model=RepricerUpdateResponse)
async def update_prices(
    update_data: RepricerUpdateRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        result = await repricer_service.update_prices(update_data)
        return result
    except Exception as e:
        logger.error(f"Price update error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update prices: {str(e)}")

# EV Tools endpoints
@app.post("/ev-tools/simulate-box", response_model=BoxSimulationResponse)
async def simulate_booster_box(
    simulation_data: BoxSimulationRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        result = await ev_tools_service.simulate_booster_box(
            simulation_data.set_code,
            simulation_data.boxes_to_open
        )
        return result
    except Exception as e:
        logger.error(f"Box simulation error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to simulate box: {str(e)}")

@app.post("/ev-tools/precon-ev", response_model=PreconEVResponse)
async def calculate_precon_ev(
    precon_data: PreconEVRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        result = await ev_tools_service.calculate_precon_ev(precon_data)
        return result
    except Exception as e:
        logger.error(f"Precon EV error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to calculate precon EV: {str(e)}")

# Pokemon Price Tracker endpoints
@app.get("/pokemon/prices", response_model=PokemonPricesResponse)
async def get_pokemon_prices(
    set_name: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        result = await pokemon_tracker_service.get_prices(set_name)
        return result
    except Exception as e:
        logger.error(f"Pokemon prices error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get Pokemon prices: {str(e)}")

# Manabox endpoints
@app.post("/manabox/convert", response_model=ManaboxConvertResponse)
async def convert_manabox_csv(
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        result = await manabox_service.convert_csv(df)
        return result
    except Exception as e:
        logger.error(f"Manabox conversion error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to convert Manabox CSV: {str(e)}")

# Inventory Management endpoints
@app.get("/inventory", response_model=InventoryResponse)
async def get_inventory(
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await inventory_service.get_user_inventory(current_user['username'])
        return result
    except Exception as e:
        logger.error(f"Inventory retrieval error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get inventory: {str(e)}")

@app.get("/inventory/snapshots", response_model=InventorySnapshotsResponse)
async def get_inventory_snapshots(
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await inventory_service.get_inventory_snapshots(current_user['username'])
        return result
    except Exception as e:
        logger.error(f"Inventory snapshots retrieval error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get inventory snapshots: {str(e)}")

@app.post("/inventory/upload-pdf", response_model=InventoryPDFProcessResponse)
async def upload_inventory_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        contents = await file.read()
        result = await inventory_service.upload_inventory_pdf(
            current_user['username'], 
            contents, 
            file.filename
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")

@app.options("/inventory/upload-csv")
async def upload_csv_options():
    """Handle preflight OPTIONS request for CSV upload"""
    return {"message": "OK"}

@app.post("/inventory/upload-csv", response_model=InventoryPDFProcessResponse)
async def upload_inventory_csv(
    file: UploadFile = File(...),
    replace_all: bool = False,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        contents = await file.read()
        
        # Use default username if no user is authenticated
        username = current_user['username'] if current_user else 'rmangana'
        
        result = await inventory_service.upload_inventory_csv(
            username, 
            contents, 
            file.filename,
            replace_all=replace_all
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

@app.get("/inventory/analytics/{period}")
async def get_inventory_analytics(
    period: str,
    current_user: dict = Depends(get_current_user)
):
    """Get inventory growth analytics for different time periods"""
    try:
        if period not in ['week', 'month', 'year']:
            raise HTTPException(status_code=400, detail="Period must be 'week', 'month', or 'year'")
        
        result = await inventory_service.get_inventory_analytics(
            current_user['username'],
            period
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get analytics: {str(e)}")

@app.get("/inventory/upload-progress/{upload_id}")
async def get_upload_progress(
    upload_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get upload progress for a specific upload ID"""
    try:
        progress_data = upload_progress.get(upload_id, {
            'progress': 0,
            'status': 'Not found',
            'timestamp': datetime.now()
        })
        return {
            'success': True,
            'upload_id': upload_id,
            'progress': progress_data['progress'],
            'status': progress_data['status'],
            'timestamp': progress_data['timestamp'].isoformat()
        }
    except Exception as e:
        logger.error(f"Upload progress error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get upload progress: {str(e)}")

# TCGPlayer Print Orders endpoints
@app.post("/tcgplayer/extract-orders", response_model=TCGPlayerOrdersResponse)
async def extract_tcgplayer_orders(
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        contents = await file.read()
        result = await tcgplayer_service.extract_orders_from_pdf(contents)
        return result
    except Exception as e:
        logger.error(f"Order extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to extract orders: {str(e)}")

# Admin-only endpoints
@app.post("/admin/update-tcgplayer-ids", response_model=AdminUpdateResponse)
async def update_tcgplayer_ids(
    current_user: dict = Depends(get_current_user)
):
    if current_user.get('username') != 'rmangana':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await tcgplayer_service.update_tcgplayer_ids()
        return result
    except Exception as e:
        logger.error(f"TCGPlayer ID update error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update TCGPlayer IDs: {str(e)}")

@app.get("/admin/cloud-control", response_model=CloudControlResponse)
async def get_cloud_control_status(
    current_user: dict = Depends(get_current_user)
):
    if current_user.get('username') != 'rmangana':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # This would integrate with your existing ECS/cloud control functionality
        result = await tcgplayer_service.get_cloud_control_status()
        return result
    except Exception as e:
        logger.error(f"Cloud control error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get cloud control status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
