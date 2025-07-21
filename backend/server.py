from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Background task flag
scheduler_running = False

# Define Models
class ScheduledMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    scheduled_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "scheduled"  # scheduled, delivered, failed
    delivered_at: Optional[datetime] = None

class ScheduledMessageCreate(BaseModel):
    title: str
    content: str
    scheduled_time: datetime

class ScheduledMessageResponse(BaseModel):
    id: str
    title: str
    content: str
    scheduled_time: datetime
    created_at: datetime
    status: str
    delivered_at: Optional[datetime] = None

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

# Message endpoints
@api_router.post("/messages", response_model=ScheduledMessageResponse)
async def create_scheduled_message(message: ScheduledMessageCreate):
    message_dict = message.dict()
    message_obj = ScheduledMessage(**message_dict)
    await db.scheduled_messages.insert_one(message_obj.dict())
    return ScheduledMessageResponse(**message_obj.dict())

@api_router.get("/messages", response_model=List[ScheduledMessageResponse])
async def get_scheduled_messages():
    messages = await db.scheduled_messages.find().sort("scheduled_time", 1).to_list(1000)
    return [ScheduledMessageResponse(**message) for message in messages]

@api_router.get("/messages/delivered", response_model=List[ScheduledMessageResponse])
async def get_delivered_messages():
    messages = await db.scheduled_messages.find({"status": "delivered"}).sort("delivered_at", -1).to_list(1000)
    return [ScheduledMessageResponse(**message) for message in messages]

@api_router.get("/messages/scheduled", response_model=List[ScheduledMessageResponse])
async def get_pending_messages():
    messages = await db.scheduled_messages.find({"status": "scheduled"}).sort("scheduled_time", 1).to_list(1000)
    return [ScheduledMessageResponse(**message) for message in messages]

@api_router.delete("/messages/{message_id}")
async def delete_message(message_id: str):
    result = await db.scheduled_messages.delete_one({"id": message_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}

@api_router.get("/")
async def root():
    return {"message": "Zeitgesteuerte Nachrichten API - Time-controlled Messages"}

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