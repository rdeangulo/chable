#!/usr/bin/env python3
"""
Test Lasso CRM API Connection
============================

Simple script to test the connection to Lasso CRM API
and verify the API key is working.
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

PROJECT_ID = 24610  # Yucatan project
CLIENT_ID = 2589

# Test endpoints
LASSO_BASE_URL = "https://api.lassocrm.com"
TEST_ENDPOINTS = [
    f"{LASSO_BASE_URL}/v1/registrants",
    f"{LASSO_BASE_URL}/v1/projects/{PROJECT_ID}",
    f"{LASSO_BASE_URL}/v1/health",
    f"{LASSO_BASE_URL}/v1/status"
]


async def test_api_connection():
    """Test the Lasso CRM API connection."""
    print("🔍 Testing Lasso CRM API Connection...")
    print("="*50)
    
    # Check if API key is available
    if not LASSO_API_KEY:
        print("❌ Error: LASSO_API_KEY_YUCATAN environment variable not set!")
        print("Please set the environment variable with your Lasso API key.")
        return
    
    headers = {
        "Authorization": f"Bearer {LASSO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in TEST_ENDPOINTS:
            try:
                print(f"\n📡 Testing: {endpoint}")
                
                # Try GET request
                response = await client.get(endpoint, headers=headers)
                
                print(f"   Status: {response.status_code}")
                print(f"   Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"   Response: {response.text}")
                else:
                    print(f"   Error Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*50)
    print("✅ API Connection Test Complete")


async def test_simple_lead_creation():
    """Test creating a simple lead."""
    print("\n🧪 Testing Simple Lead Creation...")
    print("="*50)
    
    # Check if API key is available
    if not LASSO_API_KEY:
        print("❌ Error: LASSO_API_KEY_YUCATAN environment variable not set!")
        return
    
    # Simple test lead data
    test_lead = {
        "firstName": "Test",
        "lastName": "Lead",
        "email": "test@example.com",
        "phone": "+1234567890",
        "source": "API Test",
        "projectId": PROJECT_ID,
        "notes": "This is a test lead created via API",
        "tags": ["Test", "API", "Yucatan"]
    }
    
    headers = {
        "Authorization": f"Bearer {LASSO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LASSO_BASE_URL}/v1/registrants",
                json=test_lead,
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code in [200, 201]:
                print("✅ Test lead creation successful!")
            else:
                print("❌ Test lead creation failed!")
                
    except Exception as e:
        print(f"❌ Error creating test lead: {str(e)}")


async def main():
    """Main test function."""
    try:
        await test_api_connection()
        await test_simple_lead_creation()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
