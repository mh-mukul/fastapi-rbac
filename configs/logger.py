import os
import logging
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler

load_dotenv()
LOG_DIR = os.environ.get("LOG_DIR", "./logs")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

log_file = f"{LOG_DIR}/app.log"

# Create a single logger instance
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7)

    formatter = logging.Formatter(
        "%(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
