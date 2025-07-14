from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import asyncio
import json
import os
from dotenv import load_dotenv
import hashlib
import jwt
import uuid
import logging
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KPA Form Data API",
    description="API for managing KPA (Key Performance Area) form data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/kpa_db")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-here")
JWT_ALGORITHM = "HS256"

# Pydantic models
class LoginRequest(BaseModel):
    phone_number: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None

class KPAFormData(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    designation: str
    performance_period: str
    kpa_title: str
    kpa_description: str
    target_value: float
    achieved_value: float
    weightage: float
    score: Optional[float] = None
    remarks: Optional[str] = None

class KPAFormResponse(BaseModel):
    success: bool
    message: str
    form_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class KPAFormListResponse(BaseModel):
    success: bool
    message: str
    data: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int

# Database connection pool
db_pool = None

async def init_db():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("Database connection pool created successfully")
        
        # Create tables if they don't exist
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    phone_number VARCHAR(15) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kpa_forms (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    employee_id VARCHAR(50) NOT NULL,
                    employee_name VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    designation VARCHAR(100) NOT NULL,
                    performance_period VARCHAR(50) NOT NULL,
                    kpa_title VARCHAR(200) NOT NULL,
                    kpa_description TEXT,
                    target_value DECIMAL(10,2) NOT NULL,
                    achieved_value DECIMAL(10,2) NOT NULL,
                    weightage DECIMAL(5,2) NOT NULL,
                    score DECIMAL(5,2),
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by UUID REFERENCES users(id)
                );
            """)
            
            # Insert default user for testing
            await conn.execute("""
                INSERT INTO users (phone_number, password_hash) 
                VALUES ($1, $2) 
                ON CONFLICT (phone_number) DO NOTHING;
            """, "7760873976", hashlib.sha256("to_share@123".encode()).hexdigest())
            
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

async def get_db():
    """Get database connection from pool"""
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database connection not initialized")
    return db_pool

# Authentication functions
def create_jwt_token(user_id: str, phone_number: str) -> tuple[str, datetime]:
    """Create JWT token for authenticated user"""
    expires_at = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "user_id": user_id,
        "phone_number": phone_number,
        "exp": expires_at
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = verify_jwt_token(credentials.credentials)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()

@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "KPA Form Data API is running"}

@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    User login endpoint
    
    Authenticates user with phone number and password
    Returns JWT token for subsequent API calls
    """
    try:
        db = await get_db()
        
        # Hash the provided password
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        
        # Check user credentials
        async with db.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, phone_number FROM users WHERE phone_number = $1 AND password_hash = $2",
                request.phone_number, password_hash
            )
            
            if not user:
                return LoginResponse(
                    success=False,
                    message="Invalid phone number or password"
                )
            
            # Generate JWT token
            token, expires_at = create_jwt_token(str(user['id']), user['phone_number'])
            
            return LoginResponse(
                success=True,
                message="Login successful",
                token=token,
                user_id=str(user['id']),
                expires_at=expires_at
            )
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/kpa/forms", response_model=KPAFormResponse, tags=["KPA Forms"])
async def create_kpa_form(
    form_data: KPAFormData,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create new KPA form
    
    Creates a new Key Performance Area form with the provided data
    Requires authentication token
    """
    try:
        db = await get_db()
        
        # Calculate score based on achieved vs target
        score = min((form_data.achieved_value / form_data.target_value) * form_data.weightage, form_data.weightage)
        
        async with db.acquire() as conn:
            # Insert new KPA form
            form_id = await conn.fetchval("""
                INSERT INTO kpa_forms (
                    employee_id, employee_name, department, designation, 
                    performance_period, kpa_title, kpa_description, 
                    target_value, achieved_value, weightage, score, remarks, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
            """, 
                form_data.employee_id, form_data.employee_name, form_data.department,
                form_data.designation, form_data.performance_period, form_data.kpa_title,
                form_data.kpa_description, form_data.target_value, form_data.achieved_value,
                form_data.weightage, score, form_data.remarks, current_user['user_id']
            )
            
            # Fetch the created form
            created_form = await conn.fetchrow(
                "SELECT * FROM kpa_forms WHERE id = $1", form_id
            )
            
            return KPAFormResponse(
                success=True,
                message="KPA form created successfully",
                form_id=str(form_id),
                data={
                    "id": str(created_form['id']),
                    "employee_id": created_form['employee_id'],
                    "employee_name": created_form['employee_name'],
                    "department": created_form['department'],
                    "designation": created_form['designation'],
                    "performance_period": created_form['performance_period'],
                    "kpa_title": created_form['kpa_title'],
                    "kpa_description": created_form['kpa_description'],
                    "target_value": float(created_form['target_value']),
                    "achieved_value": float(created_form['achieved_value']),
                    "weightage": float(created_form['weightage']),
                    "score": float(created_form['score']),
                    "remarks": created_form['remarks'],
                    "created_at": created_form['created_at'].isoformat(),
                    "updated_at": created_form['updated_at'].isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Create KPA form error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/kpa/forms", response_model=KPAFormListResponse, tags=["KPA Forms"])
async def get_kpa_forms(
    page: int = 1,
    limit: int = 10,
    employee_id: Optional[str] = None,
    department: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get KPA forms with pagination and filtering
    
    Retrieves list of KPA forms with optional filtering by employee_id and department
    Supports pagination with page and limit parameters
    Requires authentication token
    """
    try:
        db = await get_db()
        
        # Build query with optional filters
        base_query = "SELECT * FROM kpa_forms WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM kpa_forms WHERE 1=1"
        params = []
        param_count = 0
        
        if employee_id:
            param_count += 1
            base_query += f" AND employee_id = ${param_count}"
            count_query += f" AND employee_id = ${param_count}"
            params.append(employee_id)
            
        if department:
            param_count += 1
            base_query += f" AND department ILIKE ${param_count}"
            count_query += f" AND department ILIKE ${param_count}"
            params.append(f"%{department}%")
        
        # Add pagination
        offset = (page - 1) * limit
        base_query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        async with db.acquire() as conn:
            # Get total count
            total_count = await conn.fetchval(count_query, *params[:-2] if params else [])
            
            # Get forms
            forms = await conn.fetch(base_query, *params)
            
            # Format response data
            forms_data = []
            for form in forms:
                forms_data.append({
                    "id": str(form['id']),
                    "employee_id": form['employee_id'],
                    "employee_name": form['employee_name'],
                    "department": form['department'],
                    "designation": form['designation'],
                    "performance_period": form['performance_period'],
                    "kpa_title": form['kpa_title'],
                    "kpa_description": form['kpa_description'],
                    "target_value": float(form['target_value']),
                    "achieved_value": float(form['achieved_value']),
                    "weightage": float(form['weightage']),
                    "score": float(form['score']) if form['score'] else None,
                    "remarks": form['remarks'],
                    "created_at": form['created_at'].isoformat(),
                    "updated_at": form['updated_at'].isoformat()
                })
            
            return KPAFormListResponse(
                success=True,
                message="KPA forms retrieved successfully",
                data=forms_data,
                total_count=total_count,
                page=page,
                limit=limit
            )
            
    except Exception as e:
        logger.error(f"Get KPA forms error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/kpa/forms/{form_id}", response_model=KPAFormResponse, tags=["KPA Forms"])
async def get_kpa_form(
    form_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get specific KPA form by ID
    
    Retrieves detailed information about a specific KPA form
    Requires authentication token
    """
    try:
        db = await get_db()
        
        async with db.acquire() as conn:
            form = await conn.fetchrow(
                "SELECT * FROM kpa_forms WHERE id = $1", form_id
            )
            
            if not form:
                raise HTTPException(status_code=404, detail="KPA form not found")
            
            return KPAFormResponse(
                success=True,
                message="KPA form retrieved successfully",
                form_id=str(form['id']),
                data={
                    "id": str(form['id']),
                    "employee_id": form['employee_id'],
                    "employee_name": form['employee_name'],
                    "department": form['department'],
                    "designation": form['designation'],
                    "performance_period": form['performance_period'],
                    "kpa_title": form['kpa_title'],
                    "kpa_description": form['kpa_description'],
                    "target_value": float(form['target_value']),
                    "achieved_value": float(form['achieved_value']),
                    "weightage": float(form['weightage']),
                    "score": float(form['score']) if form['score'] else None,
                    "remarks": form['remarks'],
                    "created_at": form['created_at'].isoformat(),
                    "updated_at": form['updated_at'].isoformat()
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get KPA form error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)