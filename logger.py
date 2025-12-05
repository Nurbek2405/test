# logger.py
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"bot_{datetime.now().strftime('%d.%m.%Y')}.log")

logger = logging.getLogger("TestBot")
logger.setLevel(logging.INFO)

class UserIDFilter(logging.Filter):
    def filter(self, record):
        user_id = getattr(record, 'user_id', None)
        record.user_prefix = f"[user:{user_id}] " if user_id is not None else "[-] "
        return True

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(user_prefix)s%(message)s", "%H:%M:%S")

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.addFilter(UserIDFilter())

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.addFilter(UserIDFilter())

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_user_action(user_id: int, action: str, details: str = ""):
    msg = action
    if details:
        msg += f" | {details}"
    logger.info(msg, extra={"user_id": user_id})