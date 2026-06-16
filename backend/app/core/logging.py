import sys
from loguru import logger
from app.core.config import settings


def setup_logging() -> None:
    logger.remove()
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    logger.add(
        "/app/logs/app.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        catch=True,
    )
