

import datetime
from typing import Union
import motor.motor_asyncio # pylint: disable=import-error
from pymongo.collection import Collection # pylint: disable=import-error

from bot import Config, LOGGER # pylint: disable=import-error


logger = LOGGER(__name__)
CACHE = {}


class Database:

    def __init__(self):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URI)
        self.db = self._client["JioCinema_Bot"]
        self.usr_col = self.db["Users"]
        self.thmb_col = self.db["Thumbnails"]
        self.drive = self.db["Drive"]

        self.cache = {}


    async def new_user(self, _id, name=None, username=None):
        data = dict(
            _id=_id,
            name=name,
            username=username,
            status=dict(
                active=True,
                joined_date=datetime.date.today().isoformat(),
                last_used_on=datetime.date.today().isoformat()
            ),
            ban_status=dict(
                is_banned=False,
                ban_reason="",
                banned_on=datetime.date.max.isoformat(),
                ban_duration=0
            )
        )
        return data


    async def add_user(self, user_id: int):
        data = await self.new_user(user_id)
        await self.usr_col.insert_one(data)
        
        CACHE[str(user_id)] = data
        return True


    async def remove_user(self, user_id: int):
        if CACHE.get(str(user_id)):
            CACHE.pop(str(user_id))
        
        await self.usr_col.delete_one({"_id": user_id})
        return True


    async def get_user(self, user_id: int):

        cache = CACHE.get(str(user_id))
        if cache is not None:
            return cache
       
        user_data = await self.usr_col.find_one({"_id": user_id})
        
        if not user_data:
            await self.add_user(user_id)
            user_data = await self.new_user(user_id)
        
        CACHE[str(user_id)] = user_data
        return user_data


    async def get_status(self, user_id: int):
        await self.get_user(user_id)
        return CACHE[str(user_id)]["status"]


    async def get_ban_status(self, user_id: int):
        await self.get_user(user_id)
        return CACHE[str(user_id)]["ban_status"]


    async def get_all_users(self):
        cursor = self.usr_col.find({}, {"_id": 1})
        users = []
        for user in await cursor.to_list(length=None):
            users.append(user)
        return users

    
    async def get_all_users_count(self):
        count = await self.usr_col.count_documents({})
        return count


    async def get_all_banned_users(self):
        users = self.usr_col.find({"ban_status.is_banned":True}, {"ban_status": 1, "_id": 1})
        return await users.to_list(length=0)


    async def update_user(self, user_id: int, name: str, username: str):
        prev = await self.get_user(user_id)
        await self.usr_col.update_one(prev, {"$set":{"name": name, "username": username}})
        return True



    async def update_status(self, user_id: int, status: dict, name=None, username=None):
        prev = await self.get_user(user_id)
        await self.usr_col.update_one(prev, {"$set":{"status": status}})
        CACHE[str(user_id)]["status"] = status
        
        if not (name and username) == None:
            await self.update_user(user_id, name, username)
            CACHE[str(user_id)]["name"] = name
            CACHE[str(user_id)]["username"] = username
        
        return True


    async def update_ban_status(self, user_id: int, ban_status: dict):
        
        del CACHE[str(user_id)]
        prev = await self.get_user(user_id)
        await self.usr_col.update_one(prev, {"$set":{"ban_status": ban_status}})

        return True


    async def update_unban_user(self, user_id: int):
        prev = await self.get_user(user_id)
        total_bans = CACHE[str(user_id)]["ban_status"]["total_bans"]
        ban_history = {"$push":{"reason":"", "banned_on":"", "duration":""}}
        ban_status = { "is_banned":False, "ban_reason":"", "total_bans": (total_bans + 1),
            "ban_history": ban_history}
        
        await self.usr_col.update_one(prev, {"$set":{"ban_status":ban_status}})
        CACHE[str(user_id)]["ban_status"] = ban_status
        
        return True


    async def update_unban_all(self):
        users = await self.usr_col.find({"ban_status":{"is_banned": True}})
        for user in users:
            await self.update_unban_user(user["_id"])
        
        return True


    async def new_thumb(self, user_id: int, file_id: str) -> dict:
        return dict(
            _id=user_id,
            file_id=file_id
        )

    async def add_thumb(self, user_id: int, file_id: str) -> bool:

        count = await self.thmb_col.count_documents({"_id": user_id})

        if count == 1:
            try:
                await self.thmb_col.update_one({"_id": user_id}, {"$set": {"file_id": file_id}})
                return True
            except Exception as e:
                logger.exception(e, exc_info=True)
                return False

        else:
            thumb = await self.new_thumb(user_id, file_id)
            try:
                await self.thmb_col.insert_one(thumb)
                return True
            except Exception as e:
                logger.exception(e, exc_info=True)
                return False

    async def get_thumb(self, user_id: int) -> Union[dict, None]:

        thumb = await self.thmb_col.find_one({"_id": user_id})
        if isinstance(thumb, dict):
            return thumb["file_id"]
        else:
            return None

    async def del_thumb(self, user_id: int) -> bool:
        await self.thmb_col.delete_one({"_id": user_id})
        return True

    async def save_cread(self, user_id: int, data: dict) -> bool:

        count = await self.drive.count_documents({"_id": user_id})

        if count == 1:
            try:
                await self.drive.update_one({"_id": int(user_id)}, {"$set": {
                    "creads": data['creads'],
                    "parent_id": data['parent_id']
                }})
                return True
            except Exception as e:
                logger.exception(e, exc_info=True)
                return False

        else:
            try:
                await self.drive.insert_one({'_id': int(user_id), 'creads': data['creads'], "parent_id": data['parent_id']})
                return True
            except Exception as e:
                logger.exception(e, exc_info=True)
                return False

    async def get_cread(self, user_id: int) -> Union[dict, None]:

        data = await self.drive.find_one({"_id": int(user_id)})
        if not data is None:
            return data
        else:
            logger.info(user_id)
            logger.info(type(user_id))
            return {'_id': user_id, 'creads': None, 'parent_id': 'root'}

    async def del_cread(self, user_id: int) -> bool:
        await self.drive.delete_one({"_id": user_id})
        return True


