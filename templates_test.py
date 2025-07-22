#!/usr/bin/env python3
"""
TEMPLATES ENDPOINT MONGODB SERIALIZATION FIX TEST
Focus on testing the critical MongoDB ObjectId serialization issue for templates endpoint.
"""

import requests
import json
import uuid
import sys

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
print(f"🔗 Testing Templates MongoDB Serialization Fix at: {API_BASE}")

class TemplatesSerializationTester:
    def __init__(self):
        self.test_results = []
        self.admin_token = None
        self.created_template_ids = []
        
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
    
    def setup_admin_user(self):
        """Setup admin user for testing"""
        try:
            # Login with admin user
            admin_data = {
                "email": "admin@zeitgesteuerte.de",
                "password": "admin123"
            }
            
            response = requests.post(f"{API_BASE}/auth/login", json=admin_data)
            if response.status_code == 200:
                self.admin_token = response.json()['access_token']
                self.log_result("Admin Login", True, "Admin user authenticated successfully")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Error: {str(e)}")
            return False
    
    def test_template_creation(self):
        """Test template creation via POST /api/templates"""
        if not self.admin_token:
            self.log_result("Template Creation", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test template data from the review request
            template_data = {
                "name": "Quick Test Template",
                "title": "Test Message Title", 
                "content": "This is a test template message.",
                "category": "general",
                "is_public": False
            }
            
            response = requests.post(f"{API_BASE}/templates", json=template_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data.get('name') == template_data['name']:
                    self.created_template_ids.append(data['id'])
                    self.log_result("Template Creation", True, 
                                  f"Template created successfully with ID: {data['id']}")
                    return True
                else:
                    self.log_result("Template Creation", False, 
                                  f"Invalid response format: {data}")
                    return False
            else:
                self.log_result("Template Creation", False, 
                              f"HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Template Creation", False, f"Error: {str(e)}")
            return False
    
    def test_templates_retrieval(self):
        """Test GET /api/templates - The critical endpoint that was failing with 500 error"""
        if not self.admin_token:
            self.log_result("Templates Retrieval", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{API_BASE}/templates", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if isinstance(data, dict) and 'user_templates' in data and 'public_templates' in data:
                    user_templates = data['user_templates']
                    public_templates = data['public_templates']
                    
                    # Verify templates are properly serialized (no MongoDB ObjectId issues)
                    if isinstance(user_templates, list) and isinstance(public_templates, list):
                        # Check if our created template is in the response
                        template_found = False
                        if self.created_template_ids:
                            for template in user_templates:
                                if template.get('id') in self.created_template_ids:
                                    template_found = True
                                    # Verify no _id field (MongoDB ObjectId) is present
                                    if '_id' in template:
                                        self.log_result("Templates Retrieval", False, 
                                                      "MongoDB _id field found in response - serialization issue not fixed")
                                        return False
                                    break
                        
                        self.log_result("Templates Retrieval", True, 
                                      f"Templates retrieved successfully. User templates: {len(user_templates)}, Public templates: {len(public_templates)}")
                        return True
                    else:
                        self.log_result("Templates Retrieval", False, 
                                      "Invalid template arrays in response")
                        return False
                else:
                    self.log_result("Templates Retrieval", False, 
                                  f"Invalid response structure: {data}")
                    return False
            else:
                self.log_result("Templates Retrieval", False, 
                              f"HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Templates Retrieval", False, f"Error: {str(e)}")
            return False
    
    def test_template_creation_and_retrieval_flow(self):
        """Test complete template creation and retrieval flow"""
        if not self.admin_token:
            self.log_result("Template Flow", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Create multiple templates to test serialization with multiple records
            test_templates = [
                {
                    "name": "Meeting Reminder Template",
                    "title": "Meeting Tomorrow",
                    "content": "Don't forget about our meeting tomorrow at 2 PM.",
                    "category": "business",
                    "is_public": True
                },
                {
                    "name": "Birthday Greeting",
                    "title": "Happy Birthday!",
                    "content": "Wishing you a wonderful birthday filled with joy!",
                    "category": "personal",
                    "is_public": False
                }
            ]
            
            created_ids = []
            
            # Create templates
            for i, template_data in enumerate(test_templates):
                response = requests.post(f"{API_BASE}/templates", json=template_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data:
                        created_ids.append(data['id'])
                        print(f"   Created template {i+1}: {data['id']}")
                    else:
                        self.log_result("Template Flow", False, 
                                      f"Template {i+1} creation failed - no ID returned")
                        return False
                else:
                    self.log_result("Template Flow", False, 
                                  f"Template {i+1} creation failed: HTTP {response.status_code}")
                    return False
            
            # Retrieve templates and verify they're all there
            response = requests.get(f"{API_BASE}/templates", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                user_templates = data.get('user_templates', [])
                
                # Check if all created templates are present
                found_count = 0
                for template_id in created_ids:
                    for template in user_templates:
                        if template.get('id') == template_id:
                            found_count += 1
                            # Verify no MongoDB serialization issues
                            if '_id' in template:
                                self.log_result("Template Flow", False, 
                                              "MongoDB _id field found - serialization issue")
                                return False
                            break
                
                if found_count == len(created_ids):
                    self.log_result("Template Flow", True, 
                                  f"Complete flow working: {len(created_ids)} templates created and retrieved successfully")
                    
                    # Store IDs for cleanup
                    self.created_template_ids.extend(created_ids)
                    return True
                else:
                    self.log_result("Template Flow", False, 
                                  f"Only {found_count}/{len(created_ids)} templates found in retrieval")
                    return False
            else:
                self.log_result("Template Flow", False, 
                              f"Template retrieval failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Template Flow", False, f"Error: {str(e)}")
            return False
    
    def test_template_data_integrity(self):
        """Test that template data is returned correctly without corruption"""
        if not self.admin_token or not self.created_template_ids:
            self.log_result("Template Data Integrity", False, "No templates available for testing")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = requests.get(f"{API_BASE}/templates", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                user_templates = data.get('user_templates', [])
                
                # Find our test template
                test_template = None
                for template in user_templates:
                    if template.get('name') == "Quick Test Template":
                        test_template = template
                        break
                
                if test_template:
                    # Verify all expected fields are present and correct
                    expected_fields = ['id', 'name', 'title', 'content', 'category', 'is_public', 'usage_count', 'created_at']
                    missing_fields = [field for field in expected_fields if field not in test_template]
                    
                    if not missing_fields:
                        # Verify data integrity
                        if (test_template['name'] == "Quick Test Template" and
                            test_template['title'] == "Test Message Title" and
                            test_template['content'] == "This is a test template message." and
                            test_template['category'] == "general" and
                            test_template['is_public'] == False):
                            
                            self.log_result("Template Data Integrity", True, 
                                          "Template data returned correctly with all fields intact")
                            return True
                        else:
                            self.log_result("Template Data Integrity", False, 
                                          "Template data corrupted or incorrect")
                            return False
                    else:
                        self.log_result("Template Data Integrity", False, 
                                      f"Missing fields: {missing_fields}")
                        return False
                else:
                    self.log_result("Template Data Integrity", False, 
                                  "Test template not found in response")
                    return False
            else:
                self.log_result("Template Data Integrity", False, 
                              f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Template Data Integrity", False, f"Error: {str(e)}")
            return False
    
    def cleanup_test_templates(self):
        """Clean up created test templates"""
        if not self.admin_token or not self.created_template_ids:
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            for template_id in self.created_template_ids:
                response = requests.delete(f"{API_BASE}/templates/{template_id}", headers=headers)
                if response.status_code == 200:
                    print(f"   Cleaned up template: {template_id}")
                else:
                    print(f"   Failed to clean up template {template_id}: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"   Cleanup error: {str(e)}")
    
    def run_all_tests(self):
        """Run all template serialization tests"""
        print("\n🧪 TEMPLATES MONGODB SERIALIZATION FIX VERIFICATION")
        print("=" * 60)
        
        tests = [
            self.setup_admin_user,
            self.test_template_creation,
            self.test_templates_retrieval,
            self.test_template_creation_and_retrieval_flow,
            self.test_template_data_integrity
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()  # Add spacing between tests
        
        # Cleanup
        self.cleanup_test_templates()
        
        print("\n📊 TEMPLATES SERIALIZATION TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n✅ ALL TESTS PASSED - MongoDB serialization issue appears to be FIXED!")
            print("✅ GET /api/templates endpoint working without 500 errors")
            print("✅ Template creation and retrieval flow working correctly")
            print("✅ No MongoDB ObjectId serialization issues detected")
        else:
            print(f"\n❌ {total-passed} TESTS FAILED - MongoDB serialization issue may still exist")
            print("❌ GET /api/templates endpoint may still have issues")
        
        return passed == total

if __name__ == "__main__":
    tester = TemplatesSerializationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)