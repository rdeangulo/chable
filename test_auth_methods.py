#!/usr/bin/env python3
"""
Test Different Authentication Methods for Lasso CRM
==================================================

This script tests various authentication methods to find the correct one
for the Lasso CRM API.
"""

import asyncio
import httpx
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lasso CRM Configuration - Get from environment variables
LASSO_API_KEY = os.getenv("LASSO_API_KEY_YUCATAN")

PROJECT_ID = 24610
CLIENT_ID = 2589

# Test endpoints and authentication methods
TEST_CONFIGS = [
    {
        "name": "Bearer Token - Standard API",
        "url": "https://api.lassocrm.com/v1/registrants",
        "headers": {
            "Authorization": f"Bearer {LASSO_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    },
    {
        "name": "API Key Header - Standard API",
        "url": "https://api.lassocrm.com/v1/registrants",
        "headers": {
            "X-API-Key": LASSO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    },
    {
        "name": "API Key Header - Alternative",
        "url": "https://api.lassocrm.com/v1/registrants",
        "headers": {
            "API-Key": LASSO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    },
    {
        "name": "Token Header",
        "url": "https://api.lassocrm.com/v1/registrants",
        "headers": {
            "X-Auth-Token": LASSO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    },
    {
        "name": "Lead Capture Endpoint",
        "url": "https://api.lassocrm.com/v1/lead-capture",
        "headers": {
            "Authorization": f"Bearer {LASSO_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    },
    {
        "name": "Lead Capture with API Key",
        "url": "https://api.lassocrm.com/v1/lead-capture",
        "headers": {
            "X-API-Key": LASSO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    }
]

# Test lead data
TEST_LEAD = {
    "firstName": "Test",
    "lastName": "Lead",
    "email": "test@example.com",
    "phone": "+1234567890",
    "source": "API Test",
    "projectId": PROJECT_ID,
    "notes": "This is a test lead created via API"
}


async def test_authentication_method(config):
    """Test a specific authentication method."""
    print(f"\n🔍 Testing: {config['name']}")
    print(f"   URL: {config['url']}")
    print(f"   Headers: {config['headers']}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test GET request first
            response = await client.get(config['url'], headers=config['headers'])
            print(f"   GET Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ GET Success!")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   Response: {response.text}")
            else:
                print(f"   ❌ GET Failed: {response.text}")
            
            # Test POST request
            response = await client.post(
                config['url'], 
                json=TEST_LEAD, 
                headers=config['headers']
            )
            print(f"   POST Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"   ✅ POST Success!")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   Response: {response.text}")
            else:
                print(f"   ❌ POST Failed: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


async def main():
    """Test all authentication methods."""
    print("🧪 Testing Different Authentication Methods for Lasso CRM")
    print("="*60)
    
    # Check if API key is available
    if not LASSO_API_KEY:
        print("❌ Error: LASSO_API_KEY_YUCATAN environment variable not set!")
        print("Please set the environment variable with your Lasso API key.")
        return
    
    for config in TEST_CONFIGS:
        await test_authentication_method(config)
        print("-" * 60)
    
    print("\n✅ Authentication method testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
