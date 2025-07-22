#!/usr/bin/env python3
"""
MARKETING AUTOMATION SYSTEM COMPREHENSIVE TESTING
Tests the newly implemented Marketing Automation System backend endpoints:
- Marketing Campaigns (GET/POST)
- Marketing Templates (GET/POST) 
- Social Media Posts (GET/POST)
- Launch Metrics (GET)
- Launch Checklist (GET)
- Data Models Testing
- Content Integration Testing
- Business Logic Testing
- Admin Authorization Testing
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
print(f"🚀 Testing Marketing Automation System at: {API_BASE}")

class MarketingAutomationTester:
    def __init__(self):
        self.test_results = []
        self.admin_token = None
        self.regular_user_token = None
        self.created_campaign_ids = []
        self.created_template_ids = []
        self.created_post_ids = []
        
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
            # Try to create admin user
            admin_data = {
                "email": "admin@zeitgesteuerte.de",
                "password": "admin123",
                "name": "Admin User"
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=admin_data)
            if response.status_code == 200:
                self.admin_token = response.json()['access_token']
                print("   ✓ Admin user created successfully")
                return True
            else:
                # Try login if already exists
                login_response = requests.post(f"{API_BASE}/auth/login", json={
                    "email": admin_data['email'],
                    "password": admin_data['password']
                })
                if login_response.status_code == 200:
                    self.admin_token = login_response.json()['access_token']
                    print("   ✓ Admin user login successful")
                    return True
                else:
                    print(f"   ✗ Admin login failed: {login_response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"   ✗ Admin setup error: {str(e)}")
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
                print("   ✓ Regular user created successfully")
                return True
            else:
                print(f"   ✗ Regular user creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ✗ Regular user setup error: {str(e)}")
            return False
    
    def test_admin_authentication(self):
        """Test admin authentication for marketing endpoints"""
        if not self.admin_token:
            self.log_result("Admin Authentication", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test admin access to marketing campaigns endpoint
            response = requests.get(f"{API_BASE}/admin/marketing/campaigns", headers=headers)
            
            if response.status_code == 200:
                self.log_result("Admin Authentication", True, "Admin can access marketing endpoints")
                return True
            elif response.status_code == 403:
                self.log_result("Admin Authentication", False, "Admin access denied - role not properly set")
                return False
            else:
                self.log_result("Admin Authentication", False, f"Unexpected response: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_regular_user_authorization_blocked(self):
        """Test that regular users cannot access marketing endpoints"""
        if not self.regular_user_token:
            self.log_result("Regular User Authorization Block", False, "No regular user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.regular_user_token}"}
            
            # Test all marketing endpoints should return 403
            marketing_endpoints = [
                "/admin/marketing/campaigns",
                "/admin/marketing/templates", 
                "/admin/marketing/social-posts",
                "/admin/marketing/launch-metrics",
                "/admin/marketing/launch-checklist"
            ]
            
            blocked_count = 0
            for endpoint in marketing_endpoints:
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
                if response.status_code == 403:
                    blocked_count += 1
                else:
                    print(f"   ✗ Endpoint {endpoint} not blocked: HTTP {response.status_code}")
            
            if blocked_count == len(marketing_endpoints):
                self.log_result("Regular User Authorization Block", True, 
                              f"All {len(marketing_endpoints)} marketing endpoints properly blocked")
                return True
            else:
                self.log_result("Regular User Authorization Block", False, 
                              f"Only {blocked_count}/{len(marketing_endpoints)} endpoints blocked")
                return False
                
        except Exception as e:
            self.log_result("Regular User Authorization Block", False, f"Error: {str(e)}")
            return False
    
    def test_marketing_campaigns_get(self):
        """Test GET /api/admin/marketing/campaigns"""
        if not self.admin_token:
            self.log_result("Marketing Campaigns GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/marketing/campaigns", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if 'campaigns' in data and isinstance(data['campaigns'], list):
                    campaign_count = len(data['campaigns'])
                    self.log_result("Marketing Campaigns GET", True, 
                                  f"Retrieved {campaign_count} marketing campaigns")
                    return True
                else:
                    self.log_result("Marketing Campaigns GET", False, "Invalid response format")
                    return False
            else:
                self.log_result("Marketing Campaigns GET", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Marketing Campaigns GET", False, f"Error: {str(e)}")
            return False
    
    def test_marketing_campaigns_post(self):
        """Test POST /api/admin/marketing/campaigns"""
        if not self.admin_token:
            self.log_result("Marketing Campaigns POST", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test different campaign types
            test_campaigns = [
                {
                    "name": "Welcome Email Campaign",
                    "type": "email",
                    "target_audience": "new_users",
                    "content": {
                        "subject": "Willkommen bei Zeitgesteuerte Nachrichten!",
                        "body": "Herzlich willkommen! Hier sind deine ersten Schritte...",
                        "template_variables": ["first_name", "referral_code"]
                    },
                    "schedule_type": "triggered",
                    "trigger_event": "registration"
                },
                {
                    "name": "Social Media Launch Campaign",
                    "type": "social_media",
                    "target_audience": "all_users",
                    "content": {
                        "platforms": ["twitter", "linkedin"],
                        "message": "🚀 Neue KI-Nachrichten-App ist live! #KI #Deutschland",
                        "hashtags": ["#KI", "#Deutschland", "#Innovation"]
                    },
                    "schedule_type": "immediate"
                },
                {
                    "name": "Premium Upgrade Push",
                    "type": "push_notification",
                    "target_audience": "free_users",
                    "content": {
                        "title": "Upgrade zu Premium",
                        "body": "Unbegrenzte Nachrichten für nur €9.99/Monat",
                        "action_url": "/subscription"
                    },
                    "schedule_type": "scheduled",
                    "scheduled_time": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
                }
            ]
            
            success_count = 0
            for i, campaign_data in enumerate(test_campaigns):
                response = requests.post(f"{API_BASE}/admin/marketing/campaigns", 
                                       json=campaign_data, headers=headers)
                
                if response.status_code == 200:
                    created_campaign = response.json()
                    if (created_campaign.get('name') == campaign_data['name'] and
                        created_campaign.get('type') == campaign_data['type'] and
                        created_campaign.get('id')):
                        
                        self.created_campaign_ids.append(created_campaign['id'])
                        success_count += 1
                        print(f"   ✓ Campaign {i+1} ({campaign_data['type']}): Created successfully")
                    else:
                        print(f"   ✗ Campaign {i+1}: Invalid response data")
                else:
                    print(f"   ✗ Campaign {i+1}: HTTP {response.status_code} - {response.text}")
            
            if success_count == len(test_campaigns):
                self.log_result("Marketing Campaigns POST", True, 
                              f"All {len(test_campaigns)} campaign types created successfully")
                return True
            else:
                self.log_result("Marketing Campaigns POST", False, 
                              f"Only {success_count}/{len(test_campaigns)} campaigns created")
                return False
                
        except Exception as e:
            self.log_result("Marketing Campaigns POST", False, f"Error: {str(e)}")
            return False
    
    def test_marketing_templates_get(self):
        """Test GET /api/admin/marketing/templates"""
        if not self.admin_token:
            self.log_result("Marketing Templates GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/marketing/templates", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if ('predefined_templates' in data and 'custom_templates' in data and
                    isinstance(data['predefined_templates'], list) and
                    isinstance(data['custom_templates'], list)):
                    
                    predefined_count = len(data['predefined_templates'])
                    custom_count = len(data['custom_templates'])
                    
                    # Check predefined templates have required fields
                    if predefined_count > 0:
                        first_template = data['predefined_templates'][0]
                        required_fields = ['id', 'name', 'type', 'content', 'variables']
                        if all(field in first_template for field in required_fields):
                            # Check for German content
                            has_german_content = any('Willkommen' in str(template.get('content', '')) or 
                                                   'Herzlich' in str(template.get('content', ''))
                                                   for template in data['predefined_templates'])
                            
                            if has_german_content:
                                self.log_result("Marketing Templates GET", True, 
                                              f"Retrieved {predefined_count} predefined + {custom_count} custom templates with German content")
                                return True
                            else:
                                self.log_result("Marketing Templates GET", False, "No German content found in templates")
                                return False
                        else:
                            self.log_result("Marketing Templates GET", False, "Template missing required fields")
                            return False
                    else:
                        self.log_result("Marketing Templates GET", True, 
                                      f"Retrieved {predefined_count} predefined + {custom_count} custom templates")
                        return True
                else:
                    self.log_result("Marketing Templates GET", False, "Invalid response format")
                    return False
            else:
                self.log_result("Marketing Templates GET", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Marketing Templates GET", False, f"Error: {str(e)}")
            return False
    
    def test_marketing_templates_post(self):
        """Test POST /api/admin/marketing/templates"""
        if not self.admin_token:
            self.log_result("Marketing Templates POST", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test different template types
            test_templates = [
                {
                    "name": "Welcome Email Template",
                    "type": "email",
                    "subject": "Willkommen {{first_name}}!",
                    "content": """Hallo {{first_name}},

willkommen bei Zeitgesteuerte Nachrichten! 🎉

Deine ersten Schritte:
1. Erstelle deine erste KI-Nachricht
2. Nutze deinen Referral-Code: {{referral_code}}
3. Upgrade zu Premium für unbegrenzte Nachrichten

Viel Erfolg!
Das Team""",
                    "variables": ["first_name", "referral_code"],
                    "category": "welcome"
                },
                {
                    "name": "Social Media Post Template",
                    "type": "social_post",
                    "content": "🚀 {{app_name}} ist live! {{feature_highlight}} #KI #Deutschland #Innovation",
                    "variables": ["app_name", "feature_highlight"],
                    "category": "social_media"
                },
                {
                    "name": "Push Notification Template",
                    "type": "push_notification",
                    "subject": "{{notification_title}}",
                    "content": "{{message_body}} - Jetzt öffnen!",
                    "variables": ["notification_title", "message_body"],
                    "category": "notifications"
                }
            ]
            
            success_count = 0
            for i, template_data in enumerate(test_templates):
                response = requests.post(f"{API_BASE}/admin/marketing/templates", 
                                       json=template_data, headers=headers)
                
                if response.status_code == 200:
                    created_template = response.json()
                    if (created_template.get('name') == template_data['name'] and
                        created_template.get('type') == template_data['type'] and
                        created_template.get('id')):
                        
                        self.created_template_ids.append(created_template['id'])
                        success_count += 1
                        
                        # Check variables are properly identified
                        variables = created_template.get('variables', [])
                        expected_variables = template_data.get('variables', [])
                        if set(variables) == set(expected_variables):
                            print(f"   ✓ Template {i+1} ({template_data['type']}): Created with correct variables")
                        else:
                            print(f"   ⚠ Template {i+1}: Variables mismatch - expected {expected_variables}, got {variables}")
                    else:
                        print(f"   ✗ Template {i+1}: Invalid response data")
                else:
                    print(f"   ✗ Template {i+1}: HTTP {response.status_code} - {response.text}")
            
            if success_count == len(test_templates):
                self.log_result("Marketing Templates POST", True, 
                              f"All {len(test_templates)} template types created successfully")
                return True
            else:
                self.log_result("Marketing Templates POST", False, 
                              f"Only {success_count}/{len(test_templates)} templates created")
                return False
                
        except Exception as e:
            self.log_result("Marketing Templates POST", False, f"Error: {str(e)}")
            return False
    
    def test_social_media_posts_get(self):
        """Test GET /api/admin/marketing/social-posts"""
        if not self.admin_token:
            self.log_result("Social Media Posts GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/marketing/social-posts", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if ('ready_to_use_posts' in data and 'custom_posts' in data and
                    isinstance(data['ready_to_use_posts'], list) and
                    isinstance(data['custom_posts'], list)):
                    
                    ready_count = len(data['ready_to_use_posts'])
                    custom_count = len(data['custom_posts'])
                    
                    # Check ready-to-use posts have proper structure
                    if ready_count > 0:
                        first_post = data['ready_to_use_posts'][0]
                        required_fields = ['platform', 'content', 'hashtags']
                        if all(field in first_post for field in required_fields):
                            # Check for German content and proper hashtags
                            has_german_hashtags = any('#KI' in str(post.get('hashtags', [])) or 
                                                    '#Deutschland' in str(post.get('hashtags', []))
                                                    for post in data['ready_to_use_posts'])
                            
                            # Check platform-specific posts
                            platforms = set(post.get('platform') for post in data['ready_to_use_posts'])
                            expected_platforms = {'twitter', 'linkedin', 'facebook', 'instagram'}
                            
                            if has_german_hashtags and platforms.intersection(expected_platforms):
                                self.log_result("Social Media Posts GET", True, 
                                              f"Retrieved {ready_count} ready-to-use + {custom_count} custom posts with German hashtags")
                                return True
                            else:
                                self.log_result("Social Media Posts GET", False, 
                                              f"Missing German hashtags or platforms. Platforms: {platforms}")
                                return False
                        else:
                            self.log_result("Social Media Posts GET", False, "Post missing required fields")
                            return False
                    else:
                        self.log_result("Social Media Posts GET", True, 
                                      f"Retrieved {ready_count} ready-to-use + {custom_count} custom posts")
                        return True
                else:
                    self.log_result("Social Media Posts GET", False, "Invalid response format")
                    return False
            else:
                self.log_result("Social Media Posts GET", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Social Media Posts GET", False, f"Error: {str(e)}")
            return False
    
    def test_social_media_posts_post(self):
        """Test POST /api/admin/marketing/social-posts"""
        if not self.admin_token:
            self.log_result("Social Media Posts POST", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test different platform posts
            test_posts = [
                {
                    "platform": "twitter",
                    "content": "🚀 Zeitgesteuerte Nachrichten ist live! Deutsche KI schreibt perfekte Nachrichten ⏰ #KI #Deutschland #Innovation",
                    "hashtags": ["#KI", "#Deutschland", "#Innovation", "#StartUp"],
                    "status": "draft"
                },
                {
                    "platform": "linkedin",
                    "content": "🎯 Revolutioniere deine Business-Kommunikation mit KI-generierten Nachrichten. Zeitgesteuerte Zustellung für maximale Effizienz. #BusinessEffizienz #KI",
                    "hashtags": ["#BusinessEffizienz", "#KI", "#Produktivität"],
                    "scheduled_time": (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z",
                    "status": "scheduled"
                },
                {
                    "platform": "facebook",
                    "content": "Neu: KI-Nachrichten-App für Deutschland! 🇩🇪 Perfekte deutsche Texte, zeitgesteuerte Zustellung. Jetzt kostenlos testen!",
                    "hashtags": ["#KI", "#Deutschland", "#Kostenlos"],
                    "media_urls": ["https://example.com/app-screenshot.jpg"],
                    "status": "draft"
                },
                {
                    "platform": "instagram",
                    "content": "✨ KI + Deutsche Sprache = Perfekte Nachrichten 📱 Zeitgesteuerte Zustellung war nie einfacher! #KI #Deutschland #App",
                    "hashtags": ["#KI", "#Deutschland", "#App", "#Innovation"],
                    "media_urls": ["https://example.com/instagram-post.jpg"],
                    "status": "draft"
                }
            ]
            
            success_count = 0
            for i, post_data in enumerate(test_posts):
                response = requests.post(f"{API_BASE}/admin/marketing/social-posts", 
                                       json=post_data, headers=headers)
                
                if response.status_code == 200:
                    created_post = response.json()
                    if (created_post.get('platform') == post_data['platform'] and
                        created_post.get('content') == post_data['content'] and
                        created_post.get('id')):
                        
                        self.created_post_ids.append(created_post['id'])
                        success_count += 1
                        
                        # Check hashtags are properly stored
                        hashtags = created_post.get('hashtags', [])
                        expected_hashtags = post_data.get('hashtags', [])
                        if set(hashtags) == set(expected_hashtags):
                            print(f"   ✓ Post {i+1} ({post_data['platform']}): Created with correct hashtags")
                        else:
                            print(f"   ⚠ Post {i+1}: Hashtags mismatch")
                    else:
                        print(f"   ✗ Post {i+1}: Invalid response data")
                else:
                    print(f"   ✗ Post {i+1}: HTTP {response.status_code} - {response.text}")
            
            if success_count == len(test_posts):
                self.log_result("Social Media Posts POST", True, 
                              f"All {len(test_posts)} platform posts created successfully")
                return True
            else:
                self.log_result("Social Media Posts POST", False, 
                              f"Only {success_count}/{len(test_posts)} posts created")
                return False
                
        except Exception as e:
            self.log_result("Social Media Posts POST", False, f"Error: {str(e)}")
            return False
    
    def test_launch_metrics_get(self):
        """Test GET /api/admin/marketing/launch-metrics"""
        if not self.admin_token:
            self.log_result("Launch Metrics GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/marketing/launch-metrics", headers=headers)
            
            if response.status_code == 200:
                metrics = response.json()
                
                # Check required metrics fields
                required_fields = [
                    'new_registrations', 'premium_conversions', 'referral_signups',
                    'daily_active_users', 'social_engagement', 'email_opens', 'campaign_clicks'
                ]
                
                if all(field in metrics for field in required_fields):
                    # Check data types are correct
                    all_integers = all(isinstance(metrics[field], int) for field in required_fields)
                    
                    if all_integers:
                        # Check values are reasonable (non-negative)
                        all_non_negative = all(metrics[field] >= 0 for field in required_fields)
                        
                        if all_non_negative:
                            self.log_result("Launch Metrics GET", True, 
                                          f"Daily metrics: {metrics['new_registrations']} new users, "
                                          f"{metrics['premium_conversions']} conversions, "
                                          f"{metrics['daily_active_users']} DAU")
                            return True
                        else:
                            self.log_result("Launch Metrics GET", False, "Negative values in metrics")
                            return False
                    else:
                        self.log_result("Launch Metrics GET", False, "Invalid data types in metrics")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in metrics]
                    self.log_result("Launch Metrics GET", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_result("Launch Metrics GET", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Launch Metrics GET", False, f"Error: {str(e)}")
            return False
    
    def test_launch_checklist_get(self):
        """Test GET /api/admin/marketing/launch-checklist"""
        if not self.admin_token:
            self.log_result("Launch Checklist GET", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/admin/marketing/launch-checklist", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'checklist' in data and isinstance(data['checklist'], list):
                    checklist = data['checklist']
                    
                    # Check checklist structure
                    if len(checklist) > 0:
                        # Check categories exist
                        categories = [item.get('category') for item in checklist]
                        expected_categories = ['TECHNIK', 'MARKETING', 'BUSINESS']
                        
                        if all(cat in categories for cat in expected_categories):
                            # Check items structure
                            total_items = 0
                            completed_items = 0
                            
                            for category in checklist:
                                if 'items' in category and isinstance(category['items'], list):
                                    for item in category['items']:
                                        if 'task' in item and 'completed' in item:
                                            total_items += 1
                                            if item['completed']:
                                                completed_items += 1
                                        else:
                                            self.log_result("Launch Checklist GET", False, "Invalid item structure")
                                            return False
                                else:
                                    self.log_result("Launch Checklist GET", False, "Invalid category structure")
                                    return False
                            
                            completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
                            
                            self.log_result("Launch Checklist GET", True, 
                                          f"Checklist with {total_items} items, {completion_rate:.1f}% complete")
                            return True
                        else:
                            missing_categories = [cat for cat in expected_categories if cat not in categories]
                            self.log_result("Launch Checklist GET", False, f"Missing categories: {missing_categories}")
                            return False
                    else:
                        self.log_result("Launch Checklist GET", False, "Empty checklist")
                        return False
                else:
                    self.log_result("Launch Checklist GET", False, "Invalid response format")
                    return False
            else:
                self.log_result("Launch Checklist GET", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Launch Checklist GET", False, f"Error: {str(e)}")
            return False
    
    def test_template_variables_identification(self):
        """Test that template variables like {{first_name}} are properly identified"""
        if not self.admin_token:
            self.log_result("Template Variables Identification", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Create template with various variables
            template_data = {
                "name": "Variable Test Template",
                "type": "email",
                "subject": "Hello {{first_name}}!",
                "content": """Dear {{first_name}} {{last_name}},

Welcome to {{app_name}}! Your referral code is {{referral_code}}.

Your subscription: {{subscription_plan}}
Messages remaining: {{messages_remaining}}

Best regards,
{{sender_name}}""",
                "variables": ["first_name", "last_name", "app_name", "referral_code", "subscription_plan", "messages_remaining", "sender_name"],
                "category": "test"
            }
            
            response = requests.post(f"{API_BASE}/admin/marketing/templates", 
                                   json=template_data, headers=headers)
            
            if response.status_code == 200:
                created_template = response.json()
                returned_variables = set(created_template.get('variables', []))
                expected_variables = set(template_data['variables'])
                
                if returned_variables == expected_variables:
                    self.log_result("Template Variables Identification", True, 
                                  f"All {len(expected_variables)} template variables correctly identified")
                    return True
                else:
                    missing = expected_variables - returned_variables
                    extra = returned_variables - expected_variables
                    self.log_result("Template Variables Identification", False, 
                                  f"Variable mismatch - Missing: {missing}, Extra: {extra}")
                    return False
            else:
                self.log_result("Template Variables Identification", False, 
                              f"Template creation failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Template Variables Identification", False, f"Error: {str(e)}")
            return False
    
    def test_business_logic_calculations(self):
        """Test business logic calculations in launch metrics"""
        if not self.admin_token:
            self.log_result("Business Logic Calculations", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get current metrics
            response = requests.get(f"{API_BASE}/admin/marketing/launch-metrics", headers=headers)
            
            if response.status_code == 200:
                metrics = response.json()
                
                # Test logical relationships
                new_registrations = metrics.get('new_registrations', 0)
                premium_conversions = metrics.get('premium_conversions', 0)
                referral_signups = metrics.get('referral_signups', 0)
                daily_active_users = metrics.get('daily_active_users', 0)
                
                # Business logic checks
                logic_checks = []
                
                # Premium conversions shouldn't exceed new registrations
                if premium_conversions <= new_registrations:
                    logic_checks.append("Premium conversions ≤ new registrations")
                else:
                    logic_checks.append("❌ Premium conversions > new registrations")
                
                # Referral signups shouldn't exceed new registrations
                if referral_signups <= new_registrations:
                    logic_checks.append("Referral signups ≤ new registrations")
                else:
                    logic_checks.append("❌ Referral signups > new registrations")
                
                # DAU should be reasonable compared to new registrations
                if daily_active_users >= 0:  # Just check non-negative for now
                    logic_checks.append("DAU is non-negative")
                else:
                    logic_checks.append("❌ DAU is negative")
                
                # Check if all logic checks passed
                failed_checks = [check for check in logic_checks if check.startswith("❌")]
                
                if len(failed_checks) == 0:
                    self.log_result("Business Logic Calculations", True, 
                                  f"All business logic checks passed: {', '.join(logic_checks)}")
                    return True
                else:
                    self.log_result("Business Logic Calculations", False, 
                                  f"Failed checks: {', '.join(failed_checks)}")
                    return False
            else:
                self.log_result("Business Logic Calculations", False, 
                              f"Could not get metrics: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Business Logic Calculations", False, f"Error: {str(e)}")
            return False
    
    def test_data_quality_german_content(self):
        """Test data quality - German content in templates and posts"""
        if not self.admin_token:
            self.log_result("Data Quality German Content", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Check templates for German content
            templates_response = requests.get(f"{API_BASE}/admin/marketing/templates", headers=headers)
            posts_response = requests.get(f"{API_BASE}/admin/marketing/social-posts", headers=headers)
            
            if templates_response.status_code == 200 and posts_response.status_code == 200:
                templates_data = templates_response.json()
                posts_data = posts_response.json()
                
                # German indicators to look for
                german_indicators = [
                    'Willkommen', 'Herzlich', 'Hallo', 'Sehr geehrte', 'Mit freundlichen Grüßen',
                    'Deutschland', 'deutsch', 'KI', 'Nachrichten', 'Zeitgesteuerte'
                ]
                
                # Check templates
                template_german_count = 0
                all_templates = templates_data.get('predefined_templates', []) + templates_data.get('custom_templates', [])
                
                for template in all_templates:
                    content = str(template.get('content', '')) + str(template.get('subject', ''))
                    if any(indicator in content for indicator in german_indicators):
                        template_german_count += 1
                
                # Check posts
                post_german_count = 0
                all_posts = posts_data.get('ready_to_use_posts', []) + posts_data.get('custom_posts', [])
                
                for post in all_posts:
                    content = str(post.get('content', ''))
                    hashtags = str(post.get('hashtags', []))
                    if any(indicator in content + hashtags for indicator in german_indicators):
                        post_german_count += 1
                
                total_templates = len(all_templates)
                total_posts = len(all_posts)
                
                if total_templates > 0 and total_posts > 0:
                    template_german_ratio = template_german_count / total_templates
                    post_german_ratio = post_german_count / total_posts
                    
                    # Expect at least 50% German content
                    if template_german_ratio >= 0.5 and post_german_ratio >= 0.5:
                        self.log_result("Data Quality German Content", True, 
                                      f"German content: {template_german_count}/{total_templates} templates, "
                                      f"{post_german_count}/{total_posts} posts")
                        return True
                    else:
                        self.log_result("Data Quality German Content", False, 
                                      f"Insufficient German content: {template_german_ratio:.1%} templates, "
                                      f"{post_german_ratio:.1%} posts")
                        return False
                else:
                    self.log_result("Data Quality German Content", True, 
                                  "No content to check (empty collections)")
                    return True
            else:
                self.log_result("Data Quality German Content", False, 
                              "Could not retrieve templates or posts")
                return False
                
        except Exception as e:
            self.log_result("Data Quality German Content", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all marketing automation tests"""
        print("🚀 MARKETING AUTOMATION SYSTEM COMPREHENSIVE TESTING")
        print("=" * 60)
        
        # Setup phase
        print("\n📋 SETUP PHASE")
        if not self.setup_admin_user():
            print("❌ Cannot proceed without admin user")
            return False
        
        if not self.setup_regular_user():
            print("⚠️ Regular user setup failed - some tests will be skipped")
        
        # Test phases
        test_phases = [
            ("🔐 AUTHENTICATION & AUTHORIZATION TESTS", [
                self.test_admin_authentication,
                self.test_regular_user_authorization_blocked
            ]),
            ("📊 MARKETING CAMPAIGNS TESTS", [
                self.test_marketing_campaigns_get,
                self.test_marketing_campaigns_post
            ]),
            ("📝 MARKETING TEMPLATES TESTS", [
                self.test_marketing_templates_get,
                self.test_marketing_templates_post,
                self.test_template_variables_identification
            ]),
            ("📱 SOCIAL MEDIA POSTS TESTS", [
                self.test_social_media_posts_get,
                self.test_social_media_posts_post
            ]),
            ("📈 LAUNCH METRICS & CHECKLIST TESTS", [
                self.test_launch_metrics_get,
                self.test_launch_checklist_get
            ]),
            ("🧠 BUSINESS LOGIC & DATA QUALITY TESTS", [
                self.test_business_logic_calculations,
                self.test_data_quality_german_content
            ])
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for phase_name, tests in test_phases:
            print(f"\n{phase_name}")
            print("-" * 50)
            
            for test_func in tests:
                total_tests += 1
                if test_func():
                    passed_tests += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🎯 MARKETING AUTOMATION TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL MARKETING AUTOMATION TESTS PASSED!")
            return True
        else:
            print("⚠️ Some tests failed - check details above")
            return False

if __name__ == "__main__":
    tester = MarketingAutomationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)