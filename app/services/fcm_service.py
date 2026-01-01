"""
Firebase Cloud Messaging (FCM) Service.
Handles initialization and sending of push notifications via FCM.
"""
import os
import asyncio
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.logging import logger
from app.core.config import config

class FCMService:
    """Service for sending FCM notifications."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FCMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._app = None
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self._app = firebase_admin.get_app()
                return

            # Path to service account key
            # Try to find the file in the root directory
            cred_file = "firebase-service-account.json"
            
            # Check if file exists
            if not os.path.exists(cred_file):
                # Try looking in parent directory or absolute path if configured
                configured_path = config("FIREBASE_CREDENTIALS_PATH", default=None)
                if configured_path and os.path.exists(configured_path):
                    cred_file = configured_path
                else:
                    logger.warning(f"Firebase credentials file not found: {cred_file}")
                    return

            cred = credentials.Certificate(cred_file)
            self._app = firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin SDK: {e}")

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: dict = None,
        image: str = None
    ) -> bool:
        """
        Send a notification to a specific device token.
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional data payload (all values must be strings)
            image: Optional image URL
            
        Returns:
            True if successful, False otherwise
        """
        if not self._app:
            # Try to initialize again
            self._initialize_app()
            if not self._app:
                logger.warning("Firebase not initialized. Skipping notification.")
                return False
                
        try:
            # Ensure all data values are strings (FCM requirement)
            str_data = {}
            if data:
                for k, v in data.items():
                    str_data[str(k)] = str(v)
            
            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image
                ),
                data=str_data,
                token=token
            )
            
            # Send message in a thread to avoid blocking the event loop
            # Firebase Admin SDK is synchronous, so we need to run it in a thread
            response = await asyncio.to_thread(messaging.send, message)
            logger.info(f"FCM notification sent: {response}")
            return True
            
        except firebase_admin.messaging.UnregisteredError:
            logger.info(f"FCM token invalid or expired: {token}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return False

    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict = None,
        image: str = None
    ) -> int:
        """
        Send a notification to multiple device tokens.
        
        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Optional data payload
            image: Optional image URL
            
        Returns:
            Number of successful messages
        """
        if not self._app or not tokens:
            return 0
            
        try:
            # Ensure all data values are strings
            str_data = {}
            if data:
                for k, v in data.items():
                    str_data[str(k)] = str(v)
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image
                ),
                data=str_data,
                tokens=tokens
            )
            
            # Send multicast in a thread to avoid blocking the event loop
            batch_response = await asyncio.to_thread(messaging.send_multicast, message)
            
            if batch_response.failure_count > 0:
                logger.warning(f"FCM multicast failed for {batch_response.failure_count} tokens")
                # Could handle invalid tokens here (batch_response.responses[i].exception)
                
            logger.info(f"FCM multicast sent: {batch_response.success_count} successful")
            return batch_response.success_count
            
        except Exception as e:
            logger.error(f"Error sending FCM multicast: {e}")
            return 0

# Global instance
fcm_service = FCMService()
