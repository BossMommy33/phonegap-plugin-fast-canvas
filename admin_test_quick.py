#!/usr/bin/env python3
"""
Quick test for Admin Finance Dashboard functionality
"""

import requests
import json
import uuid

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

def test_admin_functionality():
    print("🔗 Testing Admin Finance Dashboard at:", API_BASE)
    
    # Create admin user
    admin_data = {
        "email": "admin@zeitgesteuerte.de",
        "password": "AdminPassword123!",
        "name": "Admin User"
    }
    
    # Try to register or login
    response = requests.post(f"{API_BASE}/auth/register", json=admin_data)
    if response.status_code != 200:
        # Try login instead
        response = requests.post(f"{API_BASE}/auth/login", json={
            "email": admin_data['email'],
            "password": admin_data['password']
        })
    
    if response.status_code != 200:
        print("❌ Failed to create/login admin user")
        return False
    
    admin_token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print("✅ Admin user authenticated")
    
    # Test payout validation
    print("\n--- Testing Payout System ---")
    
    # Test excessive amount
    payout_request = {"amount": 1000.0, "description": "Test excessive payout"}
    response = requests.post(f"{API_BASE}/admin/payout", json=payout_request, headers=headers)
    print(f"Excessive amount test: HTTP {response.status_code}")
    if response.status_code == 400:
        print("✅ Excessive amount correctly rejected")
    else:
        print(f"❌ Expected 400, got {response.status_code}: {response.text}")
    
    # Test small amount
    payout_request = {"amount": 0.01, "description": "Test small amount"}
    response = requests.post(f"{API_BASE}/admin/payout", json=payout_request, headers=headers)
    print(f"Small amount test: HTTP {response.status_code}")
    if response.status_code in [200, 400]:
        print("✅ Small amount handled correctly")
    else:
        print(f"❌ Unexpected response: {response.status_code}: {response.text}")
    
    # Test role management
    print("\n--- Testing Role Management ---")
    
    # Create a regular user first
    user_data = {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code == 200:
        user_id = response.json()['user']['id']
        
        # Test invalid role
        role_update = {"role": "invalid_role"}
        response = requests.put(f"{API_BASE}/admin/users/{user_id}/role", json=role_update, headers=headers)
        print(f"Invalid role test: HTTP {response.status_code}")
        if response.status_code == 400:
            print("✅ Invalid role correctly rejected")
        else:
            print(f"❌ Expected 400, got {response.status_code}: {response.text}")
        
        # Test non-existent user
        fake_user_id = str(uuid.uuid4())
        role_update = {"role": "user"}
        response = requests.put(f"{API_BASE}/admin/users/{fake_user_id}/role", json=role_update, headers=headers)
        print(f"Non-existent user test: HTTP {response.status_code}")
        if response.status_code == 404:
            print("✅ Non-existent user correctly handled")
        else:
            print(f"❌ Expected 404, got {response.status_code}: {response.text}")
    else:
        print("❌ Failed to create test user for role management")
    
    print("\n🎯 Admin functionality quick test completed!")

if __name__ == "__main__":
    test_admin_functionality()