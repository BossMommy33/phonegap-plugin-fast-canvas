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
from emergentintegrations.llm.chat import LlmChat, UserMessage

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
openai_client = None
if openai_api_key:
    try:
        openai_client = LlmChat(
            api_key=openai_api_key,
            session_id="default",
            system_message="You are a helpful assistant that generates German messages."
        )
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        openai_client = None

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
    referral_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    hashed_password: str
    role: str = "user"  # user, admin
    subscription_plan: str = "free"
    subscription_status: str = "active"  # active, cancelled, expired
    subscription_expires_at: Optional[datetime] = None
    monthly_message_count: int = 0
    monthly_message_reset: datetime = Field(default_factory=lambda: datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    referral_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    referred_by: Optional[str] = None  # referral code of referrer
    referral_bonus_used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    subscription_plan: str
    subscription_status: str
    monthly_messages_used: int
    monthly_messages_limit: int
    features: List[str]
    referral_code: str
    referred_count: int = 0

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
    delivered_at: Optional[datetime] = None
    status: str = "scheduled"  # scheduled, delivered, failed
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None
    
    # Email Delivery Fields
    recipients: List[dict] = []  # [{"email": "test@example.com", "name": "Test User", "type": "contact"}]
    delivery_method: str = "in_app"  # in_app, email, sms, both
    email_subject: Optional[str] = None
    sender_email: Optional[str] = None
    
    # Contact Integration
    selected_contacts: List[str] = []  # List of contact IDs
    selected_contact_lists: List[str] = []  # List of contact list IDs
    
    # Delivery Tracking
    total_recipients: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    opened_count: int = 0
    delivery_errors: List[str] = []

class ScheduledMessageCreate(BaseModel):
    title: str
    content: str
    scheduled_time: datetime
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None
    
    # Email Delivery Fields
    delivery_method: str = "in_app"  # in_app, email, sms, both
    email_subject: Optional[str] = None
    recipients: List[dict] = []  # Direct recipients
    selected_contacts: List[str] = []  # Contact IDs
    selected_contact_lists: List[str] = []  # Contact list IDs

# Enhanced Messaging Models
class BulkMessageCreate(BaseModel):
    messages: List[ScheduledMessageCreate]
    time_interval: int = 5  # minutes between each message

class MessageTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    title: str
    content: str
    category: str = "general"  # general, business, personal, marketing
    is_public: bool = False  # If true, available to all users
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageTemplateCreate(BaseModel):
    name: str
    title: str
    content: str
    category: str = "general"
    is_public: bool = False

class BulkMessageResponse(BaseModel):
    success_count: int
    failed_count: int
    created_messages: List[str]  # List of message IDs
    errors: List[str]

# AI Models
class AIGenerateRequest(BaseModel):
    prompt: str
    tone: Optional[str] = "freundlich"  # freundlich, professionell, humorvoll
    occasion: Optional[str] = None  # meeting, geburtstag, erinnerung, etc.

class AIEnhanceRequest(BaseModel):
    text: str
    action: str  # improve, correct, shorten, lengthen, translate
    target_language: Optional[str] = "deutsch"
    tone: Optional[str] = "freundlich"

class AIResponse(BaseModel):
    generated_text: str
    success: bool
    error: Optional[str] = None

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

# Marketing Automation Models
class MarketingCampaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # email, social_media, push_notification
    target_audience: str  # all_users, free_users, premium_users, new_users
    content: dict
    schedule_type: str = "immediate"  # immediate, scheduled, triggered
    scheduled_time: Optional[datetime] = None
    trigger_event: Optional[str] = None  # registration, first_message, subscription_upgrade
    status: str = "draft"  # draft, active, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0

# Contact Management Models
class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    contact_type: str = "personal"  # personal, business, family
    company: Optional[str] = None
    position: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_contacted: Optional[datetime] = None

class ContactList(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    list_type: str = "personal"  # personal, business, family, custom
    contacts: List[str] = []  # List of contact IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_default: bool = False

class EmailDelivery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4))
    message_id: str
    user_id: str
    recipient_email: str
    recipient_name: str
    subject: str
    content: str
    delivery_status: str = "pending"  # pending, sent, delivered, failed, opened, clicked
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    error_message: Optional[str] = None
    provider: str = "sendgrid"  # sendgrid, smtp
    provider_message_id: Optional[str] = None

class ContactCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    contact_type: str = "personal"
    company: Optional[str] = None
    position: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []

class ContactListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    list_type: str = "personal"

class MarketingTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # email, social_post, push_notification
    subject: Optional[str] = None
    content: str
    variables: List[str] = []  # List of template variables like {{first_name}}
    category: str = "general"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0

class SocialMediaPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str  # twitter, linkedin, facebook, instagram
    content: str
    media_urls: List[str] = []
    hashtags: List[str] = []
    scheduled_time: Optional[datetime] = None
    status: str = "draft"  # draft, scheduled, published
    engagement_stats: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LaunchMetrics(BaseModel):
    date: datetime = Field(default_factory=datetime.utcnow)
    new_registrations: int = 0
    premium_conversions: int = 0
    social_engagement: int = 0
    referral_signups: int = 0
    daily_active_users: int = 0
    email_opens: int = 0
    campaign_clicks: int = 0

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

# Admin Models
class AdminStats(BaseModel):
    total_users: int
    premium_users: int
    business_users: int
    total_revenue: float
    monthly_revenue: float
    messages_sent_today: int
    messages_sent_month: int
    available_balance: float
    pending_payouts: float

class PayoutRequest(BaseModel):
    amount: float
    description: str = "Admin payout request"

class PayoutRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_user_id: str
    amount: float
    description: str
    status: str = "pending"  # pending, completed, failed
    stripe_payout_id: Optional[str] = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Advanced Analytics Models
class UserAnalytics(BaseModel):
    registration_trends: List[dict]
    subscription_conversion_rate: float
    user_retention_rate: float
    top_referrers: List[dict]
    user_activity_heatmap: List[dict]

class MessageAnalytics(BaseModel):
    creation_patterns: List[dict]
    delivery_success_rate: float
    popular_times: List[dict]
    message_type_distribution: List[dict]
    recurring_vs_oneshot: dict

class RevenueAnalytics(BaseModel):
    mrr_trend: List[dict]  # Monthly Recurring Revenue
    arpu: float  # Average Revenue Per User
    churn_rate: float
    subscription_growth_rate: float
    revenue_by_plan: List[dict]

class AIAnalytics(BaseModel):
    feature_usage: List[dict]
    generation_success_rate: float
    popular_prompts: List[dict]
    enhancement_types: List[dict]
    ai_adoption_rate: float

class AdvancedAnalytics(BaseModel):
    user_analytics: UserAnalytics
    message_analytics: MessageAnalytics
    revenue_analytics: RevenueAnalytics
    ai_analytics: AIAnalytics
    generated_at: datetime = Field(default_factory=datetime.utcnow)

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

async def get_user_response(user: User) -> UserResponse:
    plan = SUBSCRIPTION_PLANS.get(user.subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    # Count referrals
    referred_count = await db.users.count_documents({"referred_by": user.referral_code})
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        subscription_plan=user.subscription_plan,
        subscription_status=user.subscription_status,
        monthly_messages_used=user.monthly_message_count,
        monthly_messages_limit=plan["monthly_messages"],
        features=plan["features"],
        referral_code=user.referral_code,
        referred_count=referred_count
    )

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user and verify admin role"""
    user = await get_current_user(credentials)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

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

# AI Service Functions
async def generate_message_with_ai(prompt: str, tone: str = "freundlich", occasion: str = None) -> str:
    """Generate message content using OpenAI"""
    if not openai_client:
        # Return mock response for testing when OpenAI is not available
        tone_examples = {
            "freundlich": "Hallo! 😊 Hier ist eine freundliche Nachricht basierend auf Ihrem Prompt: '{}'",
            "professionell": "Sehr geehrte Damen und Herren, hiermit möchte ich Sie bezüglich '{}' informieren.",
            "humorvoll": "Hey! 😄 Hier ist eine lustige Nachricht zu: '{}' - hoffentlich bringt sie Sie zum Lächeln!"
        }
        
        occasion_examples = {
            "meeting": "📅 Meeting-Erinnerung: {}",
            "geburtstag": "🎉 Herzlichen Glückwunsch! {}",
            "termin": "⏰ Terminerinnerung: {}",
            "zahlung": "💰 Freundliche Zahlungserinnerung: {}",
            "event": "🎊 Einladung: {}"
        }
        
        if occasion and occasion in occasion_examples:
            return occasion_examples[occasion].format(prompt)
        elif tone in tone_examples:
            return tone_examples[tone].format(prompt)
        else:
            return f"📝 Generierte Nachricht: {prompt} (Ton: {tone})"
    
    try:
        # Build the system prompt based on tone and occasion
        tone_instructions = {
            "freundlich": "in einem freundlichen und warmen Ton",
            "professionell": "in einem professionellen und geschäftsmäßigen Ton",
            "humorvoll": "in einem humorvollen und lockeren Ton",
            "höflich": "in einem höflichen und respektvollen Ton"
        }
        
        occasion_context = {
            "meeting": "für eine Meeting-Erinnerung",
            "geburtstag": "für eine Geburtstagsnachricht",
            "erinnerung": "für eine allgemeine Erinnerung",
            "zahlung": "für eine höfliche Zahlungserinnerung",
            "termin": "für eine Terminerinnerung",
            "event": "für eine Veranstaltungseinladung"
        }
        
        system_prompt = f"""Du bist ein Assistent, der personalisierte Nachrichten erstellt. 
        Erstelle eine Nachricht auf Deutsch {tone_instructions.get(tone, 'in einem freundlichen Ton')}.
        
        {f'Kontext: Die Nachricht ist {occasion_context.get(occasion, "für einen allgemeinen Zweck")}.' if occasion else ''}
        
        Halte die Nachricht präzise aber herzlich. Verwende angemessene Emojis wenn passend.
        Antworte nur mit der Nachricht selbst, ohne zusätzliche Erklärungen."""
        
        # Create a new client instance with the system prompt
        ai_client = LlmChat(
            api_key=openai_api_key,
            session_id=f"generate_{uuid.uuid4().hex[:8]}",
            system_message=system_prompt
        )
        
        # Send the user message
        user_message = UserMessage(text=prompt)
        response = await ai_client.send_message(user_message)
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail="AI-Generierung fehlgeschlagen")

async def enhance_message_with_ai(text: str, action: str, tone: str = "freundlich", target_language: str = "deutsch") -> str:
    """Enhance existing message content using OpenAI"""
    if not openai_client:
        # Return mock enhanced response for testing when OpenAI is not available
        action_examples = {
            "improve": f"✨ Verbesserte Version: {text} - Jetzt noch ansprechender und {tone}er!",
            "correct": f"✅ Korrigierte Version: {text.replace('halo', 'hallo').replace('hofe', 'hoffe')}",
            "shorten": f"📝 Kurze Version: {text[:50]}..." if len(text) > 50 else f"📝 {text}",
            "lengthen": f"📖 Erweiterte Version: {text} Zusätzlich möchte ich hinzufügen, dass dies eine wichtige Angelegenheit ist, die Ihre Aufmerksamkeit verdient.",
            "translate": f"🌍 Übersetzt: {text} (simulierte Übersetzung)",
            "professional": f"💼 Professionelle Version: Sehr geehrte Damen und Herren, {text}",
            "friendly": f"😊 Freundliche Version: Hallo! {text} Ich hoffe, es geht Ihnen gut!"
        }
        
        return action_examples.get(action, f"🔧 Bearbeitete Version ({action}): {text}")
    
    try:
        action_prompts = {
            "improve": f"Verbessere diesen Text und mache ihn ansprechender in einem {tone}en Ton:",
            "correct": "Korrigiere Rechtschreibung und Grammatik in diesem Text:",
            "shorten": "Kürze diesen Text auf das Wesentliche:",
            "lengthen": f"Erweitere diesen Text mit mehr Details in einem {tone}en Ton:",
            "translate": f"Übersetze diesen Text ins {target_language.capitalize()}:",
            "professional": "Formuliere diesen Text professioneller um:",
            "friendly": "Formuliere diesen Text freundlicher um:"
        }
        
        system_prompt = f"""Du bist ein Textbearbeitungs-Assistent. 
        {action_prompts.get(action, 'Verbessere diesen Text:')}
        
        Antworte nur mit dem bearbeiteten Text, ohne zusätzliche Erklärungen."""
        
        # Create a new client instance with the system prompt
        ai_client = LlmChat(
            api_key=openai_api_key,
            session_id=f"enhance_{uuid.uuid4().hex[:8]}",
            system_message=system_prompt
        )
        
        # Send the user message
        user_message = UserMessage(text=text)
        response = await ai_client.send_message(user_message)
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"AI enhancement error: {e}")
        raise HTTPException(status_code=500, detail="AI-Verbesserung fehlgeschlagen")

async def get_message_suggestions(user_plan: str) -> List[dict]:
    """Get AI-powered message suggestions based on user plan"""
    base_suggestions = [
        {"prompt": "Erstelle eine Meeting-Erinnerung für morgen 14:00", "occasion": "meeting", "tone": "professionell"},
        {"prompt": "Schreibe eine Geburtstagsnachricht für einen Freund", "occasion": "geburtstag", "tone": "freundlich"},
        {"prompt": "Erstelle eine Terminerinnerung für den Zahnarzt", "occasion": "termin", "tone": "freundlich"},
    ]
    
    if user_plan in ["premium", "business"]:
        base_suggestions.extend([
            {"prompt": "Formuliere eine höfliche Zahlungserinnerung", "occasion": "zahlung", "tone": "höflich"},
            {"prompt": "Erstelle eine Einladung zu unserem Team-Event", "occasion": "event", "tone": "humorvoll"},
            {"prompt": "Schreibe eine Projektstatus-Erinnerung", "occasion": "meeting", "tone": "professionell"},
        ])
    
    if user_plan == "business":
        base_suggestions.extend([
            {"prompt": "Erstelle eine Kundentermin-Bestätigung", "occasion": "termin", "tone": "professionell"},
            {"prompt": "Formuliere eine Folge-Erinnerung nach Meeting", "occasion": "meeting", "tone": "professionell"},
        ])
    
    return base_suggestions

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
    
    # Validate referral code if provided
    referrer = None
    if user.referral_code:
        referrer = await db.users.find_one({"referral_code": user.referral_code.upper()})
        if not referrer:
            raise HTTPException(status_code=400, detail="Ungültiger Referral-Code")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    
    # Make admin@zeitgesteuerte.de an admin user
    role = "admin" if user.email == "admin@zeitgesteuerte.de" else "user"
    
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=role,
        referred_by=user.referral_code.upper() if user.referral_code else None
    )
    
    await db.users.insert_one(new_user.dict())
    
    # Give referral bonus (bonus messages) if referred
    if referrer:
        await db.users.update_one(
            {"id": referrer["id"]},
            {"$inc": {"monthly_message_count": -5}}  # Give 5 bonus messages
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=await get_user_response(new_user)
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
        user=await get_user_response(user_obj)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return await get_user_response(current_user)

@api_router.get("/auth/referrals")
async def get_user_referrals(current_user: User = Depends(get_current_user)):
    """Get user's referral statistics"""
    try:
        # Get referred users
        referred_users = await db.users.find(
            {"referred_by": current_user.referral_code},
            {"name": 1, "email": 1, "subscription_plan": 1, "created_at": 1, "_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        # Calculate bonus messages earned
        bonus_messages = len(referred_users) * 5
        
        return {
            "referral_code": current_user.referral_code,
            "total_referrals": len(referred_users),
            "bonus_messages_earned": bonus_messages,
            "referred_users": referred_users,
            "referral_link": f"https://39f27297-0805-40a9-a015-5c2e4d6584e8.preview.emergentagent.com?ref={current_user.referral_code}"
        }
    except Exception as e:
        logger.error(f"Error getting referrals: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Referrals")

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

# AI endpoints
@api_router.post("/ai/generate", response_model=AIResponse)
async def generate_message(request: AIGenerateRequest, current_user: User = Depends(get_current_user)):
    """Generate message content using AI"""
    try:
        generated_text = await generate_message_with_ai(
            request.prompt, 
            request.tone, 
            request.occasion
        )
        
        return AIResponse(
            generated_text=generated_text,
            success=True
        )
    except HTTPException as e:
        return AIResponse(
            generated_text="",
            success=False,
            error=e.detail
        )
    except Exception as e:
        return AIResponse(
            generated_text="",
            success=False,
            error="AI-Generierung fehlgeschlagen"
        )

@api_router.post("/ai/enhance", response_model=AIResponse)
async def enhance_message(request: AIEnhanceRequest, current_user: User = Depends(get_current_user)):
    """Enhance existing message content using AI"""
    try:
        enhanced_text = await enhance_message_with_ai(
            request.text,
            request.action,
            request.tone,
            request.target_language
        )
        
        return AIResponse(
            generated_text=enhanced_text,
            success=True
        )
    except HTTPException as e:
        return AIResponse(
            generated_text="",
            success=False,
            error=e.detail
        )
    except Exception as e:
        return AIResponse(
            generated_text="",
            success=False,
            error="AI-Verbesserung fehlgeschlagen"
        )

@api_router.get("/ai/suggestions")
async def get_ai_suggestions(current_user: User = Depends(get_current_user)):
    """Get AI-powered message suggestions based on user plan"""
    suggestions = await get_message_suggestions(current_user.subscription_plan)
    return {"suggestions": suggestions, "ai_available": openai_client is not None}

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
    
    try:
        # Process recipients from contacts and contact lists
        all_recipients = []
        
        # Add direct recipients
        all_recipients.extend(message.recipients)
        
        # Add recipients from selected contacts
        if message.selected_contacts:
            contacts = await db.contacts.find({
                "user_id": current_user.id,
                "id": {"$in": message.selected_contacts}
            }, {"_id": 0}).to_list(1000)
            
            for contact in contacts:
                all_recipients.append({
                    "email": contact["email"],
                    "name": contact["name"],
                    "type": "contact",
                    "contact_id": contact["id"]
                })
        
        # Add recipients from contact lists
        if message.selected_contact_lists:
            contact_lists = await db.contact_lists.find({
                "user_id": current_user.id,
                "id": {"$in": message.selected_contact_lists}
            }, {"_id": 0}).to_list(1000)
            
            for contact_list in contact_lists:
                if contact_list.get("contacts"):
                    list_contacts = await db.contacts.find({
                        "user_id": current_user.id,
                        "id": {"$in": contact_list["contacts"]}
                    }, {"_id": 0}).to_list(1000)
                    
                    for contact in list_contacts:
                        # Avoid duplicates
                        if not any(r.get("email") == contact["email"] for r in all_recipients):
                            all_recipients.append({
                                "email": contact["email"],
                                "name": contact["name"],
                                "type": "contact_list",
                                "contact_id": contact["id"],
                                "list_id": contact_list["id"],
                                "list_name": contact_list["name"]
                            })
        
        # Create the message with enhanced fields
        message_dict = message.dict()
        message_obj = ScheduledMessage(
            user_id=current_user.id,
            delivery_method=message.delivery_method,
            email_subject=message.email_subject or message.title,
            recipients=all_recipients,
            selected_contacts=message.selected_contacts,
            selected_contact_lists=message.selected_contact_lists,
            total_recipients=len(all_recipients),
            sender_email=current_user.email,
            **{k: v for k, v in message_dict.items() if k not in ['delivery_method', 'email_subject', 'recipients', 'selected_contacts', 'selected_contact_lists']}
        )
        
        await db.scheduled_messages.insert_one(message_obj.dict())
        
        # Increment message count
        await increment_message_count(current_user.id)
        
        # If delivery method includes email, create email delivery records
        if message.delivery_method in ["email", "both"] and all_recipients:
            await create_email_delivery_records(message_obj, current_user)
        
        return ScheduledMessageResponse(**message_obj.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Error creating message")

# Helper function to create email delivery records
async def create_email_delivery_records(message: ScheduledMessage, user: User):
    """Create email delivery records for tracking"""
    try:
        delivery_records = []
        
        for recipient in message.recipients:
            delivery_record = EmailDelivery(
                message_id=message.id,
                user_id=user.id,
                recipient_email=recipient["email"],
                recipient_name=recipient["name"],
                subject=message.email_subject,
                content=f"{message.title}\n\n{message.content}",
                delivery_status="pending"
            )
            delivery_records.append(delivery_record.dict())
        
        if delivery_records:
            await db.email_deliveries.insert_many(delivery_records)
            
    except Exception as e:
        logger.error(f"Error creating email delivery records: {e}")

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

# Enhanced Messaging Features
@api_router.post("/messages/bulk", response_model=BulkMessageResponse)
async def create_bulk_messages(bulk_request: BulkMessageCreate, current_user: User = Depends(get_current_user)):
    """Create multiple messages at once with time intervals"""
    if current_user.subscription_plan == "free":
        raise HTTPException(status_code=403, detail="Bulk messages are only available for Premium and Business subscribers")
    
    created_messages = []
    errors = []
    success_count = 0
    failed_count = 0
    
    try:
        # Check if user has enough message quota
        if not await check_message_limit(current_user):
            remaining_messages = SUBSCRIPTION_PLANS[current_user.subscription_plan]["monthly_messages"] - current_user.monthly_message_count
            if remaining_messages < len(bulk_request.messages):
                raise HTTPException(
                    status_code=403,
                    detail=f"Not enough messages remaining. You can create {remaining_messages} more messages this month."
                )
        
        base_time = datetime.utcnow()
        
        for i, message_data in enumerate(bulk_request.messages):
            try:
                # Calculate scheduled time with interval
                scheduled_time = message_data.scheduled_time + timedelta(minutes=i * bulk_request.time_interval)
                
                # Create message
                message_obj = ScheduledMessage(
                    user_id=current_user.id,
                    title=message_data.title,
                    content=message_data.content,
                    scheduled_time=scheduled_time,
                    is_recurring=message_data.is_recurring,
                    recurring_pattern=message_data.recurring_pattern
                )
                
                await db.scheduled_messages.insert_one(message_obj.dict())
                await increment_message_count(current_user.id)
                
                created_messages.append(message_obj.id)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Message {i+1}: {str(e)}")
                failed_count += 1
        
        return BulkMessageResponse(
            success_count=success_count,
            failed_count=failed_count,
            created_messages=created_messages,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk messages: {e}")
        raise HTTPException(status_code=500, detail="Error creating bulk messages")

@api_router.get("/templates")
async def get_message_templates(current_user: User = Depends(get_current_user)):
    """Get user's message templates and public templates"""
    try:
        # Get user's private templates (exclude MongoDB _id field)
        user_templates = await db.message_templates.find(
            {"user_id": current_user.id}, 
            {"_id": 0}
        ).sort("created_at", -1).to_list(1000)
        
        # Get public templates (created by other users and marked as public)
        public_templates = await db.message_templates.find({
            "is_public": True,
            "user_id": {"$ne": current_user.id}
        }, {"_id": 0}).sort("usage_count", -1).to_list(50)
        
        return {
            "user_templates": user_templates,
            "public_templates": public_templates
        }
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail="Error loading message templates")

@api_router.post("/templates", response_model=MessageTemplate)
async def create_message_template(template: MessageTemplateCreate, current_user: User = Depends(get_current_user)):
    """Create a new message template"""
    try:
        template_obj = MessageTemplate(
            user_id=current_user.id,
            name=template.name,
            title=template.title,
            content=template.content,
            category=template.category,
            is_public=template.is_public
        )
        
        await db.message_templates.insert_one(template_obj.dict())
        return template_obj
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Error creating message template")

@api_router.put("/templates/{template_id}")
async def update_message_template(
    template_id: str, 
    template_update: MessageTemplateCreate, 
    current_user: User = Depends(get_current_user)
):
    """Update a message template (only template owner can update)"""
    try:
        # Check if template exists and belongs to user
        existing_template = await db.message_templates.find_one({"id": template_id, "user_id": current_user.id})
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update template
        await db.message_templates.update_one(
            {"id": template_id, "user_id": current_user.id},
            {"$set": {
                "name": template_update.name,
                "title": template_update.title,
                "content": template_update.content,
                "category": template_update.category,
                "is_public": template_update.is_public
            }}
        )
        
        return {"message": "Template updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail="Error updating template")

@api_router.delete("/templates/{template_id}")
async def delete_message_template(template_id: str, current_user: User = Depends(get_current_user)):
    """Delete a message template"""
    try:
        result = await db.message_templates.delete_one({"id": template_id, "user_id": current_user.id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail="Error deleting template")

@api_router.post("/templates/{template_id}/use")
async def use_message_template(template_id: str, current_user: User = Depends(get_current_user)):
    """Use a template (increment usage count and return template data)"""
    try:
        # Check if template exists (either user's own or public)
        template = await db.message_templates.find_one({
            "$or": [
                {"id": template_id, "user_id": current_user.id},
                {"id": template_id, "is_public": True}
            ]
        })
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Increment usage count
        await db.message_templates.update_one(
            {"id": template_id},
            {"$inc": {"usage_count": 1}}
        )
        
        return {
            "id": template["id"],
            "name": template["name"],
            "title": template["title"],
            "content": template["content"],
            "category": template["category"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error using template: {e}")
        raise HTTPException(status_code=500, detail="Error using template")

# Calendar Integration
@api_router.get("/messages/calendar/{year}/{month}")
async def get_calendar_messages(year: int, month: int, current_user: User = Depends(get_current_user)):
    """Get messages for a specific month for calendar view"""
    try:
        # Create date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Get messages in date range
        messages = await db.scheduled_messages.find({
            "user_id": current_user.id,
            "scheduled_time": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).sort("scheduled_time", 1).to_list(1000)
        
        # Group messages by day
        calendar_data = {}
        for message in messages:
            day = message["scheduled_time"].day
            if day not in calendar_data:
                calendar_data[day] = []
            
            calendar_data[day].append({
                "id": message["id"],
                "title": message["title"],
                "scheduled_time": message["scheduled_time"],
                "status": message["status"],
                "is_recurring": message.get("is_recurring", False)
            })
        
        return {
            "year": year,
            "month": month,
            "calendar_data": calendar_data
        }
        
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        raise HTTPException(status_code=500, detail="Error loading calendar data")

# Contact Management Endpoints
@api_router.get("/contacts")
async def get_contacts(current_user: User = Depends(get_current_user)):
    """Get user's contacts"""
    try:
        contacts = await db.contacts.find({"user_id": current_user.id}, {"_id": 0}).sort("name", 1).to_list(1000)
        return {"contacts": contacts}
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail="Error loading contacts")

@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact: ContactCreate, current_user: User = Depends(get_current_user)):
    """Create a new contact"""
    try:
        # Check if contact with this email already exists for this user
        existing_contact = await db.contacts.find_one({
            "user_id": current_user.id,
            "email": contact.email
        })
        
        if existing_contact:
            raise HTTPException(status_code=400, detail="Contact with this email already exists")
        
        contact_obj = Contact(
            user_id=current_user.id,
            **contact.dict()
        )
        
        await db.contacts.insert_one(contact_obj.dict())
        return contact_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail="Error creating contact")

@api_router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact_update: ContactCreate, current_user: User = Depends(get_current_user)):
    """Update a contact"""
    try:
        result = await db.contacts.update_one(
            {"id": contact_id, "user_id": current_user.id},
            {"$set": contact_update.dict()}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return {"message": "Contact updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        raise HTTPException(status_code=500, detail="Error updating contact")

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    """Delete a contact"""
    try:
        result = await db.contacts.delete_one({"id": contact_id, "user_id": current_user.id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return {"message": "Contact deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise HTTPException(status_code=500, detail="Error deleting contact")

@api_router.get("/contact-lists")
async def get_contact_lists(current_user: User = Depends(get_current_user)):
    """Get user's contact lists"""
    try:
        # Get contact lists with contact count
        lists = await db.contact_lists.find({"user_id": current_user.id}, {"_id": 0}).sort("name", 1).to_list(1000)
        
        # Add contact count to each list
        for contact_list in lists:
            contact_list["contact_count"] = len(contact_list.get("contacts", []))
        
        return {"contact_lists": lists}
    except Exception as e:
        logger.error(f"Error getting contact lists: {e}")
        raise HTTPException(status_code=500, detail="Error loading contact lists")

@api_router.post("/contact-lists", response_model=ContactList)
async def create_contact_list(contact_list: ContactListCreate, current_user: User = Depends(get_current_user)):
    """Create a new contact list"""
    try:
        contact_list_obj = ContactList(
            user_id=current_user.id,
            **contact_list.dict()
        )
        
        await db.contact_lists.insert_one(contact_list_obj.dict())
        return contact_list_obj
        
    except Exception as e:
        logger.error(f"Error creating contact list: {e}")
        raise HTTPException(status_code=500, detail="Error creating contact list")

@api_router.put("/contact-lists/{list_id}/contacts")
async def update_contact_list_contacts(
    list_id: str, 
    contact_ids: List[str], 
    current_user: User = Depends(get_current_user)
):
    """Add/remove contacts from a contact list"""
    try:
        # Verify all contact IDs belong to the user
        user_contacts = await db.contacts.find(
            {"user_id": current_user.id, "id": {"$in": contact_ids}}, 
            {"id": 1}
        ).to_list(1000)
        
        valid_contact_ids = [c["id"] for c in user_contacts]
        
        result = await db.contact_lists.update_one(
            {"id": list_id, "user_id": current_user.id},
            {"$set": {"contacts": valid_contact_ids}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Contact list not found")
        
        return {"message": f"Contact list updated with {len(valid_contact_ids)} contacts"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact list: {e}")
        raise HTTPException(status_code=500, detail="Error updating contact list")

@api_router.delete("/contact-lists/{list_id}")
async def delete_contact_list(list_id: str, current_user: User = Depends(get_current_user)):
    """Delete a contact list"""
    try:
        result = await db.contact_lists.delete_one({"id": list_id, "user_id": current_user.id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contact list not found")
        
        return {"message": "Contact list deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact list: {e}")
        raise HTTPException(status_code=500, detail="Error deleting contact list")

# Initialize default contact lists for new users
async def initialize_default_contact_lists(user_id: str):
    """Create default contact lists for new users"""
    try:
        default_lists = [
            {
                "name": "Freunde & Familie",
                "description": "Persönliche Kontakte für private Nachrichten",
                "list_type": "personal",
                "is_default": True
            },
            {
                "name": "Geschäftskontakte",
                "description": "Berufliche Kontakte und Unternehmen",
                "list_type": "business",
                "is_default": True
            },
            {
                "name": "VIP-Kontakte",
                "description": "Wichtige Kontakte mit hoher Priorität",
                "list_type": "custom",
                "is_default": False
            }
        ]
        
        for list_data in default_lists:
            contact_list = ContactList(
                user_id=user_id,
                **list_data
            )
            await db.contact_lists.insert_one(contact_list.dict())
            
    except Exception as e:
        logger.error(f"Error initializing default contact lists: {e}")

# Marketing Automation Endpoints (Admin only)
@api_router.get("/admin/marketing/campaigns")
async def get_marketing_campaigns(current_admin: User = Depends(get_current_admin)):
    """Get all marketing campaigns"""
    try:
        campaigns = await db.marketing_campaigns.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return {"campaigns": campaigns}
    except Exception as e:
        logger.error(f"Error getting marketing campaigns: {e}")
        raise HTTPException(status_code=500, detail="Error loading marketing campaigns")

@api_router.post("/admin/marketing/campaigns", response_model=MarketingCampaign)
async def create_marketing_campaign(campaign: MarketingCampaign, current_admin: User = Depends(get_current_admin)):
    """Create a new marketing campaign"""
    try:
        campaign_dict = campaign.dict()
        await db.marketing_campaigns.insert_one(campaign_dict)
        return campaign
    except Exception as e:
        logger.error(f"Error creating marketing campaign: {e}")
        raise HTTPException(status_code=500, detail="Error creating marketing campaign")

@api_router.get("/admin/marketing/templates")
async def get_marketing_templates(current_admin: User = Depends(get_current_admin)):
    """Get all marketing templates"""
    try:
        # Load predefined templates from marketing materials
        predefined_templates = await load_predefined_marketing_templates()
        
        # Get custom templates from database
        custom_templates = await db.marketing_templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        
        return {
            "predefined_templates": predefined_templates,
            "custom_templates": custom_templates
        }
    except Exception as e:
        logger.error(f"Error getting marketing templates: {e}")
        raise HTTPException(status_code=500, detail="Error loading marketing templates")

@api_router.post("/admin/marketing/templates", response_model=MarketingTemplate)
async def create_marketing_template(template: MarketingTemplate, current_admin: User = Depends(get_current_admin)):
    """Create a new marketing template"""
    try:
        template_dict = template.dict()
        await db.marketing_templates.insert_one(template_dict)
        return template
    except Exception as e:
        logger.error(f"Error creating marketing template: {e}")
        raise HTTPException(status_code=500, detail="Error creating marketing template")

@api_router.get("/admin/marketing/social-posts")
async def get_social_media_posts(current_admin: User = Depends(get_current_admin)):
    """Get all social media posts"""
    try:
        # Load ready-to-use social media posts
        social_posts = await load_social_media_posts()
        
        # Get custom posts from database
        custom_posts = await db.social_media_posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        
        return {
            "ready_to_use_posts": social_posts,
            "custom_posts": custom_posts
        }
    except Exception as e:
        logger.error(f"Error getting social media posts: {e}")
        raise HTTPException(status_code=500, detail="Error loading social media posts")

@api_router.post("/admin/marketing/social-posts", response_model=SocialMediaPost)
async def create_social_media_post(post: SocialMediaPost, current_admin: User = Depends(get_current_admin)):
    """Create/schedule a social media post"""
    try:
        post_dict = post.dict()
        await db.social_media_posts.insert_one(post_dict)
        return post
    except Exception as e:
        logger.error(f"Error creating social media post: {e}")
        raise HTTPException(status_code=500, detail="Error creating social media post")

@api_router.get("/admin/marketing/launch-metrics", response_model=LaunchMetrics)
async def get_launch_metrics(current_admin: User = Depends(get_current_admin)):
    """Get daily launch metrics"""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # New registrations today
        new_registrations = await db.users.count_documents({
            "created_at": {"$gte": today}
        })
        
        # Premium conversions today
        premium_conversions = await db.payment_transactions.count_documents({
            "payment_status": "completed",
            "completed_at": {"$gte": today}
        })
        
        # Referral signups today
        referral_signups = await db.users.count_documents({
            "referred_by": {"$ne": None, "$exists": True},
            "created_at": {"$gte": today}
        })
        
        # Daily active users (users who created messages today)
        daily_active_users = len(await db.scheduled_messages.distinct("user_id", {
            "created_at": {"$gte": today}
        }))
        
        return LaunchMetrics(
            new_registrations=new_registrations,
            premium_conversions=premium_conversions,
            referral_signups=referral_signups,
            daily_active_users=daily_active_users,
            social_engagement=0,  # Would be populated by social media APIs
            email_opens=0,  # Would be populated by email service APIs
            campaign_clicks=0  # Would be populated by campaign tracking
        )
        
    except Exception as e:
        logger.error(f"Error getting launch metrics: {e}")
        raise HTTPException(status_code=500, detail="Error loading launch metrics")

@api_router.get("/admin/marketing/launch-checklist")
async def get_launch_checklist(current_admin: User = Depends(get_current_admin)):
    """Get the launch checklist with current status"""
    try:
        checklist_items = await load_launch_checklist_with_status()
        return {"checklist": checklist_items}
    except Exception as e:
        logger.error(f"Error getting launch checklist: {e}")
        raise HTTPException(status_code=500, detail="Error loading launch checklist")

# Marketing Helper Functions
async def load_predefined_marketing_templates():
    """Load predefined marketing templates from files"""
    templates = []
    
    # Email templates
    templates.append({
        "id": "welcome_email_01",
        "name": "Welcome Email - Immediate",
        "type": "email",
        "subject": "🎉 Willkommen! Deine 5 KI-Nachrichten sind bereit",
        "content": """Hallo {{first_name}},

willkommen bei Deutschlands erster KI-Nachrichten-App! 🤖✨

SOFORT VERFÜGBAR:
✅ 5 kostenlose KI-Nachrichten  
✅ Deutsche Sprachoptimierung
✅ Zeitgesteuerte Zustellung

QUICK START (2 Minuten):
1. Klick auf "AI-Assistent" 
2. Wähle "Meeting-Erinnerung"
3. KI erstellt perfekte deutsche Nachricht
4. Zeitpunkt für Zustellung wählen

[ERSTE NACHRICHT ERSTELLEN →]

BONUS-TIPP: 
Dein Referral-Link: {{referral_link}}
Für jeden Freund bekommt ihr BEIDE 5 extra Nachrichten! 🎁

Bei Fragen einfach antworten!

Beste Grüße,
Das KI-Team 🇩🇪""",
        "variables": ["first_name", "referral_link"],
        "category": "welcome"
    })
    
    templates.append({
        "id": "onboarding_day1",
        "name": "Onboarding Day 1 - Examples",
        "type": "email", 
        "subject": "💡 {{first_name}}, hier sind 3 einfache KI-Beispiele",
        "content": """Hallo {{first_name}},

gestern hast du dich angemeldet - super! Falls du noch nicht deine erste KI-Nachricht erstellt hast, hier sind 3 einfache Ideen:

🔥 BELIEBTE KI-VORLAGEN:

1️⃣ MEETING-ERINNERUNG
"Erinnerung: Meeting morgen um 14:00 Uhr im Konferenzraum A. Agenda: Projektupdate und nächste Schritte."

2️⃣ GEBURTSTAGS-NACHRICHT  
"Herzlichen Glückwunsch zum Geburtstag! 🎉 Ich wünsche dir einen wunderschönen Tag und alles Gute für das neue Lebensjahr!"

3️⃣ ZAHLUNGS-ERINNERUNG
"Freundliche Erinnerung: Die Rechnung XYZ ist in 3 Tagen fällig. Vielen Dank für die pünktliche Begleichung!"

💡 PRO-TIPP: Klick einfach auf "AI-Assistent" → KI macht den Rest!

[JETZT AUSPROBIEREN →]

Fragen? Einfach antworten!
Das KI-Team""",
        "variables": ["first_name"],
        "category": "onboarding"
    })
    
    return templates

async def load_social_media_posts():
    """Load ready-to-use social media posts"""
    posts = [
        {
            "platform": "twitter",
            "content": "🚀 NEU: Deutschlands erste KI-Nachrichten-App ist live! \n\n✨ Deutsche KI schreibt perfekte Nachrichten\n⏰ Zeitgesteuerte Zustellung \n🎁 5 kostenlose Nachrichten\n\nJETZT KOSTENLOS TESTEN 👇\n#KI #Produktivität #Deutschland",
            "hashtags": ["#KI", "#Produktivität", "#Deutschland", "#StartUp", "#Innovation"]
        },
        {
            "platform": "linkedin", 
            "content": "🎯 GAME CHANGER für Professionals:\n\nUnsere KI-Nachrichten-App revolutioniert Business-Kommunikation:\n\n✅ KI schreibt Meeting-Erinnerungen\n✅ Perfekte deutsche Formulierungen\n✅ Zeitgesteuerte Zustellung\n✅ 5x schneller als manuell\n\nErgebnis: +40% Effizienz in der Kommunikation\n\n💡 KOSTENLOS testen - Link in Kommentaren\n\n#BusinessEffizienz #KI #Kommunikation",
            "hashtags": ["#BusinessEffizienz", "#KI", "#Kommunikation", "#Produktivität"]
        }
    ]
    
    return posts

async def load_launch_checklist_with_status():
    """Load launch checklist with current completion status"""
    checklist = [
        {
            "category": "TECHNIK",
            "items": [
                {"task": "✅ Backend API vollständig implementiert", "completed": True},
                {"task": "✅ Frontend UI/UX fertiggestellt", "completed": True}, 
                {"task": "✅ Datenbank optimiert", "completed": True},
                {"task": "✅ KI-Integration funktional", "completed": True},
                {"task": "✅ Payment-System (Stripe) integriert", "completed": True},
                {"task": "✅ Admin-Dashboard aktiv", "completed": True},
                {"task": "✅ Multi-Language Support", "completed": True},
                {"task": "⏳ Email/SMS Integration", "completed": False},
                {"task": "✅ Erweiterte Analytics", "completed": True}
            ]
        },
        {
            "category": "MARKETING",
            "items": [
                {"task": "✅ Social Media Inhalte erstellt", "completed": True},
                {"task": "✅ E-Mail-Vorlagen vorbereitet", "completed": True},
                {"task": "✅ Press Kit zusammengestellt", "completed": True},
                {"task": "✅ Launch-Strategie definiert", "completed": True},
                {"task": "⏳ Social Media Accounts eingerichtet", "completed": False},
                {"task": "⏳ Influencer-Outreach gestartet", "completed": False},
                {"task": "⏳ PR-Kampagne aktiviert", "completed": False}
            ]
        },
        {
            "category": "BUSINESS",
            "items": [
                {"task": "✅ Subscription-Modell implementiert", "completed": True},
                {"task": "✅ Referral-System aktiv", "completed": True},
                {"task": "✅ Abrechnungs-System funktional", "completed": True},
                {"task": "⏳ Rechtliche Prüfung abgeschlossen", "completed": False},
                {"task": "⏳ Datenschutz-Dokumentation", "completed": False},
                {"task": "⏳ Customer Support eingerichtet", "completed": False}
            ]
        }
    ]
    
    return checklist

# Admin endpoints
@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(current_admin: User = Depends(get_current_admin)):
    """Get comprehensive admin statistics"""
    try:
        # User statistics
        total_users = await db.users.count_documents({})
        premium_users = await db.users.count_documents({"subscription_plan": "premium"})
        business_users = await db.users.count_documents({"subscription_plan": "business"})
        
        # Revenue statistics
        total_revenue = 0.0
        monthly_revenue = 0.0
        
        # Get all completed transactions
        completed_transactions = await db.payment_transactions.find({"payment_status": "completed"}).to_list(1000)
        total_revenue = sum(t.get("amount", 0) for t in completed_transactions)
        
        # Calculate current month revenue
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_transactions = await db.payment_transactions.find({
            "payment_status": "completed",
            "completed_at": {"$gte": current_month_start}
        }).to_list(1000)
        monthly_revenue = sum(t.get("amount", 0) for t in monthly_transactions)
        
        # Message statistics
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_sent_today = await db.scheduled_messages.count_documents({
            "status": "delivered",
            "delivered_at": {"$gte": today_start}
        })
        
        messages_sent_month = await db.scheduled_messages.count_documents({
            "status": "delivered",
            "delivered_at": {"$gte": current_month_start}
        })
        
        # Mock Stripe balance (in real app, get from Stripe API)
        available_balance = total_revenue * 0.85  # Simulate 85% available after fees
        pending_payouts = await db.payout_records.aggregate([
            {"$match": {"status": "pending"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        pending_payouts = pending_payouts[0]["total"] if pending_payouts else 0.0
        
        return AdminStats(
            total_users=total_users,
            premium_users=premium_users,
            business_users=business_users,
            total_revenue=total_revenue,
            monthly_revenue=monthly_revenue,
            messages_sent_today=messages_sent_today,
            messages_sent_month=messages_sent_month,
            available_balance=available_balance,
            pending_payouts=pending_payouts
        )
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Statistiken")

@api_router.get("/admin/users")
async def get_all_users(current_admin: User = Depends(get_current_admin)):
    """Get all users (admin only)"""
    try:
        users = await db.users.find({}, {"hashed_password": 0, "_id": 0}).sort("created_at", -1).to_list(1000)
        return {"users": users}
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Benutzer")

@api_router.get("/admin/transactions")
async def get_all_transactions(current_admin: User = Depends(get_current_admin)):
    """Get all payment transactions (admin only)"""
    try:
        transactions = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        
        # Add user information to transactions
        for transaction in transactions:
            user = await db.users.find_one({"id": transaction["user_id"]}, {"email": 1, "name": 1, "_id": 0})
            if user:
                transaction["user_email"] = user["email"]
                transaction["user_name"] = user["name"]
        
        return {"transactions": transactions}
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Transaktionen")

@api_router.post("/admin/payout")
async def request_payout(payout_request: PayoutRequest, current_admin: User = Depends(get_current_admin)):
    """Request a payout to admin's bank account"""
    try:
        # Get available balance
        completed_transactions = await db.payment_transactions.find({"payment_status": "completed"}).to_list(1000)
        total_revenue = sum(t.get("amount", 0) for t in completed_transactions)
        available_balance = total_revenue * 0.85  # After Stripe fees
        
        # Get pending payouts
        pending_payouts = await db.payout_records.aggregate([
            {"$match": {"status": "pending"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        pending_payouts_total = pending_payouts[0]["total"] if pending_payouts else 0.0
        
        actual_available = available_balance - pending_payouts_total
        
    except Exception as e:
        logger.error(f"Error calculating payout balance: {e}")
        raise HTTPException(status_code=500, detail="Fehler bei der Berechnung des verfügbaren Guthabens")
    
    # Check balance outside try-catch to allow HTTPException to propagate
    if payout_request.amount > actual_available:
        raise HTTPException(
            status_code=400, 
            detail=f"Nicht genügend Guthaben verfügbar. Verfügbar: €{actual_available:.2f}"
        )
    
    try:
        # Create payout record
        payout = PayoutRecord(
            admin_user_id=current_admin.id,
            amount=payout_request.amount,
            description=payout_request.description
        )
        
        await db.payout_records.insert_one(payout.dict())
        
        # In a real implementation, you would call Stripe's Payout API here
        # stripe_payout = stripe.Payout.create(
        #     amount=int(payout_request.amount * 100),  # Convert to cents
        #     currency='eur',
        #     description=payout_request.description
        # )
        
        # For now, simulate successful payout after 5 minutes
        # In production, this would be handled by Stripe webhooks
        
        return {
            "message": "Auszahlung wurde angefordert",
            "payout_id": payout.id,
            "amount": payout_request.amount,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Error creating payout: {e}")
        raise HTTPException(status_code=500, detail="Fehler bei der Auszahlungsanforderung")

@api_router.get("/admin/payouts")
async def get_payout_history(current_admin: User = Depends(get_current_admin)):
    """Get payout history for admin"""
    try:
        payouts = await db.payout_records.find({}, {"_id": 0}).sort("requested_at", -1).to_list(1000)
        
        # Add admin user information
        for payout in payouts:
            admin_user = await db.users.find_one({"id": payout["admin_user_id"]}, {"email": 1, "name": 1, "_id": 0})
            if admin_user:
                payout["admin_email"] = admin_user["email"]
                payout["admin_name"] = admin_user["name"]
        
        return {"payouts": payouts}
    except Exception as e:
        logger.error(f"Error getting payouts: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Auszahlungen")

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, current_admin: User = Depends(get_current_admin)):
    """Update user role (admin only)"""
    new_role = role_data.get("role")
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Ungültige Rolle")
    
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"role": new_role}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
        
        return {"message": f"Benutzerrolle auf {new_role} geändert"}
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Aktualisieren der Benutzerrolle")

# Advanced Analytics Endpoints (Admin only)
@api_router.get("/admin/analytics/users", response_model=UserAnalytics) 
async def get_user_analytics(current_admin: User = Depends(get_current_admin)):
    """Get comprehensive user analytics for admin dashboard"""
    try:
        # Registration trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        registrations_pipeline = [
            {"$match": {"created_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        registration_trends = await db.users.aggregate(registrations_pipeline).to_list(None)
        
        # Subscription conversion rate
        total_users = await db.users.count_documents({})
        paid_users = await db.users.count_documents({"subscription_plan": {"$in": ["premium", "business"]}})
        conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
        
        # User retention rate (users active in last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = await db.scheduled_messages.distinct("user_id", {"created_at": {"$gte": seven_days_ago}})
        retention_rate = (len(active_users) / total_users * 100) if total_users > 0 else 0
        
        # Top referrers
        top_referrers_pipeline = [
            {"$match": {"referred_by": {"$ne": None, "$exists": True}}},
            {"$group": {"_id": "$referred_by", "referrals": {"$sum": 1}}},
            {"$sort": {"referrals": -1}},
            {"$limit": 10}
        ]
        top_referrers_raw = await db.users.aggregate(top_referrers_pipeline).to_list(None)
        top_referrers = []
        for referrer in top_referrers_raw:
            user_info = await db.users.find_one({"referral_code": referrer["_id"]}, {"name": 1, "email": 1})
            if user_info:
                top_referrers.append({
                    "referrer_name": user_info.get("name", "Unknown"),
                    "referrer_email": user_info.get("email", "Unknown"),
                    "referrals": referrer["referrals"]
                })
        
        # User activity heatmap (messages created by hour of day)
        activity_pipeline = [
            {"$group": {
                "_id": {"$hour": "$created_at"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        activity_heatmap = await db.scheduled_messages.aggregate(activity_pipeline).to_list(None)
        
        return UserAnalytics(
            registration_trends=registration_trends,
            subscription_conversion_rate=round(conversion_rate, 2),
            user_retention_rate=round(retention_rate, 2),
            top_referrers=top_referrers,
            user_activity_heatmap=activity_heatmap
        )
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Benutzer-Analytik")

@api_router.get("/admin/analytics/messages", response_model=MessageAnalytics)
async def get_message_analytics(current_admin: User = Depends(get_current_admin)):
    """Get comprehensive message analytics for admin dashboard"""
    try:
        # Message creation patterns (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        creation_pipeline = [
            {"$match": {"created_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        creation_patterns = await db.scheduled_messages.aggregate(creation_pipeline).to_list(None)
        
        # Delivery success rate
        total_messages = await db.scheduled_messages.count_documents({})
        delivered_messages = await db.scheduled_messages.count_documents({"status": "delivered"})
        success_rate = (delivered_messages / total_messages * 100) if total_messages > 0 else 0
        
        # Popular times for scheduling
        popular_times_pipeline = [
            {"$group": {
                "_id": {"$hour": "$scheduled_time"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        popular_times = await db.scheduled_messages.aggregate(popular_times_pipeline).to_list(None)
        
        # Message type distribution
        recurring_messages = await db.scheduled_messages.count_documents({"is_recurring": True})
        oneshot_messages = total_messages - recurring_messages
        message_type_distribution = [
            {"type": "Einmalig", "count": oneshot_messages},
            {"type": "Wiederkehrend", "count": recurring_messages}
        ]
        
        # Recurring vs one-shot breakdown
        recurring_vs_oneshot = {
            "recurring": recurring_messages,
            "oneshot": oneshot_messages,
            "recurring_percentage": round((recurring_messages / total_messages * 100) if total_messages > 0 else 0, 2)
        }
        
        return MessageAnalytics(
            creation_patterns=creation_patterns,
            delivery_success_rate=round(success_rate, 2),
            popular_times=popular_times,
            message_type_distribution=message_type_distribution,
            recurring_vs_oneshot=recurring_vs_oneshot
        )
    except Exception as e:
        logger.error(f"Error getting message analytics: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Nachrichten-Analytik")

@api_router.get("/admin/analytics/revenue", response_model=RevenueAnalytics)
async def get_revenue_analytics(current_admin: User = Depends(get_current_admin)):
    """Get comprehensive revenue analytics for admin dashboard"""
    try:
        # MRR trend (last 12 months)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        mrr_pipeline = [
            {"$match": {"payment_status": "completed", "completed_at": {"$gte": twelve_months_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$completed_at"}},
                "revenue": {"$sum": "$amount"}
            }},
            {"$sort": {"_id": 1}}
        ]
        mrr_trend = await db.payment_transactions.aggregate(mrr_pipeline).to_list(None)
        
        # ARPU (Average Revenue Per User)
        total_revenue = sum(t.get("revenue", 0) for t in mrr_trend)
        total_users = await db.users.count_documents({})
        arpu = (total_revenue / total_users) if total_users > 0 else 0
        
        # Churn rate (estimate based on subscription status)
        active_subscribers = await db.users.count_documents({
            "subscription_plan": {"$in": ["premium", "business"]},
            "subscription_status": "active"
        })
        total_ever_subscribed = await db.payment_transactions.distinct("user_id", {"payment_status": "completed"})
        churn_rate = ((len(total_ever_subscribed) - active_subscribers) / len(total_ever_subscribed) * 100) if total_ever_subscribed else 0
        
        # Subscription growth rate (month over month)
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        current_month_subs = await db.payment_transactions.count_documents({
            "payment_status": "completed",
            "completed_at": {"$gte": current_month}
        })
        last_month_subs = await db.payment_transactions.count_documents({
            "payment_status": "completed",
            "completed_at": {"$gte": last_month, "$lt": current_month}
        })
        
        growth_rate = ((current_month_subs - last_month_subs) / last_month_subs * 100) if last_month_subs > 0 else 0
        
        # Revenue by plan
        revenue_by_plan_pipeline = [
            {"$match": {"payment_status": "completed"}},
            {"$group": {
                "_id": "$subscription_plan",
                "revenue": {"$sum": "$amount"},
                "subscribers": {"$sum": 1}
            }}
        ]
        revenue_by_plan = await db.payment_transactions.aggregate(revenue_by_plan_pipeline).to_list(None)
        
        return RevenueAnalytics(
            mrr_trend=mrr_trend,
            arpu=round(arpu, 2),
            churn_rate=round(churn_rate, 2),
            subscription_growth_rate=round(growth_rate, 2),
            revenue_by_plan=revenue_by_plan
        )
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Umsatz-Analytik")

@api_router.get("/admin/analytics/ai", response_model=AIAnalytics)
async def get_ai_analytics(current_admin: User = Depends(get_current_admin)):
    """Get comprehensive AI usage analytics for admin dashboard"""
    try:
        # Mock AI analytics for now - would be implemented with actual usage tracking
        # In a real implementation, you'd track AI usage events in a separate collection
        
        # Feature usage (simulated based on user subscription levels)
        total_premium_business = await db.users.count_documents({"subscription_plan": {"$in": ["premium", "business"]}})
        
        feature_usage = [
            {"feature": "Nachrichtenerstellung", "usage_count": total_premium_business * 15, "percentage": 85.0},
            {"feature": "Text-Verbesserung", "usage_count": total_premium_business * 12, "percentage": 72.0},
            {"feature": "Rechtschreibprüfung", "usage_count": total_premium_business * 8, "percentage": 45.0},
            {"feature": "Tonhöhenanpassung", "usage_count": total_premium_business * 6, "percentage": 35.0}
        ]
        
        # Generation success rate (mock - would track actual API responses)
        generation_success_rate = 94.5
        
        # Popular prompts (mock data)
        popular_prompts = [
            {"prompt_type": "Meeting-Erinnerung", "usage_count": total_premium_business * 8},
            {"prompt_type": "Geburtstagsnachricht", "usage_count": total_premium_business * 6},
            {"prompt_type": "Terminerinnerung", "usage_count": total_premium_business * 7},
            {"prompt_type": "Zahlungserinnerung", "usage_count": total_premium_business * 4}
        ]
        
        # Enhancement types
        enhancement_types = [
            {"type": "Verbessern", "count": total_premium_business * 10},
            {"type": "Korrigieren", "count": total_premium_business * 8},
            {"type": "Kürzen", "count": total_premium_business * 3},
            {"type": "Erweitern", "count": total_premium_business * 5}
        ]
        
        # AI adoption rate (users who have used AI features)
        total_users = await db.users.count_documents({})
        ai_adoption_rate = (total_premium_business / total_users * 100) if total_users > 0 else 0
        
        return AIAnalytics(
            feature_usage=feature_usage,
            generation_success_rate=generation_success_rate,
            popular_prompts=popular_prompts,
            enhancement_types=enhancement_types,
            ai_adoption_rate=round(ai_adoption_rate, 2)
        )
    except Exception as e:
        logger.error(f"Error getting AI analytics: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der KI-Analytik")

@api_router.get("/admin/analytics/complete", response_model=AdvancedAnalytics)
async def get_complete_analytics(current_admin: User = Depends(get_current_admin)):
    """Get all analytics data in one comprehensive response"""
    try:
        # Get all analytics components
        user_analytics = await get_user_analytics(current_admin)
        message_analytics = await get_message_analytics(current_admin)
        revenue_analytics = await get_revenue_analytics(current_admin)
        ai_analytics = await get_ai_analytics(current_admin)
        
        return AdvancedAnalytics(
            user_analytics=user_analytics,
            message_analytics=message_analytics,
            revenue_analytics=revenue_analytics,
            ai_analytics=ai_analytics
        )
    except Exception as e:
        logger.error(f"Error getting complete analytics: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der vollständigen Analytik")

@api_router.get("/admin/analytics/export")
async def export_analytics_data(format: str = "csv", current_admin: User = Depends(get_current_admin)):
    """Export analytics data in CSV or JSON format (Business feature)"""
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    try:
        # Get complete analytics
        analytics = await get_complete_analytics(current_admin)
        
        if format == "json":
            return {
                "format": "json",
                "data": analytics.dict(),
                "exported_at": datetime.utcnow().isoformat()
            }
        else:
            # For CSV export, return a simplified structure
            # In a real implementation, you'd generate actual CSV content
            return {
                "format": "csv",
                "download_url": f"/api/admin/analytics/download?format=csv&generated_at={datetime.utcnow().isoformat()}",
                "message": "CSV export prepared. Use the download_url to get the file."
            }
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Exportieren der Analytik")

# Basic Analytics (Business users only)
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