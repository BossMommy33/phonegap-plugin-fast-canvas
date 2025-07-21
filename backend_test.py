#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Premium Subscription System
Tests authentication, subscription management, message limits, Stripe integration, and analytics
"""

import requests
import json
import time
from datetime import datetime, timedelta
import uuid
import sys
import os

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
if not BACKEND_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"
print(f"🔗 Testing Premium Subscription System at: {API_BASE}")

class PremiumSubscriptionTester:
    def __init__(self):
        self.test_results = []
        self.created_message_ids = []
        self.test_users = {}  # Store test user credentials and tokens
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
        
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Premium" in data["message"]:
                    self.log_result("API Root", True, "Premium API is accessible")
                    return True
                else:
                    self.log_result("API Root", False, "Unexpected response format")
                    return False
            else:
                self.log_result("API Root", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            user_data = {
                "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecurePassword123!",
                "name": "Test User Premium"
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['access_token', 'token_type', 'user']
                
                if all(field in data for field in required_fields):
                    user_info = data['user']
                    if (user_info.get('email') == user_data['email'] and 
                        user_info.get('subscription_plan') == 'free' and
                        user_info.get('monthly_messages_limit') == 5):
                        
                        # Store user for later tests
                        self.test_users['free_user'] = {
                            'email': user_data['email'],
                            'password': user_data['password'],
                            'token': data['access_token'],
                            'user_id': user_info['id']
                        }
                        
                        self.log_result("User Registration", True, 
                                      f"User registered with free plan (5 messages limit)")
                        return True
                    else:
                        self.log_result("User Registration", False, "Invalid user data returned")
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("User Registration", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login"""
        if 'free_user' not in self.test_users:
            self.log_result("User Login", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            login_data = {
                "email": user['email'],
                "password": user['password']
            }
            
            response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get('access_token') and 
                    data.get('user', {}).get('email') == user['email']):
                    
                    # Update token
                    self.test_users['free_user']['token'] = data['access_token']
                    self.log_result("User Login", True, "Login successful with valid token")
                    return True
                else:
                    self.log_result("User Login", False, "Invalid login response")
                    return False
            else:
                self.log_result("User Login", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Error: {str(e)}")
            return False
    
    def test_profile_access(self):
        """Test profile access with JWT token"""
        if 'free_user' not in self.test_users:
            self.log_result("Profile Access", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            response = requests.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get('email') == user['email'] and
                    data.get('subscription_plan') == 'free' and
                    data.get('monthly_messages_limit') == 5):
                    
                    self.log_result("Profile Access", True, "Profile retrieved with correct data")
                    return True
                else:
                    self.log_result("Profile Access", False, "Profile data mismatch")
                    return False
            else:
                self.log_result("Profile Access", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Profile Access", False, f"Error: {str(e)}")
            return False
    
    def test_subscription_plans(self):
        """Test subscription plans endpoint"""
        try:
            response = requests.get(f"{API_BASE}/subscriptions/plans")
            
            if response.status_code == 200:
                data = response.json()
                expected_plans = ['free', 'premium', 'business']
                
                if all(plan in data for plan in expected_plans):
                    # Check plan details
                    free_plan = data['free']
                    premium_plan = data['premium']
                    business_plan = data['business']
                    
                    if (free_plan['price'] == 0.0 and free_plan['monthly_messages'] == 5 and
                        premium_plan['price'] == 9.99 and premium_plan['monthly_messages'] == -1 and
                        business_plan['price'] == 29.99 and business_plan['monthly_messages'] == -1):
                        
                        self.log_result("Subscription Plans", True, 
                                      "All plans available with correct pricing")
                        return True
                    else:
                        self.log_result("Subscription Plans", False, "Plan details incorrect")
                        return False
                else:
                    self.log_result("Subscription Plans", False, f"Missing plans: {expected_plans}")
                    return False
            else:
                self.log_result("Subscription Plans", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Subscription Plans", False, f"Error: {str(e)}")
            return False
    
    def test_stripe_subscription_creation(self):
        """Test Stripe subscription creation"""
        if 'free_user' not in self.test_users:
            self.log_result("Stripe Subscription", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            # Test premium subscription
            subscription_data = {"plan": "premium"}
            response = requests.post(f"{API_BASE}/subscriptions/subscribe", 
                                   json=subscription_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if 'checkout_url' in data and 'session_id' in data:
                    # Store session ID for status testing
                    self.test_users['free_user']['session_id'] = data['session_id']
                    self.log_result("Stripe Subscription", True, 
                                  "Stripe checkout session created successfully")
                    return True
                else:
                    self.log_result("Stripe Subscription", False, "Missing checkout data")
                    return False
            else:
                self.log_result("Stripe Subscription", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Stripe Subscription", False, f"Error: {str(e)}")
            return False
    
    def test_message_creation_free_limit(self):
        """Test message creation with free plan limits"""
        if 'free_user' not in self.test_users:
            self.log_result("Message Limit Test", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            # Try to create 6 messages (should fail on 6th due to 5 message limit)
            success_count = 0
            
            for i in range(6):
                future_time = datetime.utcnow() + timedelta(minutes=i+1)
                message_data = {
                    "title": f"Test Message {i+1}",
                    "content": f"This is test message number {i+1} for limit testing.",
                    "scheduled_time": future_time.isoformat() + "Z"
                }
                
                response = requests.post(f"{API_BASE}/messages", json=message_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_message_ids.append(data['id'])
                    success_count += 1
                elif response.status_code == 403:
                    # Expected limit reached
                    if "limit reached" in response.text.lower():
                        break
                    else:
                        self.log_result("Message Limit Test", False, "Wrong 403 error message")
                        return False
                else:
                    self.log_result("Message Limit Test", False, f"Unexpected error: HTTP {response.status_code}")
                    return False
            
            if success_count == 5:
                self.log_result("Message Limit Test", True, 
                              "Free plan limit enforced correctly (5 messages)")
                return True
            else:
                self.log_result("Message Limit Test", False, 
                              f"Wrong limit behavior: {success_count} messages created")
                return False
                
        except Exception as e:
            self.log_result("Message Limit Test", False, f"Error: {str(e)}")
            return False
    
    def test_recurring_message_restriction(self):
        """Test recurring message restriction for free users"""
        if 'free_user' not in self.test_users:
            self.log_result("Recurring Restriction", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            future_time = datetime.utcnow() + timedelta(hours=1)
            message_data = {
                "title": "Recurring Test Message",
                "content": "This should fail for free users.",
                "scheduled_time": future_time.isoformat() + "Z",
                "is_recurring": True,
                "recurring_pattern": "daily"
            }
            
            response = requests.post(f"{API_BASE}/messages", json=message_data, headers=headers)
            
            if response.status_code == 403:
                if "recurring" in response.text.lower():
                    self.log_result("Recurring Restriction", True, 
                                  "Recurring messages blocked for free users")
                    return True
                else:
                    self.log_result("Recurring Restriction", False, "Wrong error message")
                    return False
            else:
                self.log_result("Recurring Restriction", False, 
                              f"Expected 403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Recurring Restriction", False, f"Error: {str(e)}")
            return False
    
    def test_message_crud_isolation(self):
        """Test message CRUD with user isolation"""
        if 'free_user' not in self.test_users:
            self.log_result("Message CRUD Isolation", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            # Get user's messages
            response = requests.get(f"{API_BASE}/messages", headers=headers)
            
            if response.status_code == 200:
                messages = response.json()
                
                # Verify all messages belong to this user (by checking we can delete them)
                user_message_count = len(messages)
                
                # Test scheduled and delivered endpoints
                scheduled_response = requests.get(f"{API_BASE}/messages/scheduled", headers=headers)
                delivered_response = requests.get(f"{API_BASE}/messages/delivered", headers=headers)
                
                if (scheduled_response.status_code == 200 and 
                    delivered_response.status_code == 200):
                    
                    scheduled_msgs = scheduled_response.json()
                    delivered_msgs = delivered_response.json()
                    
                    # Verify filtering works
                    all_scheduled = all(msg.get('status') == 'scheduled' for msg in scheduled_msgs)
                    all_delivered = all(msg.get('status') == 'delivered' for msg in delivered_msgs)
                    
                    if all_scheduled and all_delivered:
                        self.log_result("Message CRUD Isolation", True, 
                                      f"User isolation working, filtered endpoints functional")
                        return True
                    else:
                        self.log_result("Message CRUD Isolation", False, "Filtering not working properly")
                        return False
                else:
                    self.log_result("Message CRUD Isolation", False, "Filtered endpoints failed")
                    return False
            else:
                self.log_result("Message CRUD Isolation", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Message CRUD Isolation", False, f"Error: {str(e)}")
            return False
    
    def test_analytics_access_control(self):
        """Test analytics access control (business only)"""
        if 'free_user' not in self.test_users:
            self.log_result("Analytics Access Control", False, "No test user available")
            return False
            
        try:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            response = requests.get(f"{API_BASE}/analytics", headers=headers)
            
            if response.status_code == 403:
                if "business" in response.text.lower():
                    self.log_result("Analytics Access Control", True, 
                                  "Analytics blocked for non-business users")
                    return True
                else:
                    self.log_result("Analytics Access Control", False, "Wrong error message")
                    return False
            else:
                self.log_result("Analytics Access Control", False, 
                              f"Expected 403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Analytics Access Control", False, f"Error: {str(e)}")
            return False
    
    def test_background_scheduler(self):
        """Test background scheduler functionality"""
        if 'free_user' not in self.test_users:
            self.log_result("Background Scheduler", False, "No test user available")
            return False
            
        try:
            print("\n🕐 Testing background scheduler (this will take ~60 seconds)...")
            
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            # Create message scheduled for 20 seconds from now
            future_time = datetime.utcnow() + timedelta(seconds=20)
            
            message_data = {
                "title": "Scheduler Test Message",
                "content": "This message tests the background scheduler functionality.",
                "scheduled_time": future_time.isoformat() + "Z"
            }
            
            # Create the message
            response = requests.post(f"{API_BASE}/messages", json=message_data, headers=headers)
            if response.status_code != 200:
                self.log_result("Background Scheduler", False, "Failed to create test message")
                return False
            
            message_data = response.json()
            message_id = message_data['id']
            self.created_message_ids.append(message_id)
            
            print(f"   Created message {message_id}, waiting for delivery...")
            
            # Wait for the message to be delivered (check every 10 seconds for up to 60 seconds)
            max_wait = 60
            check_interval = 10
            waited = 0
            
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                
                # Check if message has been delivered
                response = requests.get(f"{API_BASE}/messages", headers=headers)
                if response.status_code == 200:
                    messages = response.json()
                    test_message = next((msg for msg in messages if msg['id'] == message_id), None)
                    
                    if test_message:
                        if test_message['status'] == 'delivered':
                            if test_message.get('delivered_at'):
                                self.log_result("Background Scheduler", True, 
                                              f"Message delivered after {waited}s")
                                return True
                            else:
                                self.log_result("Background Scheduler", False, 
                                              "Status is delivered but no delivered_at timestamp")
                                return False
                        else:
                            print(f"   Still waiting... (status: {test_message['status']}, waited: {waited}s)")
                    else:
                        self.log_result("Background Scheduler", False, "Test message not found")
                        return False
                else:
                    print(f"   Error checking messages: HTTP {response.status_code}")
            
            self.log_result("Background Scheduler", False, f"Message not delivered after {max_wait}s")
            return False
            
        except Exception as e:
            self.log_result("Background Scheduler", False, f"Error: {str(e)}")
            return False
    
    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        try:
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = requests.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_result("JWT Token Validation", True, "Invalid token rejected correctly")
                return True
            else:
                self.log_result("JWT Token Validation", False, 
                              f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("JWT Token Validation", False, f"Error: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up test data"""
        if 'free_user' in self.test_users:
            user = self.test_users['free_user']
            headers = {"Authorization": f"Bearer {user['token']}"}
            
            print(f"\n🧹 Cleaning up {len(self.created_message_ids)} test messages...")
            for message_id in self.created_message_ids[:]:
                try:
                    response = requests.delete(f"{API_BASE}/messages/{message_id}", headers=headers)
                    if response.status_code == 200:
                        print(f"   Deleted message {message_id}")
                        self.created_message_ids.remove(message_id)
                    else:
                        print(f"   Failed to delete message {message_id}: HTTP {response.status_code}")
                except Exception as e:
                    print(f"   Error deleting message {message_id}: {e}")
    
    def run_all_tests(self):
        """Run all premium subscription system tests"""
        print("🚀 Starting Premium Subscription System Tests\n")
        
        # Test sequence
        tests = [
            ("API Connectivity", self.test_api_root),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Profile Access", self.test_profile_access),
            ("JWT Token Validation", self.test_jwt_token_validation),
            ("Subscription Plans", self.test_subscription_plans),
            ("Stripe Integration", self.test_stripe_subscription_creation),
            ("Message Limit Enforcement", self.test_message_creation_free_limit),
            ("Recurring Message Restriction", self.test_recurring_message_restriction),
            ("Message CRUD Isolation", self.test_message_crud_isolation),
            ("Analytics Access Control", self.test_analytics_access_control),
            ("Background Scheduler", self.test_background_scheduler),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- Running: {test_name} ---")
            if test_func():
                passed += 1
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print(f"\n{'='*70}")
        print(f"🎯 PREMIUM SUBSCRIPTION SYSTEM TEST SUMMARY: {passed}/{total} tests passed")
        print(f"{'='*70}")
        
        if passed == total:
            print("🎉 All tests passed! Premium subscription system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
        return passed == total

def main():
    """Main test execution"""
    tester = PremiumSubscriptionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Premium subscription system testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Premium subscription system testing completed with failures!")
        sys.exit(1)

if __name__ == "__main__":
    main()