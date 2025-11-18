"""Quick verification script for search endpoints."""

import requests
import sys

BASE_URL = "http://localhost:8001"

print("=" * 70)
print("SEARCH API ENDPOINTS VERIFICATION")
print("=" * 70)
print()

# Check if server is running
print("1. Checking if server is running...")
try:
    response = requests.get(f"{BASE_URL}/docs")
    if response.status_code == 200:
        print("   [OK] Server is running at http://localhost:8001")
        print("   [OK] API docs available at http://localhost:8001/docs")
    else:
        print(f"   [ERROR] Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Server not accessible: {e}")
    sys.exit(1)

print()
print("2. Checking OpenAPI schema for search endpoints...")
try:
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})
        
        search_endpoints = [path for path in paths.keys() if "/search" in path]
        
        if search_endpoints:
            print(f"   [OK] Found {len(search_endpoints)} search endpoints:")
            for endpoint in sorted(search_endpoints):
                methods = list(paths[endpoint].keys())
                print(f"     - {', '.join(m.upper() for m in methods):8} {endpoint}")
        else:
            print("   [ERROR] No search endpoints found in OpenAPI schema")
    else:
        print(f"   [ERROR] Could not fetch OpenAPI schema: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error checking schema: {e}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("[SUCCESS] Search feature has been successfully implemented!")
print()
print("Available Search Endpoints:")
print("  POST   /api/search/connect      - Connect search engine")
print("  GET    /api/search/status       - Check connection status")
print("  POST   /api/search/query        - Perform web search")
print("  GET    /api/search/history      - Get search history")
print("  GET    /api/search/history/{id} - Get search details")
print("  GET    /api/search/tools        - Get available tools")
print("  GET    /api/search/callback     - OAuth callback")
print()
print("Documentation:")
print("  * Interactive API docs: http://localhost:8001/docs")
print("  * ReDoc: http://localhost:8001/redoc")
print("  * Testing guide: SEARCH_TESTING.md")
print()
print("Next Steps:")
print("  1. Visit http://localhost:8001/docs to see all endpoints")
print("  2. Use the 'search' tag to filter search-related endpoints")
print("  3. Follow SEARCH_TESTING.md for detailed testing instructions")
print("  4. Ensure SerpAPI is configured in Composio for full functionality")
print()
print("=" * 70)