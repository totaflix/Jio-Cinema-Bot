import os
from time import time
from dotenv import load_dotenv

load_dotenv('config.env')

def getConfig(name: str):
    return os.environ[name]

class Config (object):
    
    APP_ID = int(os.environ.get("APP_ID", 0))
    
    API_HASH = os.environ.get("API_HASH", "")
    
    AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "1478357602").split())
    
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    BOT_START_TIME = time()
    
    DB_URI = os.environ.get("DATABASE_URL", "")

    DEFAULT_THUMB = os.environ.get("DEFAULT_THUMB", "https://placehold.it/90x90")
    
    HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", '')

    HEROKU_APP_NAME = os.environ.get('HEROKU_APP_NAME', '')

    REQUEST_DELAY = int(os.environ.get("REQUEST_DELAY", 120))

    PARENT_ID = os.environ.get("PARENT_ID", "root")

    JIO_USERS = set(int(x) for x in os.environ.get("JIO_USERS", "1478357602").split())

    try:
        FORCE_SUB_CHANNEL = getConfig('FORCE_SUB_CHANNEL')
        if FORCE_SUB_CHANNEL.lower() == 'false' or len(FORCE_SUB_CHANNEL) == 0:
            FORCE_SUB_CHANNEL = False
    except KeyError:
        FORCE_SUB_CHANNEL = False

    try:
        INDEX_URL = getConfig('INDEX_URL')
        if len(INDEX_URL) == 0:
            INDEX_URL = None
    except KeyError:
        INDEX_URL = None

    try:
        IS_TEAM_DRIVE = getConfig('IS_TEAM_DRIVE')
        if IS_TEAM_DRIVE.lower() == 'true':
            IS_TEAM_DRIVE = True
        else:
            IS_TEAM_DRIVE = False
    except KeyError:
        IS_TEAM_DRIVE = False


    try:
        USE_SERVICE_ACCOUNTS = getConfig('USE_SERVICE_ACCOUNTS')
        if USE_SERVICE_ACCOUNTS.lower() == 'true':
            USE_SERVICE_ACCOUNTS = True
        else:
            USE_SERVICE_ACCOUNTS = False
    except KeyError:
        USE_SERVICE_ACCOUNTS = False


