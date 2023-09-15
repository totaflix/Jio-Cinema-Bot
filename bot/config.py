import os
from time import time
from dotenv import load_dotenv

load_dotenv('config.env')

def getConfig(name: str):
    return os.environ[name]

class Config (object):
    
    APP_ID = int(os.environ.get("APP_ID", 1543212))
    
    API_HASH = os.environ.get("API_HASH", "d47de4b25ddf79a08127b433de32dc84")
    try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "1478357602 5485818124 1738852527").split()):
        ADMINS.append(int(x))
 except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

    BOT_TOKEN = os.environ.get("BOT_TOKEN", "5502968436:AAHtTd9M1T0OlRv5akFGO3fGCwtfIs0INis")

    BOT_START_TIME = time()
    
    DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://gtm:gtm@cluster0.mc904kw.mongodb.net/?retryWrites=true&w=majority")

    DEFAULT_THUMB = os.environ.get("DEFAULT_THUMB", "https://placehold.it/90x90")

    REQUEST_DELAY = int(os.environ.get("REQUEST_DELAY", 120))

    PARENT_ID = os.environ.get("PARENT_ID", "1CI7KC0YrbPzd24XhySb9lVZRCXdg-sRG")
    try:
    JIO=[]
    for x in (os.environ.get("JIO_USERS", "1478357602 5485818124 1738852527").split()):
        JIO.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

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


