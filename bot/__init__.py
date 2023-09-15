
import logging
import time
from .config import Config
from logging.handlers import RotatingFileHandler


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            "logs.txt",
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

UP_TIME = time.time()


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
