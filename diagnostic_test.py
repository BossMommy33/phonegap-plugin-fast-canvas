#!/usr/bin/env python3
"""
Diagnostic test to investigate the failing tests
"""

import requests
import json
from datetime import datetime, timedelta
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

def test_message_limit_diagnostic():
    """Diagnostic test for message limit issue"""
    print("🔍 Diagnosing Message Limit Issue...")
    
    # Create a fresh user
    user_data = {
        "email": f"diagnostic_{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePassword123!",
        "name": "Diagnostic User"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Failed to create diagnostic user: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    token = data['access_token']
    user_info = data['user']
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Created user: {user_info['email']}")
    print(f"   Subscription plan: {user_info['subscription_plan']}")
    print(f"   Monthly messages used: {user_info['monthly_messages_used']}")
    print(f"   Monthly messages limit: {user_info['monthly_messages_limit']}")
    
    # Try to create one message
    future_time = datetime.utcnow() + timedelta(minutes=5)
    message_data = {
        "title": "Diagnostic Test Message",
        "content": "Testing message creation for diagnostic purposes.",
        "scheduled_time": future_time.isoformat() + "Z"
    }
    
    response = requests.post(f"{API_BASE}/messages", json=message_data, headers=headers)
    print(f"\n📝 Message creation attempt:")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 200:
        message_id = response.json()['id']
        print(f"   ✅ Message created with ID: {message_id}")
        
        # Clean up
        delete_response = requests.delete(f"{API_BASE}/messages/{message_id}", headers=headers)
        print(f"   🧹 Cleanup: {delete_response.status_code}")
    else:
        print(f"   ❌ Message creation failed")

def test_recurring_diagnostic():
    """Diagnostic test for recurring message issue"""
    print("\n🔍 Diagnosing Recurring Message Issue...")
    
    # Create a fresh user
    user_data = {
        "email": f"recurring_diag_{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePassword123!",
        "name": "Recurring Diagnostic User"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Failed to create recurring diagnostic user: {response.status_code}")
        return
    
    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create recurring message
    future_time = datetime.utcnow() + timedelta(hours=1)
    message_data = {
        "title": "Recurring Diagnostic Test",
        "content": "This should fail for free users.",
        "scheduled_time": future_time.isoformat() + "Z",
        "is_recurring": True,
        "recurring_pattern": "daily"
    }
    
    response = requests.post(f"{API_BASE}/messages", json=message_data, headers=headers)
    print(f"📝 Recurring message creation attempt:")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 403:
        if "recurring" in response.text.lower():
            print("   ✅ Recurring messages properly blocked for free users")
        else:
            print("   ⚠️  403 error but wrong message")
    else:
        print("   ❌ Recurring message should have been blocked")

if __name__ == "__main__":
    test_message_limit_diagnostic()
    test_recurring_diagnostic()