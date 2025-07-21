#!/usr/bin/env python3
"""
ADVANCED ANALYTICS DASHBOARD BACKEND TESTING
Tests the new Advanced Analytics Dashboard backend implementation including:
- User Analytics (registration trends, conversion rate, retention, referrers, activity heatmap)
- Message Analytics (creation patterns, delivery success rate, popular times, type distribution)
- Revenue Analytics (MRR trend, ARPU, churn rate, growth rate, revenue by plan)
- AI Usage Analytics (feature usage, success rate, popular prompts, enhancement types, adoption rate)
- Complete Analytics (all analytics combined)
- Export Analytics (CSV/JSON format export)
- Authentication & Authorization (admin only access)
- Error Handling & Performance
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
print(f"🔗 Testing Advanced Analytics Dashboard at: {API_BASE}")

class AdvancedAnalyticsTester:
    def __init__(self):
        self.test_results = []
        self.admin_token = None
        self.regular_user_token = None
        
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
            admin_data = {
                "email": "admin@zeitgesteuerte.de",
                "password": "admin123",
                "name": "Admin User"
            }
            
            # Try to register admin (might already exist)
            response = requests.post(f"{API_BASE}/auth/register", json=admin_data)
            if response.status_code == 200:
                self.admin_token = response.json()['access_token']
                print("✅ Admin user registered successfully")
                return True
            else:
                # Try login if already exists
                login_response = requests.post(f"{API_BASE}/auth/login", json={
                    "email": admin_data['email'],
                    "password": admin_data['password']
                })
                if login_response.status_code == 200:
                    self.admin_token = login_response.json()['access_token']
                    print("✅ Admin user login successful")
                    return True
                else:
                    print(f"❌ Cannot access admin user: {login_response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error setting up admin user: {str(e)}")
            return False
    
    def setup_regular_user(self):
        """Setup regular user for authorization testing"""
        try:
            user_data = {
                "email": f"regular_{uuid.uuid4().hex[:8]}@example.com",
                "password": "RegularPassword123!",
                "name": "Regular User"
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            if response.status_code == 200:
                self.regular_user_token = response.json()['access_token']
                print("✅ Regular user created successfully")
                return True
            else:
                print(f"❌ Cannot create regular user: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up regular user: {str(e)}")
            return False
    
    def test_admin_authentication(self):
        """Test admin authentication and authorization"""
        if not self.admin_token:
            self.log_result("Admin Authentication", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test admin profile access
            response = requests.get(f"{API_BASE}/auth/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('role') == 'admin':
                    self.log_result("Admin Authentication", True, 
                                  f"Admin user authenticated with role: {user_data.get('role')}")
                    return True
                else:
                    self.log_result("Admin Authentication", False, 
                                  f"User role is not admin: {user_data.get('role')}")
                    return False
            else:
                self.log_result("Admin Authentication", False, 
                              f"Admin profile access failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_regular_user_authorization(self):
        """Test that regular users cannot access admin analytics"""
        if not self.regular_user_token:
            self.log_result("Regular User Authorization", False, "No regular user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.regular_user_token}"}
            
            # Test all admin analytics endpoints
            admin_endpoints = [
                "/admin/analytics/users",
                "/admin/analytics/messages", 
                "/admin/analytics/revenue",
                "/admin/analytics/ai",
                "/admin/analytics/complete",
                "/admin/analytics/export"
            ]
            
            forbidden_count = 0
            for endpoint in admin_endpoints:
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
                if response.status_code == 403:
                    forbidden_count += 1
                else:
                    print(f"   Endpoint {endpoint}: Expected 403, got {response.status_code}")
            
            if forbidden_count == len(admin_endpoints):
                self.log_result("Regular User Authorization", True, 
                              f"All {len(admin_endpoints)} admin endpoints properly protected")
                return True
            else:
                self.log_result("Regular User Authorization", False, 
                              f"Only {forbidden_count}/{len(admin_endpoints)} endpoints protected")
                return False
                
        except Exception as e:
            self.log_result("Regular User Authorization", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_token_rejection(self):
        """Test that invalid JWT tokens are rejected"""
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            
            # Test all admin analytics endpoints with invalid token
            admin_endpoints = [
                "/admin/analytics/users",
                "/admin/analytics/messages", 
                "/admin/analytics/revenue",
                "/admin/analytics/ai",
                "/admin/analytics/complete",
                "/admin/analytics/export"
            ]
            
            rejected_count = 0
            for endpoint in admin_endpoints:
                response = requests.get(f"{API_BASE}{endpoint}", headers=invalid_headers)
                if response.status_code == 401:
                    rejected_count += 1
                else:
                    print(f"   Endpoint {endpoint}: Expected 401, got {response.status_code}")
            
            if rejected_count == len(admin_endpoints):
                self.log_result("Invalid Token Rejection", True, 
                              f"All {len(admin_endpoints)} endpoints reject invalid tokens")
                return True
            else:
                self.log_result("Invalid Token Rejection", False, 
                              f"Only {rejected_count}/{len(admin_endpoints)} endpoints reject invalid tokens")
                return False
                
        except Exception as e:
            self.log_result("Invalid Token Rejection", False, f"Error: {str(e)}")
            return False
    
    def test_user_analytics_endpoint(self):
        """Test GET /api/admin/analytics/users endpoint"""
        if not self.admin_token:
            self.log_result("User Analytics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            start_time = time.time()
            
            response = requests.get(f"{API_BASE}/admin/analytics/users", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = [
                    'registration_trends', 'subscription_conversion_rate', 
                    'user_retention_rate', 'top_referrers', 'user_activity_heatmap'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result("User Analytics Endpoint", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types and ranges
                conversion_rate = data.get('subscription_conversion_rate', -1)
                retention_rate = data.get('user_retention_rate', -1)
                
                if not (0 <= conversion_rate <= 100):
                    self.log_result("User Analytics Endpoint", False, 
                                  f"Invalid conversion rate: {conversion_rate}")
                    return False
                
                if not (0 <= retention_rate <= 100):
                    self.log_result("User Analytics Endpoint", False, 
                                  f"Invalid retention rate: {retention_rate}")
                    return False
                
                # Verify arrays are present
                if not isinstance(data.get('registration_trends'), list):
                    self.log_result("User Analytics Endpoint", False, 
                                  "registration_trends is not a list")
                    return False
                
                if not isinstance(data.get('top_referrers'), list):
                    self.log_result("User Analytics Endpoint", False, 
                                  "top_referrers is not a list")
                    return False
                
                if not isinstance(data.get('user_activity_heatmap'), list):
                    self.log_result("User Analytics Endpoint", False, 
                                  "user_activity_heatmap is not a list")
                    return False
                
                # Check performance
                if response_time > 5.0:
                    self.log_result("User Analytics Endpoint", False, 
                                  f"Response too slow: {response_time:.2f}s")
                    return False
                
                self.log_result("User Analytics Endpoint", True, 
                              f"Valid response in {response_time:.2f}s, conversion: {conversion_rate}%, retention: {retention_rate}%")
                return True
            else:
                self.log_result("User Analytics Endpoint", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_message_analytics_endpoint(self):
        """Test GET /api/admin/analytics/messages endpoint"""
        if not self.admin_token:
            self.log_result("Message Analytics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            start_time = time.time()
            
            response = requests.get(f"{API_BASE}/admin/analytics/messages", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = [
                    'creation_patterns', 'delivery_success_rate', 
                    'popular_times', 'message_type_distribution', 'recurring_vs_oneshot'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result("Message Analytics Endpoint", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types and ranges
                success_rate = data.get('delivery_success_rate', -1)
                
                if not (0 <= success_rate <= 100):
                    self.log_result("Message Analytics Endpoint", False, 
                                  f"Invalid success rate: {success_rate}")
                    return False
                
                # Verify arrays are present
                if not isinstance(data.get('creation_patterns'), list):
                    self.log_result("Message Analytics Endpoint", False, 
                                  "creation_patterns is not a list")
                    return False
                
                if not isinstance(data.get('popular_times'), list):
                    self.log_result("Message Analytics Endpoint", False, 
                                  "popular_times is not a list")
                    return False
                
                if not isinstance(data.get('message_type_distribution'), list):
                    self.log_result("Message Analytics Endpoint", False, 
                                  "message_type_distribution is not a list")
                    return False
                
                # Verify recurring_vs_oneshot structure
                recurring_data = data.get('recurring_vs_oneshot', {})
                if not isinstance(recurring_data, dict):
                    self.log_result("Message Analytics Endpoint", False, 
                                  "recurring_vs_oneshot is not a dict")
                    return False
                
                # Check performance
                if response_time > 5.0:
                    self.log_result("Message Analytics Endpoint", False, 
                                  f"Response too slow: {response_time:.2f}s")
                    return False
                
                self.log_result("Message Analytics Endpoint", True, 
                              f"Valid response in {response_time:.2f}s, success rate: {success_rate}%")
                return True
            else:
                self.log_result("Message Analytics Endpoint", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Message Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_revenue_analytics_endpoint(self):
        """Test GET /api/admin/analytics/revenue endpoint"""
        if not self.admin_token:
            self.log_result("Revenue Analytics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            start_time = time.time()
            
            response = requests.get(f"{API_BASE}/admin/analytics/revenue", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = [
                    'mrr_trend', 'arpu', 'churn_rate', 
                    'subscription_growth_rate', 'revenue_by_plan'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types and ranges
                arpu = data.get('arpu', -1)
                churn_rate = data.get('churn_rate', -1)
                growth_rate = data.get('subscription_growth_rate', -1000)
                
                if arpu < 0:
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  f"Invalid ARPU: {arpu}")
                    return False
                
                if not (0 <= churn_rate <= 100):
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  f"Invalid churn rate: {churn_rate}")
                    return False
                
                # Growth rate can be negative, but should be reasonable
                if not (-100 <= growth_rate <= 1000):
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  f"Unreasonable growth rate: {growth_rate}")
                    return False
                
                # Verify arrays are present
                if not isinstance(data.get('mrr_trend'), list):
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  "mrr_trend is not a list")
                    return False
                
                if not isinstance(data.get('revenue_by_plan'), list):
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  "revenue_by_plan is not a list")
                    return False
                
                # Check performance
                if response_time > 5.0:
                    self.log_result("Revenue Analytics Endpoint", False, 
                                  f"Response too slow: {response_time:.2f}s")
                    return False
                
                self.log_result("Revenue Analytics Endpoint", True, 
                              f"Valid response in {response_time:.2f}s, ARPU: €{arpu:.2f}, churn: {churn_rate}%")
                return True
            else:
                self.log_result("Revenue Analytics Endpoint", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Revenue Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_ai_analytics_endpoint(self):
        """Test GET /api/admin/analytics/ai endpoint"""
        if not self.admin_token:
            self.log_result("AI Analytics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            start_time = time.time()
            
            response = requests.get(f"{API_BASE}/admin/analytics/ai", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = [
                    'feature_usage', 'generation_success_rate', 
                    'popular_prompts', 'enhancement_types', 'ai_adoption_rate'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result("AI Analytics Endpoint", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types and ranges
                success_rate = data.get('generation_success_rate', -1)
                adoption_rate = data.get('ai_adoption_rate', -1)
                
                if not (0 <= success_rate <= 100):
                    self.log_result("AI Analytics Endpoint", False, 
                                  f"Invalid success rate: {success_rate}")
                    return False
                
                if not (0 <= adoption_rate <= 100):
                    self.log_result("AI Analytics Endpoint", False, 
                                  f"Invalid adoption rate: {adoption_rate}")
                    return False
                
                # Verify arrays are present
                if not isinstance(data.get('feature_usage'), list):
                    self.log_result("AI Analytics Endpoint", False, 
                                  "feature_usage is not a list")
                    return False
                
                if not isinstance(data.get('popular_prompts'), list):
                    self.log_result("AI Analytics Endpoint", False, 
                                  "popular_prompts is not a list")
                    return False
                
                if not isinstance(data.get('enhancement_types'), list):
                    self.log_result("AI Analytics Endpoint", False, 
                                  "enhancement_types is not a list")
                    return False
                
                # Check performance
                if response_time > 5.0:
                    self.log_result("AI Analytics Endpoint", False, 
                                  f"Response too slow: {response_time:.2f}s")
                    return False
                
                self.log_result("AI Analytics Endpoint", True, 
                              f"Valid response in {response_time:.2f}s, success: {success_rate}%, adoption: {adoption_rate}%")
                return True
            else:
                self.log_result("AI Analytics Endpoint", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("AI Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_complete_analytics_endpoint(self):
        """Test GET /api/admin/analytics/complete endpoint"""
        if not self.admin_token:
            self.log_result("Complete Analytics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            start_time = time.time()
            
            response = requests.get(f"{API_BASE}/admin/analytics/complete", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure - should contain all four analytics objects
                required_fields = [
                    'user_analytics', 'message_analytics', 
                    'revenue_analytics', 'ai_analytics', 'generated_at'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result("Complete Analytics Endpoint", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify each analytics section has its required fields
                user_analytics = data.get('user_analytics', {})
                if not all(field in user_analytics for field in ['registration_trends', 'subscription_conversion_rate']):
                    self.log_result("Complete Analytics Endpoint", False, 
                                  "user_analytics missing required fields")
                    return False
                
                message_analytics = data.get('message_analytics', {})
                if not all(field in message_analytics for field in ['creation_patterns', 'delivery_success_rate']):
                    self.log_result("Complete Analytics Endpoint", False, 
                                  "message_analytics missing required fields")
                    return False
                
                revenue_analytics = data.get('revenue_analytics', {})
                if not all(field in revenue_analytics for field in ['mrr_trend', 'arpu']):
                    self.log_result("Complete Analytics Endpoint", False, 
                                  "revenue_analytics missing required fields")
                    return False
                
                ai_analytics = data.get('ai_analytics', {})
                if not all(field in ai_analytics for field in ['feature_usage', 'generation_success_rate']):
                    self.log_result("Complete Analytics Endpoint", False, 
                                  "ai_analytics missing required fields")
                    return False
                
                # Verify generated_at timestamp
                generated_at = data.get('generated_at')
                if not generated_at:
                    self.log_result("Complete Analytics Endpoint", False, 
                                  "Missing generated_at timestamp")
                    return False
                
                # Check performance
                if response_time > 5.0:
                    self.log_result("Complete Analytics Endpoint", False, 
                                  f"Response too slow: {response_time:.2f}s")
                    return False
                
                self.log_result("Complete Analytics Endpoint", True, 
                              f"Complete analytics response in {response_time:.2f}s with all sections")
                return True
            else:
                self.log_result("Complete Analytics Endpoint", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Complete Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_export_analytics_endpoint(self):
        """Test GET /api/admin/analytics/export endpoint"""
        if not self.admin_token:
            self.log_result("Export Analytics Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test JSON export
            start_time = time.time()
            response = requests.get(f"{API_BASE}/admin/analytics/export?format=json", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('format') != 'json':
                    self.log_result("Export Analytics (JSON)", False, 
                                  f"Wrong format returned: {data.get('format')}")
                    return False
                
                if 'data' not in data or 'exported_at' not in data:
                    self.log_result("Export Analytics (JSON)", False, 
                                  "Missing data or exported_at fields")
                    return False
                
                # Verify the data contains analytics
                export_data = data.get('data', {})
                if not all(field in export_data for field in ['user_analytics', 'message_analytics']):
                    self.log_result("Export Analytics (JSON)", False, 
                                  "Export data missing analytics sections")
                    return False
                
                print(f"   JSON export successful in {response_time:.2f}s")
            else:
                self.log_result("Export Analytics (JSON)", False, 
                              f"JSON export failed: HTTP {response.status_code}")
                return False
            
            # Test CSV export
            start_time = time.time()
            response = requests.get(f"{API_BASE}/admin/analytics/export?format=csv", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('format') != 'csv':
                    self.log_result("Export Analytics (CSV)", False, 
                                  f"Wrong format returned: {data.get('format')}")
                    return False
                
                if 'download_url' not in data or 'message' not in data:
                    self.log_result("Export Analytics (CSV)", False, 
                                  "Missing download_url or message fields")
                    return False
                
                print(f"   CSV export successful in {response_time:.2f}s")
            else:
                self.log_result("Export Analytics (CSV)", False, 
                              f"CSV export failed: HTTP {response.status_code}")
                return False
            
            # Test invalid format
            response = requests.get(f"{API_BASE}/admin/analytics/export?format=invalid", headers=headers)
            if response.status_code != 400:
                self.log_result("Export Analytics (Invalid Format)", False, 
                              f"Invalid format not rejected: HTTP {response.status_code}")
                return False
            
            self.log_result("Export Analytics Endpoint", True, 
                          "JSON, CSV, and invalid format handling all working")
            return True
                
        except Exception as e:
            self.log_result("Export Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_data_quality_validation(self):
        """Test data quality and calculations"""
        if not self.admin_token:
            self.log_result("Data Quality Validation", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get complete analytics for validation
            response = requests.get(f"{API_BASE}/admin/analytics/complete", headers=headers)
            if response.status_code != 200:
                self.log_result("Data Quality Validation", False, 
                              f"Cannot get analytics data: HTTP {response.status_code}")
                return False
            
            data = response.json()
            issues = []
            
            # Validate user analytics
            user_analytics = data.get('user_analytics', {})
            conversion_rate = user_analytics.get('subscription_conversion_rate', -1)
            retention_rate = user_analytics.get('user_retention_rate', -1)
            
            if not (0 <= conversion_rate <= 100):
                issues.append(f"Invalid conversion rate: {conversion_rate}")
            
            if not (0 <= retention_rate <= 100):
                issues.append(f"Invalid retention rate: {retention_rate}")
            
            # Validate message analytics
            message_analytics = data.get('message_analytics', {})
            success_rate = message_analytics.get('delivery_success_rate', -1)
            
            if not (0 <= success_rate <= 100):
                issues.append(f"Invalid delivery success rate: {success_rate}")
            
            # Validate revenue analytics
            revenue_analytics = data.get('revenue_analytics', {})
            arpu = revenue_analytics.get('arpu', -1)
            churn_rate = revenue_analytics.get('churn_rate', -1)
            
            if arpu < 0:
                issues.append(f"Invalid ARPU: {arpu}")
            
            if not (0 <= churn_rate <= 100):
                issues.append(f"Invalid churn rate: {churn_rate}")
            
            # Validate AI analytics
            ai_analytics = data.get('ai_analytics', {})
            ai_success_rate = ai_analytics.get('generation_success_rate', -1)
            adoption_rate = ai_analytics.get('ai_adoption_rate', -1)
            
            if not (0 <= ai_success_rate <= 100):
                issues.append(f"Invalid AI success rate: {ai_success_rate}")
            
            if not (0 <= adoption_rate <= 100):
                issues.append(f"Invalid AI adoption rate: {adoption_rate}")
            
            # Validate date formats in trends
            registration_trends = user_analytics.get('registration_trends', [])
            for trend in registration_trends:
                if '_id' in trend:
                    try:
                        datetime.strptime(trend['_id'], '%Y-%m-%d')
                    except ValueError:
                        issues.append(f"Invalid date format in registration trends: {trend['_id']}")
                        break
            
            if issues:
                self.log_result("Data Quality Validation", False, 
                              f"Data quality issues: {'; '.join(issues)}")
                return False
            else:
                self.log_result("Data Quality Validation", True, 
                              "All data quality checks passed")
                return True
                
        except Exception as e:
            self.log_result("Data Quality Validation", False, f"Error: {str(e)}")
            return False
    
    def test_performance_requirements(self):
        """Test that all endpoints respond within 5 seconds"""
        if not self.admin_token:
            self.log_result("Performance Requirements", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            endpoints = [
                "/admin/analytics/users",
                "/admin/analytics/messages",
                "/admin/analytics/revenue", 
                "/admin/analytics/ai",
                "/admin/analytics/complete",
                "/admin/analytics/export?format=json"
            ]
            
            slow_endpoints = []
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    if response_time > 5.0:
                        slow_endpoints.append(f"{endpoint}: {response_time:.2f}s")
                    else:
                        print(f"   {endpoint}: {response_time:.2f}s ✓")
                else:
                    slow_endpoints.append(f"{endpoint}: HTTP {response.status_code}")
            
            if slow_endpoints:
                self.log_result("Performance Requirements", False, 
                              f"Slow/failed endpoints: {'; '.join(slow_endpoints)}")
                return False
            else:
                self.log_result("Performance Requirements", True, 
                              f"All {len(endpoints)} endpoints respond within 5 seconds")
                return True
                
        except Exception as e:
            self.log_result("Performance Requirements", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all analytics tests"""
        print("🚀 Starting Advanced Analytics Dashboard Backend Tests\n")
        
        # Setup
        if not self.setup_admin_user():
            print("❌ Cannot proceed without admin user")
            return False
        
        if not self.setup_regular_user():
            print("❌ Cannot proceed without regular user")
            return False
        
        # Authentication & Authorization Tests
        print("\n📋 Authentication & Authorization Tests:")
        self.test_admin_authentication()
        self.test_regular_user_authorization()
        self.test_invalid_token_rejection()
        
        # Analytics Endpoint Tests
        print("\n📊 Analytics Endpoint Tests:")
        self.test_user_analytics_endpoint()
        self.test_message_analytics_endpoint()
        self.test_revenue_analytics_endpoint()
        self.test_ai_analytics_endpoint()
        self.test_complete_analytics_endpoint()
        self.test_export_analytics_endpoint()
        
        # Data Quality & Performance Tests
        print("\n🔍 Data Quality & Performance Tests:")
        self.test_data_quality_validation()
        self.test_performance_requirements()
        
        # Summary
        print("\n" + "="*60)
        print("📊 ADVANCED ANALYTICS DASHBOARD TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = AdvancedAnalyticsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)