#!/usr/bin/env python3
"""
Diagnostic test to check user subscription plans and bulk message access
"""

import requests
import json
from datetime import datetime, timedelta

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

def test_user_subscription_plan(email, password, expected_plan):
    """Test a specific user's subscription plan"""
    print(f"\n🔍 Testing user: {email}")
    
    # Login
    login_data = {"email": email, "password": password}
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json()['access_token']
    user_info = response.json()['user']
    
    print(f"✅ Login successful")
    print(f"   User ID: {user_info['id']}")
    print(f"   Subscription Plan: {user_info['subscription_plan']}")
    print(f"   Monthly Messages Limit: {user_info['monthly_messages_limit']}")
    print(f"   Monthly Messages Used: {user_info['monthly_messages_used']}")
    
    # Get profile to double-check
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/auth/me", headers=headers)
    
    if response.status_code == 200:
        profile = response.json()
        print(f"   Profile Plan: {profile['subscription_plan']}")
        
        # Test bulk messages access
        base_time = datetime.utcnow() + timedelta(minutes=60)
        bulk_request = {
            "messages": [
                {
                    "title": "Diagnostic Test Message",
                    "content": "Testing bulk message access",
                    "scheduled_time": base_time.isoformat() + "Z"
                }
            ],
            "time_interval": 5
        }
        
        response = requests.post(f"{API_BASE}/messages/bulk", json=bulk_request, headers=headers)
        print(f"   Bulk Messages Test: HTTP {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        else:
            print(f"   Success: {response.json()}")
    
    return True

def main():
    print("🔍 DIAGNOSTIC: User Subscription Plans and Bulk Message Access")
    print("=" * 70)
    
    # Test known users
    test_users = [
        ("admin@zeitgesteuerte.de", "admin123", "admin"),
        ("demo@zeitgesteuerte.de", "Demo123!", "premium")
    ]
    
    for email, password, expected_plan in test_users:
        test_user_subscription_plan(email, password, expected_plan)

if __name__ == "__main__":
    main()