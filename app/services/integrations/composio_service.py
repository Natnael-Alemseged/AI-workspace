"""Composio service for integrating Gmail and Web Search tools."""
#composio_service.py
import json
from typing import Any, Dict, List, Optional

from composio import Composio
from loguru import logger

from app.core.config import COMPOSIO_API_KEY, COMPOSIO_AUTH_CONFIG_ID


class ComposioService:
    """Service for managing Composio integrations."""

    def __init__(self):
        """Initialize Composio service."""
        self._composio_client = None

    @property
    def composio_client(self):
        """Lazy initialization of Composio client."""
        if self._composio_client is None:
            if not COMPOSIO_API_KEY:
                raise ValueError("COMPOSIO_API_KEY is not set in environment variables")
            logger.info("Initializing Composio client...")
            self._composio_client = Composio(apikey=COMPOSIO_API_KEY)
        return self._composio_client


    def get_gmail_tools(self, user_id: str) -> List[Any]:
        """Get Gmail tools for a specific user entity (OpenAI format)."""
        try:
            logger.info(f"Getting Gmail tools for user {user_id}")
            tools = self.composio_client.tools.get(
                user_id=user_id,
                toolkits=["GMAIL"]
            )
            logger.info(f"Retrieved {len(tools)} Gmail tools for user {user_id}")
            return tools
        except Exception as e:
            logger.error(f"Error getting Gmail tools: {e}", exc_info=True)
            raise

    async def get_web_search_tools(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get web search tools (SerpAPI) for a specific user entity."""
        try:
            logger.info(f"Getting web search tools for entity {entity_id}")
            tools = self.composio_client.tools.get(apps=["serpapi"], entity_id=entity_id)
            logger.info(f"Retrieved {len(tools)} web search tools for entity {entity_id}")
            return tools
        except Exception as e:
            logger.error(f"Error getting web search tools: {e}", exc_info=True)
            raise

    async def execute_gmail_action(
        self,
        entity_id: str,
        action_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a Gmail action using Composio."""
        try:
            logger.info(f"Executing Gmail action {action_name} for entity {entity_id}")

            action_str = (
                getattr(action_name, "value", None)
                or getattr(action_name, "name", None)
                or str(action_name)
            )

            result = self.composio_client.tools.execute(
                action=action_str,
                params=params,
                entity_id=entity_id,
            )

            logger.info(f"Executed Gmail action {action_name} successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing Gmail action {action_name}: {e}", exc_info=True)
            raise

    async def execute_web_search(
        self,
        entity_id: str,
        query: str,
        num_results: int = 10,
    ) -> Dict[str, Any]:
        """Execute a web search using Composio."""
        try:
            logger.info(f"Executing web search for query: {query}")
            result = self.composio_client.tools.execute(
                action="SERPAPI_SEARCH",
                params={"query": query, "num": num_results},
                entity_id=entity_id,
            )
            logger.info(f"Executed web search successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing web search: {e}", exc_info=True)
            raise

    def connect_gmail_account(
        self,
        user_id: str,
        auth_config_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initiate OAuth connection for a user's Gmail account."""
        try:
            logger.info(f"Connecting Gmail account for user={user_id}")

            connection_request = self.composio_client.connected_accounts.link(
                user_id=user_id,
                auth_config_id=auth_config_id or COMPOSIO_AUTH_CONFIG_ID
            )

            logger.info(f"Initiated Gmail connection for user {user_id}")
            return {
                "connection_url": connection_request.redirect_url,
                "entity_id": user_id,
                "status": connection_request.status
            }
        except Exception as e:
            logger.error(f"Error connecting Gmail account: {e}", exc_info=True)
            raise

    def get_gmail_status(self, user_id: str) -> Dict[str, Any]:
        """Get Gmail connection status for a user."""
        try:
            accounts = self.composio_client.connected_accounts.list(
                user_ids=[user_id],
                toolkit_slugs=["GMAIL"],
            )

            for account in accounts.items:
                if account.status == "ACTIVE":
                    return {
                        "connected": True,
                        "entity_id": account.id,
                        "account": account
                    }
                logger.warning(f"Inactive account {account.id} found for user id: {user_id}")
            
            return {"connected": False, "entity_id": user_id}
        except Exception as e:
            logger.error(f"Error getting Gmail status: {e}", exc_info=True)
            raise

    def send_email(
        self,
        user_id: str,
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        extra_recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an email via Gmail using Composio."""
        try:
            logger.info(f"Sending email for user {user_id}")

            # Get active Gmail account
            accounts = self.composio_client.connected_accounts.list(
                user_ids=[user_id],
                toolkit_slugs=["GMAIL"]
            )
            active_account = next((acc for acc in accounts.items if acc.status == "ACTIVE"), None)
            if not active_account:
                raise ValueError("No active Gmail account connected")

            payload = {
                "recipient_email": recipient_email,
                "subject": subject,
                "body": body,
                "cc": cc or [],
                "bcc": bcc or [],
                "extra_recipients": extra_recipients or [],
            }

            result = self.composio_client.tools.execute(
                user_id=user_id,
                connected_account_id=active_account.id,
                slug="GMAIL_SEND_EMAIL",
                version="20251107_00",
                arguments=payload
            )

            logger.info(f"Email sent successfully for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            raise

    def read_emails(
        self,
        user_id: str,
        limit: int = 5,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch emails for a user."""
        try:
            logger.info(f"Fetching emails for user {user_id}")

            arguments = {
                "ids_only": False,
                "include_payload": True,
                "include_spam_trash": False,
                "max_results": limit,
                "page_token": None,
                "query": query,
                "user_id": "me",
                "verbose": True
            }

            result = self.composio_client.tools.execute(
                user_id=user_id,
                slug="GMAIL_FETCH_EMAILS",
                arguments=arguments,
                version="20251107_00"
            )

            return {
                "status": "success",
                "emails": result.get("data", {}).get("messages", []),
                "count": len(result.get("data", {}).get("messages", [])),
            }
        except Exception as e:
            logger.error(f"Error reading emails: {e}", exc_info=True)
            raise


# Singleton instance
composio_service = ComposioService()
