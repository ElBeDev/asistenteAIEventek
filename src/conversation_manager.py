import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages the mapping between user IDs (e.g., WhatsApp sender ID)
    and OpenAI Thread IDs.

    NOTE: This is a simple in-memory implementation. For production,
    consider using a database (like MongoDB) to persist these mappings,
    especially if your App Engine instances might scale or restart.
    """
    def __init__(self):
        # Simple in-memory dictionary to store user_id -> thread_id mappings
        self._thread_map: Dict[str, str] = {}
        logger.info("ConversationManager initialized (in-memory storage).")

    def get_thread_id(self, user_id: str) -> Optional[str]:
        """
        Retrieves the OpenAI Thread ID associated with a given user ID.

        Args:
            user_id: The unique identifier for the user (e.g., WhatsApp ID).

        Returns:
            The Thread ID if found, otherwise None.
        """
        thread_id = self._thread_map.get(user_id)
        if thread_id:
            logger.debug(f"Found existing thread_id {thread_id} for user_id {user_id}")
        else:
            logger.debug(f"No thread_id found for user_id {user_id}")
        return thread_id

    def add_thread(self, user_id: str, thread_id: str):
        """
        Stores the mapping between a user ID and a newly created Thread ID.

        Args:
            user_id: The unique identifier for the user.
            thread_id: The OpenAI Thread ID to associate with the user.
        """
        if user_id in self._thread_map:
             logger.warning(f"Overwriting existing thread_id {self._thread_map[user_id]} for user_id {user_id} with new thread_id {thread_id}")
        self._thread_map[user_id] = thread_id
        logger.info(f"Associated thread_id {thread_id} with user_id {user_id}")

    def remove_thread(self, user_id: str):
        """
        Removes the mapping for a given user ID (optional).

        Args:
            user_id: The unique identifier for the user.
        """
        if user_id in self._thread_map:
            removed_thread_id = self._thread_map.pop(user_id)
            logger.info(f"Removed thread mapping for user_id {user_id} (was thread_id {removed_thread_id})")
        else:
            logger.debug(f"Attempted to remove thread mapping for user_id {user_id}, but none existed.")

    # You might add methods to load/save from DB later if needed
    # async def load_from_db(self, db_client): ...
    # async def save_to_db(self, db_client, user_id, thread_id): ...