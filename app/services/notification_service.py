"""FCM Push Notification Service for offline notifications."""
from typing import Optional

from app.core.logging import logger
from app.services.fcm_service import fcm_service


class NotificationService:
    """Service for sending notifications via FCM."""
    
    async def send_notification(
        self,
        subscription_info: dict,
        title: str,
        body: str,
        data: Optional[dict] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """
        Send a notification to a subscriber via FCM.
        
        Args:
            subscription_info: FCM token (string or dict with 'token' or 'endpoint')
            title: Notification title
            body: Notification body text
            data: Optional additional data to send
            icon: Optional icon URL
            badge: Optional badge URL (unused in FCM)
            tag: Optional tag for notification grouping (unused in FCM)
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        # Extract FCM token from various formats
        fcm_token = None
        if isinstance(subscription_info, str):
            fcm_token = subscription_info
        elif isinstance(subscription_info, dict):
            # Try different keys where token might be stored
            fcm_token = subscription_info.get("token") or subscription_info.get("endpoint")
        
        if not fcm_token:
            logger.warning("No FCM token found in subscription_info")
            return False
        
        # Send via FCM
        return fcm_service.send_notification(
            token=fcm_token,
            title=title,
            body=body,
            data=data,
            image=icon
        )
    
    async def send_message_notification(
        self,
        subscription_info: dict,
        sender_name: str,
        message_preview: str,
        topic_name: str,
        topic_id: str
    ) -> bool:
        """
        Send a notification for a new message.
        """
        return await self.send_notification(
            subscription_info=subscription_info,
            title=f"New message from {sender_name}",
            body=f"{topic_name}: {message_preview}",
            data={
                "type": "new_message",
                "topic_id": topic_id,
                "sender_name": sender_name
            },
            tag=f"topic_{topic_id}"
        )
    
    async def send_mention_notification(
        self,
        subscription_info: dict,
        sender_name: str,
        message_preview: str,
        topic_name: str,
        topic_id: str
    ) -> bool:
        """
        Send a notification for a mention.
        """
        return await self.send_notification(
            subscription_info=subscription_info,
            title=f"{sender_name} mentioned you",
            body=f"{topic_name}: {message_preview}",
            data={
                "type": "mention",
                "topic_id": topic_id,
                "sender_name": sender_name
            },
            tag=f"mention_{topic_id}"
        )


# Global notification service instance
notification_service = NotificationService()
