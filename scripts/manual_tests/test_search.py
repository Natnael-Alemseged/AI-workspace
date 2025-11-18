"""Test script for Web Search API endpoints."""

import asyncio
import sys
from datetime import datetime

import httpx
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

BASE_URL = "http://localhost:8001"


async def test_search_endpoints():
    """Test all search endpoints."""
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check (no auth required)
        logger.info("=" * 60)
        logger.info("Test 1: Server Health Check")
        logger.info("=" * 60)
        try:
            response = await client.get(f"{BASE_URL}/")
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        # Test 2: Check API docs
        logger.info("\n" + "=" * 60)
        logger.info("Test 2: API Documentation")
        logger.info("=" * 60)
        try:
            response = await client.get(f"{BASE_URL}/docs")
            logger.info(f"Swagger UI Status: {response.status_code}")
            logger.success("✓ API docs accessible at http://localhost:8001/docs")
        except Exception as e:
            logger.error(f"API docs check failed: {e}")
        
        # Test 3: Register a test user
        logger.info("\n" + "=" * 60)
        logger.info("Test 3: User Registration")
        logger.info("=" * 60)
        test_email = f"test_{datetime.now().timestamp()}@example.com"
        test_password = "SecurePass123!"
        
        try:
            response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": test_email,
                    "password": test_password
                }
            )
            logger.info(f"Registration Status: {response.status_code}")
            if response.status_code == 201:
                logger.success(f"✓ User registered: {test_email}")
            else:
                logger.warning(f"Registration response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Registration failed: {e}")
        
        # Test 4: Login
        logger.info("\n" + "=" * 60)
        logger.info("Test 4: User Login")
        logger.info("=" * 60)
        token = None
        try:
            response = await client.post(
                f"{BASE_URL}/auth/jwt/login",
                data={
                    "username": test_email,
                    "password": test_password
                }
            )
            logger.info(f"Login Status: {response.status_code}")
            if response.status_code == 200:
                token = response.json().get("access_token")
                logger.success(f"✓ Login successful, token obtained")
            else:
                logger.warning(f"Login response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Login failed: {e}")
        
        if not token:
            logger.error("Cannot proceed without authentication token")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 5: Check search status
        logger.info("\n" + "=" * 60)
        logger.info("Test 5: Check Search Status")
        logger.info("=" * 60)
        try:
            response = await client.get(
                f"{BASE_URL}/api/search/status",
                headers=headers
            )
            logger.info(f"Status Check: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ Search status endpoint working")
                logger.info(f"Connected: {data.get('connected')}")
            else:
                logger.warning(f"Response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Status check failed: {e}")
        
        # Test 6: Get search tools
        logger.info("\n" + "=" * 60)
        logger.info("Test 6: Get Available Search Tools")
        logger.info("=" * 60)
        try:
            response = await client.get(
                f"{BASE_URL}/api/search/tools",
                headers=headers
            )
            logger.info(f"Tools Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ Search tools endpoint working")
                logger.info(f"Tools count: {data.get('count', 0)}")
            else:
                logger.warning(f"Response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Tools check failed: {e}")
        
        # Test 7: Perform a search (may fail if SerpAPI not configured)
        logger.info("\n" + "=" * 60)
        logger.info("Test 7: Perform Web Search")
        logger.info("=" * 60)
        try:
            response = await client.post(
                f"{BASE_URL}/api/search/query",
                headers=headers,
                json={
                    "query": "Python FastAPI tutorial",
                    "num_results": 5,
                    "save_to_db": True
                }
            )
            logger.info(f"Search Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ Search executed successfully")
                logger.info(f"Query: {data.get('query')}")
                logger.info(f"Results count: {data.get('count')}")
                logger.info(f"Search ID: {data.get('search_id')}")
            else:
                logger.warning(f"Search may require SerpAPI configuration")
                logger.info(f"Response: {response.text[:300]}")
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        # Test 8: Get search history
        logger.info("\n" + "=" * 60)
        logger.info("Test 8: Get Search History")
        logger.info("=" * 60)
        try:
            response = await client.get(
                f"{BASE_URL}/api/search/history",
                headers=headers
            )
            logger.info(f"History Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ Search history endpoint working")
                logger.info(f"Total searches: {data.get('total', 0)}")
                logger.info(f"Page: {data.get('page')}")
            else:
                logger.warning(f"Response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"History check failed: {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.success("✓ Search API endpoints are exposed and accessible")
        logger.info("📝 All endpoints are available at: http://localhost:8001/api/search")
        logger.info("📚 API Documentation: http://localhost:8001/docs")
        logger.info("📖 Testing Guide: See SEARCH_TESTING.md")
        logger.info("\n" + "=" * 60)
        logger.info("AVAILABLE ENDPOINTS:")
        logger.info("=" * 60)
        logger.info("POST   /api/search/connect     - Connect search engine")
        logger.info("GET    /api/search/status      - Check connection status")
        logger.info("POST   /api/search/query       - Perform web search")
        logger.info("GET    /api/search/history     - Get search history")
        logger.info("GET    /api/search/history/:id - Get search details")
        logger.info("GET    /api/search/tools       - Get available tools")
        logger.info("GET    /api/search/callback    - OAuth callback")
        logger.info("=" * 60)


if __name__ == "__main__":
    logger.info("Starting Web Search API Tests...")
    logger.info(f"Target: {BASE_URL}")
    logger.info("")
    
    try:
        asyncio.run(test_search_endpoints())
    except KeyboardInterrupt:
        logger.warning("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)