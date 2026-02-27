"""Database connection and initialization."""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

logger = logging.getLogger(__name__)

# MongoDB client and database
client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Connect to MongoDB and create indexes."""
    global client, db
    
    logger.info(f"Connecting to MongoDB at {settings.MONGO_URL}")
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    # Create indexes for optimal query performance
    await create_indexes()
    logger.info("Database connected and indexes created")


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("Database connection closed")


async def create_indexes():
    """Create database indexes for optimal performance."""
    logger.info("Creating database indexes...")
    
    try:
        # Users collection
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        
        # Assets collection (frequently queried by userId)
        await db.assets.create_index([("userId", 1), ("symbol", 1)])
        await db.assets.create_index("userId")
        
        # Predictions collection (sorted by timestamp, paginated)
        await db.predictions.create_index([("userId", 1), ("timestamp", -1)])
        await db.predictions.create_index("stockSymbol")
        
        # Quiz scores (sorted by completedAt)
        await db.quiz_scores.create_index([("userId", 1), ("completedAt", -1)])
        await db.quiz_scores.create_index("lessonId")
        
        # Chat history (sorted by timestamp)
        await db.chat_history.create_index([("userId", 1), ("timestamp", -1)])
        
        # Alerts (filtered by is_read, sorted by created_at, paginated)
        await db.alerts.create_index([("is_read", 1), ("created_at", -1)])
        await db.alerts.create_index("created_at")
        
        # Community chat (sorted by timestamp, with TTL)
        await db.community_chat.create_index([("timestamp", -1)])
        # TTL index: auto-delete messages older than 30 days
        await db.community_chat.create_index(
            "timestamp", 
            expireAfterSeconds=2592000,  # 30 days
            name="ttl_community_chat"
        )
        
        # Stocks collection
        await db.stocks.create_index("symbol", unique=True)
        
        # Lessons collection
        await db.lessons.create_index("order")
        
        # News collection
        await db.news.create_index("date")
        
        logger.info("✓ All indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        # Don't fail startup if indexes already exist


def get_db():
    """Dependency injection for database."""
    return db
