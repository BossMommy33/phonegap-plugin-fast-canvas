from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from openai import OpenAI

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = "zeitgesteuerte-nachrichten-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Stripe
stripe_api_key = os.environ.get('STRIPE_API_KEY')

# OpenAI
openai_api_key = os.environ.get('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Background task flag
scheduler_running = False

# Subscription Plans
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Kostenlos",
        "price": 0.0,
        "monthly_messages": 5,
        "features": ["5 Nachrichten pro Monat", "Basis-Funktionen"]
    },
    "premium": {
        "name": "Premium",
        "price": 9.99,
        "monthly_messages": -1,  # unlimited
        "features": ["Unbegrenzte Nachrichten", "Wiederkehrende Nachrichten", "Erweiterte Zeitoptionen", "Export/Import"]
    },
    "business": {
        "name": "Business",
        "price": 29.99,
        "monthly_messages": -1,  # unlimited
        "features": ["Alles aus Premium", "Analytics Dashboard", "API-Zugang", "Priority Support"]
    }
}

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    hashed_password: str
    subscription_plan: str = "free"
    subscription_status: str = "active"  # active, cancelled, expired
    subscription_expires_at: Optional[datetime] = None
    monthly_message_count: int = 0
    monthly_message_reset: datetime = Field(default_factory=lambda: datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    subscription_plan: str
    subscription_status: str
    monthly_messages_used: int
    monthly_messages_limit: int
    features: List[str]

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Message Models (Enhanced)
class ScheduledMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    scheduled_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "scheduled"  # scheduled, delivered, failed
    delivered_at: Optional[datetime] = None
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None  # daily, weekly, monthly
    next_occurrence: Optional[datetime] = None

class ScheduledMessageCreate(BaseModel):
    title: str
    content: str
    scheduled_time: datetime
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None

class ScheduledMessageResponse(BaseModel):
    id: str
    title: str
    content: str
    scheduled_time: datetime
    created_at: datetime
    status: str
    delivered_at: Optional[datetime] = None
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None

# Payment Models
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    amount: float
    currency: str = "eur"
    subscription_plan: str
    payment_status: str = "pending"  # pending, completed, failed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Subscription Request
class SubscribeRequest(BaseModel):
    plan: str  # premium, business

# Utility Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

def get_user_response(user: User) -> UserResponse:
    plan = SUBSCRIPTION_PLANS.get(user.subscription_plan, SUBSCRIPTION_PLANS["free"])
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        subscription_plan=user.subscription_plan,
        subscription_status=user.subscription_status,
        monthly_messages_used=user.monthly_message_count,
        monthly_messages_limit=plan["monthly_messages"],
        features=plan["features"]
    )

async def check_message_limit(user: User) -> bool:
    """Check if user has reached their monthly message limit"""
    plan = SUBSCRIPTION_PLANS.get(user.subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    # Unlimited for premium plans
    if plan["monthly_messages"] == -1:
        return True
    
    # Reset monthly count if new month
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if user.monthly_message_reset < month_start:
        await db.users.update_one(
            {"id": user.id},
            {"$set": {
                "monthly_message_count": 0,
                "monthly_message_reset": month_start
            }}
        )
        user.monthly_message_count = 0
    
    return user.monthly_message_count < plan["monthly_messages"]

async def increment_message_count(user_id: str):
    """Increment user's monthly message count"""
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"monthly_message_count": 1}}
    )

def calculate_next_occurrence(scheduled_time: datetime, pattern: str) -> datetime:
    """Calculate next occurrence for recurring messages"""
    if pattern == "daily":
        return scheduled_time + timedelta(days=1)
    elif pattern == "weekly":
        return scheduled_time + timedelta(weeks=1)
    elif pattern == "monthly":
        # Add one month (approximately)
        if scheduled_time.month == 12:
            return scheduled_time.replace(year=scheduled_time.year + 1, month=1)
        else:
            return scheduled_time.replace(month=scheduled_time.month + 1)
    return scheduled_time

# Background scheduler function
async def message_scheduler():
    global scheduler_running
    scheduler_running = True
    logger.info("Message scheduler started")
    
    while scheduler_running:
        try:
            current_time = datetime.utcnow()
            
            # Find messages that are due for delivery
            due_messages = await db.scheduled_messages.find({
                "scheduled_time": {"$lte": current_time},
                "status": "scheduled"
            }).to_list(100)
            
            for message in due_messages:
                # Mark message as delivered
                await db.scheduled_messages.update_one(
                    {"id": message["id"]},
                    {
                        "$set": {
                            "status": "delivered",
                            "delivered_at": current_time
                        }
                    }
                )
                
                # Handle recurring messages
                if message.get("is_recurring") and message.get("recurring_pattern"):
                    next_time = calculate_next_occurrence(
                        message["scheduled_time"], 
                        message["recurring_pattern"]
                    )
                    
                    # Create next occurrence
                    new_message = ScheduledMessage(
                        user_id=message["user_id"],
                        title=message["title"],
                        content=message["content"],
                        scheduled_time=next_time,
                        is_recurring=True,
                        recurring_pattern=message["recurring_pattern"]
                    )
                    await db.scheduled_messages.insert_one(new_message.dict())
                
                logger.info(f"Delivered message: {message['title']}")
            
            # Sleep for 10 seconds before checking again
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in message scheduler: {e}")
            await asyncio.sleep(30)  # Wait longer on error

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application")
    # Start the background scheduler
    task = asyncio.create_task(message_scheduler())
    yield
    # Shutdown
    global scheduler_running
    scheduler_running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Background scheduler stopped")
    client.close()
    logger.info("Application shutdown complete")

# Create the main app
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Auth endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    
    await db.users.insert_one(new_user.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=get_user_response(new_user)
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_obj = User(**db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=get_user_response(user_obj)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return get_user_response(current_user)

# Subscription endpoints
@api_router.get("/subscriptions/plans")
async def get_subscription_plans():
    return SUBSCRIPTION_PLANS

@api_router.post("/subscriptions/subscribe")
async def create_subscription(
    request: SubscribeRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    if request.plan not in ["premium", "business"]:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    if current_user.subscription_plan == request.plan:
        raise HTTPException(status_code=400, detail="Already subscribed to this plan")
    
    plan = SUBSCRIPTION_PLANS[request.plan]
    
    # Initialize Stripe
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Create checkout session
    success_url = f"{str(http_request.base_url).rstrip('/')}/subscription-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{str(http_request.base_url).rstrip('/')}/subscription-cancelled"
    
    checkout_request = CheckoutSessionRequest(
        amount=plan["price"],
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user.id,
            "subscription_plan": request.plan,
            "type": "subscription"
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Store transaction
    transaction = PaymentTransaction(
        user_id=current_user.id,
        session_id=session.session_id,
        amount=plan["price"],
        subscription_plan=request.plan
    )
    await db.payment_transactions.insert_one(transaction.dict())
    
    return {"checkout_url": session.url, "session_id": session.session_id}

@api_router.get("/subscriptions/status/{session_id}")
async def get_subscription_status(session_id: str, current_user: User = Depends(get_current_user)):
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction and user if payment completed
    if status.payment_status == "paid":
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if transaction and transaction["payment_status"] != "completed":
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "payment_status": "completed",
                    "completed_at": datetime.utcnow()
                }}
            )
            
            # Update user subscription
            expires_at = datetime.utcnow() + timedelta(days=30)
            await db.users.update_one(
                {"id": current_user.id},
                {"$set": {
                    "subscription_plan": transaction["subscription_plan"],
                    "subscription_status": "active",
                    "subscription_expires_at": expires_at
                }}
            )
    
    return {
        "payment_status": status.payment_status,
        "status": status.status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

# Stripe webhook
@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    try:
        webhook_request_body = await request.body()
        stripe_signature = request.headers.get("Stripe-Signature")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(webhook_request_body, stripe_signature)
        
        if webhook_response.payment_status == "paid":
            # Find and update transaction
            transaction = await db.payment_transactions.find_one({"session_id": webhook_response.session_id})
            if transaction and transaction["payment_status"] != "completed":
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": "completed",
                        "completed_at": datetime.utcnow()
                    }}
                )
                
                # Update user subscription
                expires_at = datetime.utcnow() + timedelta(days=30)
                await db.users.update_one(
                    {"id": transaction["user_id"]},
                    {"$set": {
                        "subscription_plan": transaction["subscription_plan"],
                        "subscription_status": "active",
                        "subscription_expires_at": expires_at
                    }}
                )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Enhanced Message endpoints
@api_router.post("/messages", response_model=ScheduledMessageResponse)
async def create_scheduled_message(message: ScheduledMessageCreate, current_user: User = Depends(get_current_user)):
    # Check message limit
    if not await check_message_limit(current_user):
        raise HTTPException(
            status_code=403, 
            detail=f"Monthly message limit reached. Upgrade to Premium for unlimited messages."
        )
    
    # Check if recurring is allowed
    if message.is_recurring and current_user.subscription_plan == "free":
        raise HTTPException(
            status_code=403,
            detail="Recurring messages are only available for Premium and Business subscribers"
        )
    
    message_dict = message.dict()
    message_obj = ScheduledMessage(user_id=current_user.id, **message_dict)
    await db.scheduled_messages.insert_one(message_obj.dict())
    
    # Increment message count
    await increment_message_count(current_user.id)
    
    return ScheduledMessageResponse(**message_obj.dict())

@api_router.get("/messages", response_model=List[ScheduledMessageResponse])
async def get_scheduled_messages(current_user: User = Depends(get_current_user)):
    messages = await db.scheduled_messages.find({"user_id": current_user.id}).sort("scheduled_time", 1).to_list(1000)
    return [ScheduledMessageResponse(**message) for message in messages]

@api_router.get("/messages/delivered", response_model=List[ScheduledMessageResponse])
async def get_delivered_messages(current_user: User = Depends(get_current_user)):
    messages = await db.scheduled_messages.find({
        "user_id": current_user.id,
        "status": "delivered"
    }).sort("delivered_at", -1).to_list(1000)
    return [ScheduledMessageResponse(**message) for message in messages]

@api_router.get("/messages/scheduled", response_model=List[ScheduledMessageResponse])
async def get_pending_messages(current_user: User = Depends(get_current_user)):
    messages = await db.scheduled_messages.find({
        "user_id": current_user.id,
        "status": "scheduled"
    }).sort("scheduled_time", 1).to_list(1000)
    return [ScheduledMessageResponse(**message) for message in messages]

@api_router.delete("/messages/{message_id}")
async def delete_message(message_id: str, current_user: User = Depends(get_current_user)):
    result = await db.scheduled_messages.delete_one({"id": message_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}

# Analytics (Business only)
@api_router.get("/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    if current_user.subscription_plan != "business":
        raise HTTPException(status_code=403, detail="Analytics are only available for Business subscribers")
    
    # Get message stats
    total_messages = await db.scheduled_messages.count_documents({"user_id": current_user.id})
    delivered_messages = await db.scheduled_messages.count_documents({
        "user_id": current_user.id,
        "status": "delivered"
    })
    scheduled_messages = await db.scheduled_messages.count_documents({
        "user_id": current_user.id,
        "status": "scheduled"
    })
    
    # Get monthly stats
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_messages = await db.scheduled_messages.count_documents({
        "user_id": current_user.id,
        "created_at": {"$gte": month_start}
    })
    
    return {
        "total_messages": total_messages,
        "delivered_messages": delivered_messages,
        "scheduled_messages": scheduled_messages,
        "monthly_messages": monthly_messages,
        "subscription_plan": current_user.subscription_plan,
        "subscription_status": current_user.subscription_status
    }

@api_router.get("/")
async def root():
    return {"message": "Zeitgesteuerte Nachrichten API - Premium Edition"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)