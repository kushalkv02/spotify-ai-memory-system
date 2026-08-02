from __future__ import annotations

from typing import Any

from ..models.conversation import Conversation
from ..models.message import Message
from .base_repository import BaseRepository


class ConversationRepository(BaseRepository):
    label = "Conversation"
    id_field = "conversation_id"

    def start_conversation(self, conversation: Conversation) -> dict[str, Any]:
        node = self.merge(conversation.to_dict())
        query = """
        MATCH (c:Conversation {conversation_id: $conversation_id})
        MATCH (u:User {user_id: $user_id})
        MERGE (u)-[:STARTED]->(c)
        """
        self.client.execute_write(
            query, {"conversation_id": conversation.conversation_id, "user_id": conversation.user_id}
        )
        return node

    def add_message(self, message: Message) -> dict[str, Any]:
        query = """
        MATCH (c:Conversation {conversation_id: $conversation_id})
        CREATE (m:Message {
            message_id: $message_id,
            role: $role,
            content: $content,
            created_at: $created_at
        })
        MERGE (c)-[:HAS_MESSAGE]->(m)
        RETURN m
        """
        data = message.to_dict()
        result = self.client.execute_write(query, data)
        return result[0]["m"] if result else {}
