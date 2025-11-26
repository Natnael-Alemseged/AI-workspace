"""Web Push Notification Service for offline notifications."""
import json
import os
from typing import Optional
from pywebpush import webpush, WebPushException

from app.core.logging import logger
from app.core.config import config


class NotificationService:
    """Service for sending Web Push notifications."""
    
    def __init__(self):
        """Initialize the notification service with VAPID keys."""
        self.vapid_private_key = config("VAPID_PRIVATE_KEY", default="")
        self.vapid_public_key = config("VAPID_PUBLIC_KEY", default="")
        self.vapid_claims = {
            "sub": config("VAPID_SUBJECT", default="mailto:admin@armadaden.com")
        }
    
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
        Send a Web Push notification to a subscriber.
        
        Args:
            subscription_info: Push subscription object with endpoint, keys
            title: Notification title
            body: Notification body text
            data: Optional additional data to send
            icon: Optional icon URL
            badge: Optional badge URL
            tag: Optional tag for notification grouping
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("VAPID keys not configured. Skipping push notification.")
            return False
        
        try:
            # Build notification payload
            payload = {
                "title": title,
                "body": body,
                "icon": icon or "/default-icon.png",
                "badge": badge or "/badge-icon.png",
                "tag": tag or "default",
                "data": data or {}
            }
            
            # Send push notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            logger.info(f"Push notification sent successfully: {title}")
            return True
            
        except WebPushException as e:
            logger.error(f"Web Push error: {e}")
            # If subscription is invalid (410 Gone), it should be removed
            if e.response and e.response.status_code == 410:
                logger.info("Subscription expired, should be removed from database")
            return False
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
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
        
        Args:
            subscription_info: Push subscription object
            sender_name: Name of the message sender
            message_preview: Preview of the message content
            topic_name: Name of the topic
            topic_id: ID of the topic
            
        Returns:
            True if notification sent successfully
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
        
        Args:
            subscription_info: Push subscription object
            sender_name: Name of the user who mentioned
            message_preview: Preview of the message content
            topic_name: Name of the topic
            topic_id: ID of the topic
            
        Returns:
            True if notification sent successfully
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
