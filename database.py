import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_USERNAME, DB_PASSWORD, DB_SERVER, DB_NAME
from bson.objectid import ObjectId
import time


class Database(object):
    def __init__(self):
        self.async_client = AsyncIOMotorClient(
           f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"
        )

        self.async_db = self.async_client[DB_NAME]
        self.user_messages = self.async_db.user_messages
        self.boost_data = self.async_db.boost_data
        self.color_data = self.async_db.color_data
        self.server_data = self.async_db.server_data
        self.locked_channels = self.async_db.locked_channels
        self.card_stats = self.async_db.card_stats
        self.active_games = self.async_db.active_games
        self.polls = self.async_db.polls
        self.violations = self.async_db.violations
        self.afk = self.async_db.afk
        self.reminder = self.async_db.reminder
        self.giveaways = self.async_db.giveaways
        self.invites = self.async_db.invites

    async def sync_invites(self, guild):
        for invite in await guild.invites():
            await self.invites.update_one({
                "invite_id": invite.id,
                "guild_id": str(guild.id),
                "user_id": str(invite.inviter.id),
            }, {
                "$set": {
                    "uses": 0,
                    "joins": [],
                    "leaves": []
                }
            }, upsert=True)

    async def add_game(self, data):
        data = await self.active_games.insert_one(data)

        return ObjectId(data.inserted_id)

    async def create_game(self, data):
        """Cards against Discord"""
        data = await self.active_games.insert_one(data)

        return ObjectId(data.inserted_id)

    async def find_game(self, host_id: str):
        """Cards against Discord"""
        data = await self.active_games.find_one({"host": host_id})
        return data

    async def find_stats(self, user_id: str):
        """Cards against Discord"""
        data = await self.active_games.find_one({"user_id": str(user_id)})
        return data

    async def update_stats(self, user_id: int, data):
        """Cards against Discord"""
        try:
            await self.card_stats.update_one({"user_id": str(user_id)}, data)

        except Exception as e:
            print("Issue editing stats:", e)

    async def edit_game(self, host_id: int, data):
        """Cards against Discord"""
        try:
            await self.active_games.update_one({"host": host_id}, data)

        except Exception as e:
            print("Issue editing game:", e)

    async def add_user(self, host_id: str, user_id: str, user_data):
        """Cards against Discord"""
        try:
            data = await self.active_games.update_one(
                {"host": host_id},
                {"$set": {f"players.{user_id}": user_data[user_id]}},
            )

            if data.modified_count > 0:
                return {"added": True}

            else:
                return {"added": False, "error": "This game is full!"}

        except Exception as e:
            print("Issue adding user to a game!:", e)
            return {
                "added": False,
                "error": f"I couldn't add you to the game for the following reason: {e}. Please contact support!"
            }

    async def remove_user(self, host_id: str, user_id: str):
        """Cards against Discord"""
        try:
            data = await self.active_games.update_one(
                {"host": host_id},
                {"$unset": {f"players.{user_id}": ""}}
            )

            if data.modified_count > 0:
                return {"removed": True}

            else:
                return {"removed": False, "error": "You're not in this game!"}

        except Exception as e:
            print("Issue removing user from a game!:", e)
            return {
                "removed": False,
                "error": f"I couldn't remove you from the game for the following reason: {e}. Please contact support!"
            }

    async def delete_game(self, host_id: str):
        """Cards against Discord"""
        try:
            data = await self.active_games.delete_one(
                {'host': host_id},
            )

            if data.deleted_count > 0:
                return {"deleted": True}

        except Exception as e:
            print("Isuee deleting game:", e)
            return {"deleted": False, "error": f"Failed to delete game for the following reason: {e}"}

        return {"deleted": False, "error": "The game doesn't exist, perhaps it has expired?"}

    # Server Settings
    async def create_server(self, guild_id):
        try:
            data = {"_server_id": str(guild_id)}
            await self.server_data.insert_one(data)
            return data

        except Exception as e:
            print("Issues with creating server..", e)

    async def get_server(self, guild_id, create=False):
        data = await self.server_data.find_one({"_server_id": str(guild_id)})

        if data is None:
            if create:
                data = await self.create_server(guild_id)

            else:
                data = {"_server_id": str(guild_id)}

        return data

    async def update_server(self, guild_id, key, value=1, delete=False):
        try:
            await self.get_server(guild_id, True)  # Just making sure it exists

            if delete:
                await self.server_data.update_one(
                    {"_server_id": str(guild_id)},
                    {"$unset": {key: value}}
                )

            else:
                await self.server_data.update_one(
                    {"_server_id": str(guild_id)},
                    {"$set": {key: value}}
                )

        except Exception as e:
            print("issue with updating server", e)

    # Channels
    async def add_lock_channel(self, data):
        try:
            await self.locked_channels.insert_one(data)
            return data

        except Exception as e:
            print("Issues with creating giveaway for a user...", e)

    async def find_ended_channel_lock(self, duration, flag=True):
        search = self.locked_channels.find({
            "duration": {"$lt": duration}
        })

        return await search.to_list(length=100)

    async def delete_channel_data(self, id):
        try:
            data = await self.locked_channels.delete_one(
                {"_id": ObjectId(str(id))}
            )

            if data.deleted_count > 0:
                return True

        except Exception as e:
            print("Issue deleting channel data:", e)
            return True

        return False

    # Giveaways
    async def create_giveaway(self, giveaway_data):
        try:
            await self.giveaways.insert_one(giveaway_data)
            return giveaway_data

        except Exception as e:
            print("Issues with creating giveaway for a user...", e)

    async def get_giveaway(self, id):
        data = await self.giveaways.find_one({"message_id": id})
        return data

    async def add_to_giveaway(self, id, participant):
        try:
            await self.giveaways.update_one(
                {"message_id": id},
                {"$push": {"participants": participant}}
            )

        except Exception as e:
            print("Issue with add to giveaway:", e)
            return False

        return True

    async def find_user_giveaways(self, host, amount, flag=True):
        host = str(host)  # we ensure it is string

        search = self.giveaways.find({
            "host": host,
            "ended": flag
        })

        expired_giveaways = await search.to_list(length=amount)
        return expired_giveaways

    async def find_ended_giveaways(self, duration, flag=True):
        search = self.giveaways.find({
            "duration": {"$lt": duration},
            "ended": flag
        })

        expired_giveaways = await search.to_list(length=100)
        return expired_giveaways

    async def update_giveaway(self, id, key, value, first_edit=False):
        try:

            if first_edit:
                await self.giveaways.update_one(
                    {"_id": ObjectId(str(id))},
                    {"$set": {key: value}}
                )

            else:
                await self.giveaways.update_one(
                    {"message_id": id},
                    {"$set": {key: value}}
                )

        except Exception as e:
            print("issue with updating ", e)

    async def end_giveaway(self, id):
        try:
            data = await self.giveaways.delete_one(
                {"_id": ObjectId(str(id))}
            )

            if data.deleted_count > 0:
                return True

        except Exception as e:
            print("Issue deleting giveaway:", e)
            return True

        return False

    # Boosts
    async def get_user_boosts(self, user_id):
        bar_data = await self.boost_data.find_one({"_user_id": str(user_id)})
        return bar_data

    async def create_user_boosts(self, boost_data):
        try:
            await self.boost_data.replace_one(
                {"_user_id": boost_data["_user_id"]},
                boost_data,
                upsert=True
            )
            return boost_data

        except Exception as e:
            print("Issues with creating account for a user...", e)

    async def update_user_boost(self, user, boost_type, boost_time):
        try:
            if boost_time != 0:
                boost_time = time.time() + boost_time

            if boost_time is None or boost_time is False:
                boost_time = 0

            await self.boost_data.update_one(
                {"_user_id": user},
                {"$set": {boost_type: boost_time}}
            )

        except Exception as e:
            print("issue with updating user boosts", e)

    # Cooldowns
    async def get_user_cooldowns(self, user_id):
        bar_data = await self.cooldown_data.find_one({"_user_id": str(user_id)})
        return bar_data

    async def create_user_cooldowns(self, cooldown_data):
        try:
            await self.cooldown_data.replace_one(
                {"_user_id": cooldown_data["_user_id"]},
                cooldown_data,
                upsert=True
            )
            return cooldown_data

        except Exception as e:
            print("Issues with creating account for a user...", e)

    # Cooldowns
    async def update_user_cooldown(self, user, cd_type, cd_time):
        try:
            if cd_time != 0:
                cd_time = time.time() + cd_time

            if cd_time is None or cd_time is False:
                cd_time = 0

            await self.cooldown_data.update_one(
                {"_user_id": user},
                {"$set": {cd_type: cd_time}}
            )

        except Exception as e:
            print("issue with updating user cooldowns", e)

    async def update_cooldown_data(self, user, data):
        """Updates a users data. Data must be a dictionary that contains a key and value"""

        try:
            # We process all of the key and values in data to update the user
            for value in data:
                await self.cooldown_data.update_one(
                    {"_user_id": str(user)},
                    {"$set": {f"{value}": data[value]}},
                )

        except Exception as e:
            print("Encountered an issue while trying to update someones cooldown", e, "user", user)

    async def leaderboard(self, item, amount, page, stats=False):
        if stats:
            search = self.bar_data.find({
                f"stats.{item}": {"$exists": True}
            }).skip(page)

            search.sort(f"stats.{item}", pymongo.DESCENDING).limit(amount)

        else:
            search = self.bar_data.find({
                f"{item}": {"$exists": True}
            }).skip(page)

            search.sort(f"{item}", pymongo.DESCENDING).limit(amount)

        leaderboard = await search.to_list(length=amount)

        return leaderboard

    async def add_suggestion(self, suggestion):
        try:
            await self.suggestions.replace_one({"_message_id": suggestion["_message_id"]}, suggestion, upsert=True)

        except Exception as e:
            print("Issue with set subscription:", e)

    async def find_suggestion(self, message_id):
        suggestion = await self.suggestions.find_one({"_message_id": message_id})
        return suggestion