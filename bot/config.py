import os
from time import time
from dotenv import load_dotenv

# Load environment variables from 'config.env' file
load_dotenv('config.env')

def get_env_variable(name: str, default=None, is_int=False):
    value = os.environ.get(name, default)
    if value is not None and is_int:
        try:
            value = int(value)
        except ValueError:
            raise Exception(f"The {name} environment variable should be an integer.")
    return value

class Config:
    APP_ID = get_env_variable("APP_ID", 1543212, is_int=True)
    API_HASH = get_env_variable("API_HASH", "d47de4b25ddf79a08127b433de32dc84")
    ADMINS = get_env_variable("ADMINS", "1478357602").split()
    ADMINS = [int(admin) for admin in ADMINS]
    BOT_TOKEN = get_env_variable("BOT_TOKEN", "5502968436:AAHtTd9M1T0OlRv5akFGO3fGCwtfIs0INis")
    BOT_START_TIME = time()
    DB_URI = get_env_variable("DATABASE_URL", "mongodb+srv://gtm:gtm@cluster0.mc904kw.mongodb.net/?retryWrites=true&w=majority")
    DEFAULT_THUMB = get_env_variable("DEFAULT_THUMB", "https://placehold.it/90x90")
    REQUEST_DELAY = get_env_variable("REQUEST_DELAY", 120, is_int=True)
    PARENT_ID = get_env_variable("PARENT_ID", "1CI7KC0YrbPzd24XhySb9lVZRCXdg-sRG")
    JIO_USERS = get_env_variable("JIO_USERS", "1478357602 5485818124 1738852527").split()
    JIO_USERS = [int(user) for user in JIO_USERS]

    # Handle boolean environment variables
    FORCE_SUB_CHANNEL = get_env_variable('FORCE_SUB_CHANNEL', 'false')
    FORCE_SUB_CHANNEL = FORCE_SUB_CHANNEL.lower() == 'true' if FORCE_SUB_CHANNEL else False

    INDEX_URL = get_env_variable('INDEX_URL', '')
    INDEX_URL = None if len(INDEX_URL) == 0 else INDEX_URL

    IS_TEAM_DRIVE = get_env_variable('IS_TEAM_DRIVE', 'false')
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true' if IS_TEAM_DRIVE else False

    USE_SERVICE_ACCOUNTS = get_env_variable('USE_SERVICE_ACCOUNTS', 'false')
    USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true' if USE_SERVICE_ACCOUNTS else False
