import bcrypt
import jwt
from jwt import PyJWTError
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from .database import DatabaseService

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))  # 24 hours
        self.db_service = DatabaseService()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return {"username": username, "is_admin": payload.get("is_admin", False)}
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except PyJWTError as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        try:
            # Get user from database
            user = await self.db_service.get_user_by_username(username)
            if not user:
                logger.warning(f"User not found: {username}")
                return None
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            await self.db_service.update_last_login(username)
            
            # Create access token
            token_data = {
                "sub": username,
                "is_admin": user.get('is_admin', False)
            }
            access_token = self.create_access_token(token_data)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": user['username'],
                    "email": user.get('email'),
                    "is_admin": user.get('is_admin', False)
                }
            }
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def create_user(self, username: str, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create a new user account"""
        try:
            # Check if user already exists
            existing_user = await self.db_service.get_user_by_username(username)
            if existing_user:
                logger.warning(f"User already exists: {username}")
                return None
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user in database
            user = await self.db_service.create_user(username, email, password_hash)
            
            return {
                "username": user['username'],
                "email": user['email'],
                "is_admin": user.get('is_admin', False),
                "created_at": user['created_at']
            }
        
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return None
    
    async def verify_token_async(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token and return user info"""
        token_data = self.verify_token(token)
        if not token_data:
            return None
        
        # Get fresh user data from database
        user = await self.db_service.get_user_by_username(token_data['username'])
        if not user:
            return None
        
        return {
            "username": user['username'],
            "email": user.get('email'),
            "is_admin": user.get('is_admin', False)
        }
