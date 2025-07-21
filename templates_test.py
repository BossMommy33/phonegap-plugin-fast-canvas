#!/usr/bin/env python3
"""
Test templates endpoint to diagnose the 500 error
"""

import requests
import json

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BACKEND_URL = get_backend_url()
API_BASE = f"{BACKEND_URL}/api"

def test_templates_endpoint():
    """Test templates endpoint"""
    print("🔍 Testing Templates Endpoint...")
    
    # Login as admin (business plan)
    login_data = {"email": "admin@zeitgesteuerte.de", "password": "admin123"}
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Logged in as admin")
    
    # Test GET templates
    print("\n📋 Testing GET /api/templates...")
    response = requests.get(f"{API_BASE}/templates", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: Found {len(data.get('user_templates', []))} user templates and {len(data.get('public_templates', []))} public templates")
    else:
        print(f"   Error: {response.text}")
    
    # Test POST template
    print("\n📝 Testing POST /api/templates...")
    template_data = {
        "name": "Test Template",
        "title": "Test Title",
        "content": "Test content for template",
        "category": "general",
        "is_public": False
    }
    
    response = requests.post(f"{API_BASE}/templates", json=template_data, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        template = response.json()
        template_id = template['id']
        print(f"   Success: Created template with ID {template_id}")
        
        # Test GET templates again to see if it causes the error
        print("\n📋 Testing GET /api/templates after creating template...")
        response = requests.get(f"{API_BASE}/templates", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        
        # Clean up
        delete_response = requests.delete(f"{API_BASE}/templates/{template_id}", headers=headers)
        print(f"   🧹 Cleanup: {delete_response.status_code}")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_templates_endpoint()