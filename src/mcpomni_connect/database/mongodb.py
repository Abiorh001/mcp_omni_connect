from mcpomni_connect.memory_store.base import AbstractMemoryStore
from datetime import datetime
from mcpomni_connect.utils import logger
from pymongo import AsyncMongoClient, errors


class MongoDb(AbstractMemoryStore):
    def __init__(
        self,
        uri="mongodb://localhost:27017/",
        db_name="mcpomni_connect",
        collection="messages",
    ):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection
        self.client = None
        self.db = None
        self.collection = None
        self._initialized = False
        self.memory_config = {"mode": "token_budget", "value": None}

    async def _ensure_connected(self):
        """Ensure MongoDB connection is established"""
        if not self._initialized:
            try:
                self.client = AsyncMongoClient(self.uri)
                await self.client.admin.command("ping")
                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]
                await self.collection.create_index("session_id")
                await self.collection.create_index("msg_metadata.agent_name")
                self._initialized = True
                logger.info("connected to mongodb")
            except errors.ConnectionError as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise RuntimeError(f"Could not connect to MongoDB at {self.uri}.")

    def set_memory_config(self, mode: str, value: int = None) -> None:
        valid_modes = {"sliding_window", "token_budget"}
        if mode.lower() not in valid_modes:
            raise ValueError(
                f"Invalid memory mode: {mode}. Must be one of {valid_modes}."
            )
        self.memory_config = {"mode": mode, "value": value}

    async def store_message(
        self,
        role: str,
        content: str,
        metadata: dict | None = None,
        session_id: str = None,
    ) -> None:
        """
        Store a message in the MongoDB collection.
        """
        try:
            await self._ensure_connected()
            if metadata is None:
                metadata = {}
            message = {
                "role": role,
                "content": content,
                "msg_metadata": metadata,
                "session_id": session_id,
                "timestamp": datetime.now(),
            }
            await self.collection.insert_one(message)
        except Exception as e:
            logger.error(f"Failed to store message: {e}")

    async def get_messages(self, session_id: str = None, agent_name: str = None):
        """
        Retrieve messages from the MongoDB collection.
        If session_id is provided, filter by session_id.
        If agent_name is provided, filter by agent_name in metadata.
        """
        try:
            await self._ensure_connected()
            query = {}
            if session_id:
                query["session_id"] = session_id
            if agent_name:
                query["msg_metadata.agent_name"] = agent_name

            cursor = self.collection.find(
                query,
                {"_id": 0},
            ).sort("timestamp", 1)

            messages = await cursor.to_list(length=None)
            result = [
                {
                    "role": m["role"],
                    "content": m["content"],
                    "session_id": m["session_id"],
                    "timestamp": (
                        m["timestamp"].timestamp()
                        if isinstance(m["timestamp"], datetime)
                        else m["timestamp"]
                    ),
                    "msg_metadata": m.get("msg_metadata"),
                }
                for m in messages
            ]
            mode = self.memory_config.get("mode", "token_budget")
            value = self.memory_config.get("value")
            if mode.lower() == "sliding_window" and value is not None:
                result = result[-value:]
            if mode.lower() == "token_budget" and value is not None:
                total_tokens = sum(len(str(msg["content"]).split()) for msg in result)
                while total_tokens > value and result:
                    result.pop(0)
                    total_tokens = sum(
                        len(str(msg["content"]).split()) for msg in result
                    )
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []

        return result

    async def clear_memory(
        self, session_id: str = None, agent_name: str = None
    ) -> None:
        try:
            await self._ensure_connected()

            if session_id and agent_name:

                await self.collection.delete_many(
                    {"session_id": session_id, "msg_metadata.agent_name": agent_name}
                )

            elif session_id:

                await self.collection.delete_many({"session_id": session_id})
            elif agent_name:

                await self.collection.delete_many(
                    {"msg_metadata.agent_name": agent_name}
                )
            else:

                await self.collection.delete_many({})
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
