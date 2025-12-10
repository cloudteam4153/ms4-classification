"""Client for Sanjay's Integrations Microservice (ms2)"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import httpx
from datetime import datetime

from models.message import MessageRead, ChannelType
from utils.config import config


class IntegrationsClient:
    """Client to interact with Sanjay's Integrations Microservice"""
    
    def __init__(self):
        self.base_url = config.INTEGRATIONS_SERVICE_URL
        self.timeout = 30.0
        print(f"📡 Integrations client initialized: {self.base_url}")
    
    async def get_messages(
        self,
        token: Optional[str] = None,
        limit: int = 50,
        channel: Optional[str] = None
    ) -> List[MessageRead]:
        """
        Fetch messages from Integrations service
        
        Args:
            token: JWT token for authentication
            limit: Maximum number of messages to fetch
            channel: Filter by channel (gmail/slack)
            
        Returns:
            List of MessageRead objects
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        params = {"limit": limit}
        if channel:
            params["channel"] = channel
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/messages",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                messages = []
                
                for msg_data in data:
                    # Convert to MessageRead model
                    messages.append(self._parse_message(msg_data))
                
                return messages
                
        except httpx.HTTPError as e:
            print(f"Error fetching messages from integrations service: {e}")
            return []
    
    async def get_message_by_id(
        self,
        message_id: UUID,
        token: Optional[str] = None
    ) -> Optional[MessageRead]:
        """
        Fetch a single message by ID
        
        Args:
            message_id: Message UUID
            token: JWT token for authentication
            
        Returns:
            MessageRead object or None if not found
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/messages/{message_id}",
                    headers=headers
                )
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                data = response.json()
                return self._parse_message(data)
                
        except httpx.HTTPError as e:
            print(f"Error fetching message {message_id}: {e}")
            return None
    
    async def get_messages_by_ids(
        self,
        message_ids: List[UUID],
        token: Optional[str] = None
    ) -> List[MessageRead]:
        """
        Fetch multiple messages by IDs
        
        Args:
            message_ids: List of message UUIDs
            token: JWT token for authentication
            
        Returns:
            List of MessageRead objects
        """
        messages = []
        
        # Fetch messages in parallel
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            for msg_id in message_ids:
                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                
                tasks.append(
                    client.get(
                        f"{self.base_url}/messages/{msg_id}",
                        headers=headers
                    )
                )
            
            # Wait for all requests
            responses = await httpx.AsyncClient().gather(*tasks)
            
            for response in responses:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        messages.append(self._parse_message(data))
                    except Exception as e:
                        print(f"Error parsing message: {e}")
        
        return messages
    
    def _parse_message(self, data: Dict[str, Any]) -> MessageRead:
        """Parse message data from API response"""
        # Handle different possible field names
        msg_id = data.get("msg_id") or data.get("message_id") or data.get("id")
        
        # Parse datetime fields
        received_at = data.get("received_at")
        if isinstance(received_at, str):
            received_at = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif not created_at:
            created_at = datetime.utcnow()
        
        # Handle channel enum
        channel_str = data.get("channel", "gmail")
        try:
            channel = ChannelType(channel_str)
        except ValueError:
            channel = ChannelType.GMAIL
        
        return MessageRead(
            msg_id=msg_id,
            account_id=data.get("account_id"),
            external_id=data.get("external_id", ""),
            channel=channel,
            sender=data.get("sender", ""),
            subject=data.get("subject"),
            snippet=data.get("snippet", ""),
            received_at=received_at,
            raw_ref=data.get("raw_ref"),
            priority=data.get("priority"),
            created_at=created_at
        )


# Singleton instance
integrations_client = IntegrationsClient()

