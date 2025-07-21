#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Scheduled Messages System
Tests all API endpoints and background scheduler functionality
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
print(f"🔗 Testing backend at: {API_BASE}")

class BackendTester:
    def __init__(self):
        self.test_results = []
        self.created_message_ids = []
        
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
                if "message" in data:
                    self.log_result("API Root", True, "API is accessible")
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
    
    def test_create_message_valid(self):
        """Test creating a valid scheduled message"""
        try:
            # Create message scheduled for 2 minutes in the future
            future_time = datetime.utcnow() + timedelta(minutes=2)
            
            message_data = {
                "title": "Test Meeting Reminder",
                "content": "Don't forget about the team meeting at 3 PM today. Please bring your project updates and be prepared to discuss the quarterly goals.",
                "scheduled_time": future_time.isoformat() + "Z"
            }
            
            response = requests.post(f"{API_BASE}/messages", json=message_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'title', 'content', 'scheduled_time', 'created_at', 'status']
                
                if all(field in data for field in required_fields):
                    if data['status'] == 'scheduled':
                        self.created_message_ids.append(data['id'])
                        self.log_result("Create Valid Message", True, f"Message created with ID: {data['id']}")
                        return True
                    else:
                        self.log_result("Create Valid Message", False, f"Wrong status: {data['status']}")
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Create Valid Message", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_result("Create Valid Message", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Valid Message", False, f"Error: {str(e)}")
            return False
    
    def test_create_message_past_date(self):
        """Test creating message with past date (should work but note behavior)"""
        try:
            # Create message scheduled for past time
            past_time = datetime.utcnow() - timedelta(minutes=30)
            
            message_data = {
                "title": "Past Message Test",
                "content": "This message was scheduled for the past to test backend behavior.",
                "scheduled_time": past_time.isoformat() + "Z"
            }
            
            response = requests.post(f"{API_BASE}/messages", json=message_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_message_ids.append(data['id'])
                self.log_result("Create Past Date Message", True, "Backend accepts past dates", 
                              f"Status: {data['status']}")
                return True
            else:
                self.log_result("Create Past Date Message", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Create Past Date Message", False, f"Error: {str(e)}")
            return False
    
    def test_create_message_invalid(self):
        """Test creating message with missing required fields"""
        try:
            # Missing title
            message_data = {
                "content": "Missing title test",
                "scheduled_time": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
            }
            
            response = requests.post(f"{API_BASE}/messages", json=message_data)
            
            if response.status_code == 422:  # Validation error expected
                self.log_result("Create Invalid Message", True, "Validation error returned as expected")
                return True
            else:
                self.log_result("Create Invalid Message", False, f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Create Invalid Message", False, f"Error: {str(e)}")
            return False
    
    def test_get_all_messages(self):
        """Test getting all messages"""
        try:
            response = requests.get(f"{API_BASE}/messages")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get All Messages", True, f"Retrieved {len(data)} messages")
                    return True
                else:
                    self.log_result("Get All Messages", False, "Response is not a list")
                    return False
            else:
                self.log_result("Get All Messages", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get All Messages", False, f"Error: {str(e)}")
            return False
    
    def test_get_scheduled_messages(self):
        """Test getting only scheduled messages"""
        try:
            response = requests.get(f"{API_BASE}/messages/scheduled")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check that all returned messages have status 'scheduled'
                    all_scheduled = all(msg.get('status') == 'scheduled' for msg in data)
                    if all_scheduled:
                        self.log_result("Get Scheduled Messages", True, f"Retrieved {len(data)} scheduled messages")
                        return True
                    else:
                        self.log_result("Get Scheduled Messages", False, "Some messages are not scheduled")
                        return False
                else:
                    self.log_result("Get Scheduled Messages", False, "Response is not a list")
                    return False
            else:
                self.log_result("Get Scheduled Messages", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Scheduled Messages", False, f"Error: {str(e)}")
            return False
    
    def test_get_delivered_messages(self):
        """Test getting only delivered messages"""
        try:
            response = requests.get(f"{API_BASE}/messages/delivered")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check that all returned messages have status 'delivered'
                    all_delivered = all(msg.get('status') == 'delivered' for msg in data)
                    if all_delivered:
                        self.log_result("Get Delivered Messages", True, f"Retrieved {len(data)} delivered messages")
                        return True
                    else:
                        self.log_result("Get Delivered Messages", False, "Some messages are not delivered")
                        return False
                else:
                    self.log_result("Get Delivered Messages", False, "Response is not a list")
                    return False
            else:
                self.log_result("Get Delivered Messages", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Delivered Messages", False, f"Error: {str(e)}")
            return False
    
    def test_delete_message_valid(self):
        """Test deleting a valid message"""
        if not self.created_message_ids:
            self.log_result("Delete Valid Message", False, "No messages to delete")
            return False
            
        try:
            message_id = self.created_message_ids[0]
            response = requests.delete(f"{API_BASE}/messages/{message_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    # Remove from our tracking list
                    self.created_message_ids.remove(message_id)
                    self.log_result("Delete Valid Message", True, f"Message {message_id} deleted")
                    return True
                else:
                    self.log_result("Delete Valid Message", False, "Unexpected response format")
                    return False
            else:
                self.log_result("Delete Valid Message", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Delete Valid Message", False, f"Error: {str(e)}")
            return False
    
    def test_delete_message_invalid(self):
        """Test deleting a non-existent message"""
        try:
            fake_id = str(uuid.uuid4())
            response = requests.delete(f"{API_BASE}/messages/{fake_id}")
            
            if response.status_code == 404:
                self.log_result("Delete Invalid Message", True, "404 returned for non-existent message")
                return True
            else:
                self.log_result("Delete Invalid Message", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Delete Invalid Message", False, f"Error: {str(e)}")
            return False
    
    def test_scheduler_functionality(self):
        """Test background scheduler by creating a message due soon"""
        try:
            print("\n🕐 Testing background scheduler (this will take ~90 seconds)...")
            
            # Create message scheduled for 30 seconds from now
            future_time = datetime.utcnow() + timedelta(seconds=30)
            
            message_data = {
                "title": "Scheduler Test Message",
                "content": "This message tests the background scheduler functionality. It should be automatically delivered.",
                "scheduled_time": future_time.isoformat() + "Z"
            }
            
            # Create the message
            response = requests.post(f"{API_BASE}/messages", json=message_data)
            if response.status_code != 200:
                self.log_result("Scheduler Test", False, "Failed to create test message")
                return False
            
            message_data = response.json()
            message_id = message_data['id']
            self.created_message_ids.append(message_id)
            
            print(f"   Created message {message_id}, waiting for delivery...")
            
            # Wait for the message to be delivered (check every 15 seconds for up to 90 seconds)
            max_wait = 90
            check_interval = 15
            waited = 0
            
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                
                # Check if message has been delivered
                response = requests.get(f"{API_BASE}/messages")
                if response.status_code == 200:
                    messages = response.json()
                    test_message = next((msg for msg in messages if msg['id'] == message_id), None)
                    
                    if test_message:
                        if test_message['status'] == 'delivered':
                            if test_message.get('delivered_at'):
                                self.log_result("Scheduler Test", True, 
                                              f"Message delivered after {waited}s", 
                                              f"Delivered at: {test_message['delivered_at']}")
                                return True
                            else:
                                self.log_result("Scheduler Test", False, 
                                              "Status is delivered but no delivered_at timestamp")
                                return False
                        else:
                            print(f"   Still waiting... (status: {test_message['status']}, waited: {waited}s)")
                    else:
                        self.log_result("Scheduler Test", False, "Test message not found")
                        return False
                else:
                    print(f"   Error checking messages: HTTP {response.status_code}")
            
            self.log_result("Scheduler Test", False, f"Message not delivered after {max_wait}s")
            return False
            
        except Exception as e:
            self.log_result("Scheduler Test", False, f"Error: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up any remaining test messages"""
        print(f"\n🧹 Cleaning up {len(self.created_message_ids)} test messages...")
        for message_id in self.created_message_ids[:]:
            try:
                response = requests.delete(f"{API_BASE}/messages/{message_id}")
                if response.status_code == 200:
                    print(f"   Deleted message {message_id}")
                    self.created_message_ids.remove(message_id)
                else:
                    print(f"   Failed to delete message {message_id}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   Error deleting message {message_id}: {e}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Scheduled Messages Backend Tests\n")
        
        # Test sequence
        tests = [
            ("API Connectivity", self.test_api_root),
            ("Create Valid Message", self.test_create_message_valid),
            ("Create Past Date Message", self.test_create_message_past_date),
            ("Create Invalid Message", self.test_create_message_invalid),
            ("Get All Messages", self.test_get_all_messages),
            ("Get Scheduled Messages", self.test_get_scheduled_messages),
            ("Get Delivered Messages", self.test_get_delivered_messages),
            ("Delete Valid Message", self.test_delete_message_valid),
            ("Delete Invalid Message", self.test_delete_message_invalid),
            ("Background Scheduler", self.test_scheduler_functionality),
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
        print(f"\n{'='*60}")
        print(f"🎯 TEST SUMMARY: {passed}/{total} tests passed")
        print(f"{'='*60}")
        
        if passed == total:
            print("🎉 All tests passed! Backend is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
        return passed == total

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Backend testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Backend testing completed with failures!")
        sys.exit(1)

if __name__ == "__main__":
    main()