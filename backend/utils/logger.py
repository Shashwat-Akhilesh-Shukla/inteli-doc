import os
import sys
from loguru import logger

# Remove default handler
logger.remove()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

IF_DEV = ENVIRONMENT == "development"

# Add console handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if IF_DEV else "INFO",
    colorize=True,
    enqueue=True,
)

# Add file handler for production or persistent logs
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    enqueue=True,
)

def get_logger(name: str = None):
    if name:
        return logger.bind(name=name)
    return logger

app_logger = get_logger()
