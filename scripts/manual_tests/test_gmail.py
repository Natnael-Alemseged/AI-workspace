"""
Test script for Gmail integration via Composio.

This script demonstrates how to:
1. Connect a Gmail account
2. Check connection status
3. Read emails
4. Send emails
5. Create drafts

Usage:
    python test_gmail.py
"""

import asyncio
import sys
from typing import Optional

import httpx
from loguru import logger

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api"


class GmailTester:
    """Test Gmail integration endpoints."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token: Optional[str] = None
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def register_user(self, email: str, password: str) -> dict:
        """Register a new user."""
        logger.info(f"Registering user: {email}")
        
        response = await self.client.post(
            f"{self.base_url}/auth/register",
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 201:
            logger.success("User registered successfully")
            return response.json()
        else:
            logger.error(f"Registration failed: {response.text}")
            return {}
    
    async def login(self, email: str, password: str) -> bool:
        """Login and get access token."""
        logger.info(f"Logging in as: {email}")
        
        response = await self.client.post(
            f"{self.base_url}/auth/jwt/login",
            data={
                "username": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"
            logger.success("Login successful")
            return True
        else:
            logger.error(f"Login failed: {response.text}")
            return False
    
    async def connect_gmail(self, redirect_url: str = "http://localhost:8002/api/gmail/callback") -> dict:
        """Initiate Gmail connection."""
        logger.info("Connecting Gmail account...")
        
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/gmail/connect",
            json={"redirect_url": redirect_url}
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success("Gmail connection initiated")
            logger.info(f"Please visit this URL to authorize: {data.get('connection_url')}")
            return data
        else:
            logger.error(f"Gmail connection failed: {response.text}")
            return {}
    
    async def check_gmail_status(self) -> dict:
        """Check Gmail connection status."""
        logger.info("Checking Gmail status...")
        
        response = await self.client.get(
            f"{self.base_url}{API_PREFIX}/gmail/status"
        )
        
        if response.status_code == 200:
            data = response.json()
            is_connected = data.get("connected", False)
            
            if is_connected:
                logger.success("Gmail is connected")
            else:
                logger.warning("Gmail is not connected")
            
            return data
        else:
            logger.error(f"Status check failed: {response.text}")
            return {}
    
    async def get_gmail_tools(self) -> dict:
        """Get available Gmail tools."""
        logger.info("Getting Gmail tools...")
        
        response = await self.client.get(
            f"{self.base_url}{API_PREFIX}/gmail/tools"
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success(f"Retrieved {data.get('count', 0)} Gmail tools")
            return data
        else:
            logger.error(f"Failed to get tools: {response.text}")
            return {}
    
    async def read_emails(self, max_results: int = 5, query: str = "is:unread") -> dict:
        """Read emails from Gmail."""
        logger.info(f"Reading emails with query: {query}")
        
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/gmail/read",
            json={
                "max_results": max_results,
                "query": query
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success(f"Retrieved {data.get('count', 0)} emails")
            return data
        else:
            logger.error(f"Failed to read emails: {response.text}")
            return {}
    
    async def send_email(self, to_email: str, subject: str, body: str) -> dict:
        """Send an email via Gmail."""
        logger.info(f"Sending email to: {to_email}")
        
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/gmail/send",
            json={
                "to": [{"email": to_email}],
                "subject": subject,
                "body": body
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success("Email sent successfully")
            return data
        else:
            logger.error(f"Failed to send email: {response.text}")
            return {}
    
    async def create_draft(self, to_email: str, subject: str, body: str) -> dict:
        """Create an email draft in Gmail."""
        logger.info(f"Creating draft for: {to_email}")
        
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/gmail/draft",
            json={
                "to": [{"email": to_email}],
                "subject": subject,
                "body": body
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success("Draft created successfully")
            return data
        else:
            logger.error(f"Failed to create draft: {response.text}")
            return {}


async def main():
    """Run Gmail integration tests."""
    logger.info("Starting Gmail integration tests...")
    
    tester = GmailTester()
    
    try:
        # Test credentials
        test_email = "test@example.com"
        test_password = "testpassword123"
        
        # Step 1: Register or login
        logger.info("\n=== Step 1: Authentication ===")
        await tester.register_user(test_email, test_password)
        
        if not await tester.login(test_email, test_password):
            logger.error("Authentication failed. Exiting.")
            return
        
        # Step 2: Connect Gmail
        logger.info("\n=== Step 2: Connect Gmail ===")
        connection_data = await tester.connect_gmail()
        
        if connection_data:
            logger.info("\n" + "="*60)
            logger.info("IMPORTANT: Please complete the OAuth flow:")
            logger.info(f"1. Visit: {connection_data.get('connection_url')}")
            logger.info("2. Authorize Gmail access")
            logger.info("3. Wait for redirect to complete")
            logger.info("="*60 + "\n")
            
            input("Press Enter after completing OAuth authorization...")
        
        # Step 3: Check Gmail status
        logger.info("\n=== Step 3: Check Gmail Status ===")
        status = await tester.check_gmail_status()
        
        if not status.get("connected"):
            logger.warning("Gmail is not connected. Some tests will be skipped.")
        
        # Step 4: Get available tools
        logger.info("\n=== Step 4: Get Gmail Tools ===")
        tools = await tester.get_gmail_tools()
        
        if tools.get("tools"):
            logger.info("Available Gmail actions:")
            for i, tool in enumerate(tools["tools"][:5], 1):
                logger.info(f"  {i}. {tool.get('function', {}).get('name', 'Unknown')}")
        
        # Step 5: Read emails (if connected)
        if status.get("connected"):
            logger.info("\n=== Step 5: Read Emails ===")
            emails = await tester.read_emails(max_results=5, query="is:unread")
            
            if emails.get("emails"):
                logger.info(f"Found {len(emails['emails'])} unread emails")
        
        # Step 6: Create a draft (if connected)
        if status.get("connected"):
            logger.info("\n=== Step 6: Create Email Draft ===")
            draft = await tester.create_draft(
                to_email="recipient@example.com",
                subject="Test Email from Armada Den",
                body="This is a test email created via Composio integration."
            )
            
            if draft.get("status") == "success":
                logger.success(f"Draft created with ID: {draft.get('draft_id')}")
        
        logger.info("\n=== Tests Completed ===")
        logger.success("All tests finished successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tester.close()


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run tests
    asyncio.run(main())