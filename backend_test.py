#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class DhanDraftAPITester:
    def __init__(self):
        self.base_url = "https://emergent-analyzer-1.preview.emergentagent.com/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log(self, message, success=None):
        """Log test results"""
        if success is True:
            print(f"✅ {message}")
            self.tests_passed += 1
        elif success is False:
            print(f"❌ {message}")
        else:
            print(f"ℹ️  {message}")
        self.tests_run += 1

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            
            if success:
                return True, response.json() if response.content else {}
            else:
                self.log(f"API {method} {endpoint} failed: Expected {expected_status}, got {response.status_code}", False)
                return False, {}
                
        except requests.exceptions.RequestException as e:
            self.log(f"API {method} {endpoint} error: {str(e)}", False)
            return False, {}

    def test_auth_endpoints(self):
        """Test authentication system"""
        print("\n🔐 Testing Authentication APIs...")
        
        # Test demo login
        success, response = self.make_request('POST', '/auth/login', {
            'email': 'demo@dhandraft.com',
            'password': 'Demo123!'
        })
        
        if success and 'data' in response and 'token' in response['data']:
            self.token = response['data']['token']
            self.user_id = response['data']['user']['id']
            self.log("Demo login successful", True)
            
            # Test auth/me endpoint
            success, _ = self.make_request('GET', '/auth/me')
            self.log("Get current user profile", success)
        else:
            self.log("Demo login failed", False)
            return False
            
        # Test register new user
        timestamp = datetime.now().strftime("%H%M%S")
        success, response = self.make_request('POST', '/auth/register', {
            'name': f'Test User {timestamp}',
            'email': f'test{timestamp}@example.com',
            'password': 'TestPass123!'
        })
        self.log("User registration", success)
        
        return True

    def test_overview_endpoints(self):
        """Test overview/dashboard APIs"""
        print("\n📊 Testing Overview APIs...")
        
        success, response = self.make_request('GET', '/overview/summary')
        if success and 'data' in response:
            data = response['data']
            # Check required fields
            required_fields = ['financialHealth', 'riskPersonality', 'portfolioAllocation', 'predictionAccuracy', 'taxOptimization', 'aiInsight', 'sectorSentiment']
            all_present = all(field in data for field in required_fields)
            self.log(f"Overview summary with all fields", all_present)
        else:
            self.log("Overview summary failed", False)

    def test_learn_endpoints(self):
        """Test learning/education APIs"""
        print("\n📚 Testing Learn APIs...")
        
        # Get lessons
        success, response = self.make_request('GET', '/learn/lessons')
        lessons = []
        if success and 'data' in response:
            lessons = response['data']
            self.log(f"Get lessons ({len(lessons)} found)", success and len(lessons) >= 5)
        else:
            self.log("Get lessons failed", False)
            
        # Test lesson detail
        if lessons:
            lesson_id = lessons[0]['id']
            success, _ = self.make_request('GET', f'/learn/lessons/{lesson_id}')
            self.log("Get lesson detail", success)
            
            # Test quiz submission
            success, response = self.make_request('POST', '/learn/quiz/submit', {
                'lessonId': lesson_id,
                'answers': [1, 0, 1, 2]  # Sample answers
            })
            self.log("Submit quiz", success)
            
        # Test quiz history
        success, _ = self.make_request('GET', '/learn/quiz/history')
        self.log("Get quiz history", success)
        
        # Test tax comparison
        success, _ = self.make_request('POST', '/learn/tax-compare', {
            'income': 1000000,
            'deductions_80c': 150000,
            'deductions_80d': 25000,
            'hra_exemption': 0,
            'other_deductions': 0
        })
        self.log("Tax regime comparison", success)
        
        # Test bank rates
        success, _ = self.make_request('GET', '/learn/bank-rates')
        self.log("Get bank rates", success)

    def test_markets_endpoints(self):
        """Test markets/stocks APIs"""
        print("\n📈 Testing Markets APIs...")
        
        # Get stocks list
        success, response = self.make_request('GET', '/markets/stocks')
        stocks = []
        if success and 'data' in response:
            stocks = response['data']
            self.log(f"Get stocks list ({len(stocks)} found)", success and len(stocks) >= 8)
        else:
            self.log("Get stocks list failed", False)
            
        # Test stock detail
        if stocks:
            symbol = stocks[0]['symbol']
            success, _ = self.make_request('GET', f'/markets/stocks/{symbol}')
            self.log("Get stock detail", success)
            
            # Test prediction
            success, _ = self.make_request('POST', '/markets/predict', {
                'stockSymbol': symbol,
                'predictedDirection': 'up'
            })
            self.log("Make stock prediction", success)
            
        # Test predictions history
        success, _ = self.make_request('GET', '/markets/predictions')
        self.log("Get predictions history", success)
        
        # Test sentiment analysis
        success, _ = self.make_request('GET', '/markets/sentiment')
        self.log("Get news sentiment", success)
        
        # Test heatmap
        success, _ = self.make_request('GET', '/markets/heatmap')
        self.log("Get sector heatmap", success)

    def test_portfolio_endpoints(self):
        """Test portfolio/tax APIs"""
        print("\n💼 Testing Portfolio & Tax APIs...")
        
        # Get assets
        success, _ = self.make_request('GET', '/portfolio/assets')
        self.log("Get portfolio assets", success)
        
        # Get portfolio summary
        success, response = self.make_request('GET', '/portfolio/summary')
        if success and 'data' in response:
            data = response['data']
            required_fields = ['totalValue', 'totalCost', 'totalGain', 'allocation', 'sectorDiversification']
            all_present = all(field in data for field in required_fields)
            self.log("Portfolio summary with all fields", all_present)
        else:
            self.log("Portfolio summary failed", False)
            
        # Test tax comparison
        success, _ = self.make_request('POST', '/portfolio/tax/compare', {
            'income': 1200000,
            'deductions_80c': 150000,
            'deductions_80d': 25000,
            'hra_exemption': 50000,
            'other_deductions': 0
        })
        self.log("Portfolio tax comparison", success)
        
        # Test capital gains
        success, _ = self.make_request('POST', '/portfolio/tax/capital-gains', {
            'buyPrice': 100,
            'sellPrice': 150,
            'quantity': 100,
            'holdingMonths': 14,
            'assetType': 'equity'
        })
        self.log("Capital gains calculation", success)
        
        # Test FD tax
        success, _ = self.make_request('POST', '/portfolio/tax/fd', {
            'principal': 500000,
            'rate': 7,
            'years': 3,
            'taxBracket': 30
        })
        self.log("FD tax calculation", success)

    def test_risk_endpoints(self):
        """Test risk & safety APIs"""
        print("\n🛡️  Testing Risk & Safety APIs...")
        
        # Test transaction risk
        success, response = self.make_request('POST', '/risk/transaction', {
            'amount': 75000,
            'type': 'bank_transfer',
            'description': 'Payment for services',
            'recipientNew': False
        })
        if success and 'data' in response:
            data = response['data']
            required_fields = ['risk_score', 'reasons', 'recommendation', 'confidence']
            all_present = all(field in data for field in required_fields)
            self.log("Transaction risk analysis", all_present)
        else:
            self.log("Transaction risk analysis failed", False)
            
        # Test fraud detection
        success, response = self.make_request('POST', '/risk/fraud', {
            'text': 'Congratulations! You have won a lottery prize of Rs.50,00,000. Click here to claim your prize urgently!'
        })
        if success and 'data' in response:
            data = response['data']
            required_fields = ['probability', 'verdict', 'keywords_found', 'recommendation']
            all_present = all(field in data for field in required_fields)
            self.log("Fraud detection analysis", all_present)
        else:
            self.log("Fraud detection analysis failed", False)

    def test_advisor_endpoints(self):
        """Test AI advisor APIs"""
        print("\n🤖 Testing AI Advisor APIs...")
        
        # Test advisor analysis
        success, response = self.make_request('POST', '/advisor/analyze', {
            'query': 'Review my portfolio and suggest improvements'
        })
        if success and 'data' in response:
            data = response['data']
            required_fields = ['strategy', 'tax_suggestion', 'risk_alert', 'sector_warning']
            all_present = all(field in data for field in required_fields)
            self.log("AI advisor analysis", all_present)
        else:
            self.log("AI advisor analysis failed", False)
            
        # Test advisor history
        success, _ = self.make_request('GET', '/advisor/history')
        self.log("Get advisor history", success)

    def test_alerts_endpoints(self):
        """Test new alerts/notifications APIs"""
        print("\n🔔 Testing Alerts/Notifications APIs...")
        
        # Test get alerts
        success, response = self.make_request('GET', '/alerts')
        if success and 'data' in response:
            data = response['data']
            required_fields = ['alerts', 'unread_count']
            all_present = all(field in data for field in required_fields)
            self.log(f"Get alerts (unread: {data.get('unread_count', 0)})", all_present)
            
            alerts = data.get('alerts', [])
            if alerts:
                # Test mark single alert as read
                alert_id = alerts[0]['id']
                success, _ = self.make_request('POST', '/alerts/mark-read', {'alertId': alert_id})
                self.log("Mark single alert as read", success)
        else:
            self.log("Get alerts failed", False)
            
        # Test mark all alerts as read
        success, _ = self.make_request('POST', '/alerts/mark-all-read')
        self.log("Mark all alerts as read", success)

    def test_community_endpoints(self):
        """Test community chat APIs"""
        print("\n💬 Testing Community Chat APIs...")
        
        # Test get community messages
        success, response = self.make_request('GET', '/community/messages')
        if success and 'data' in response:
            messages = response['data']
            self.log(f"Get community messages ({len(messages)} found)", len(messages) >= 4)
        else:
            self.log("Get community messages failed", False)

    def test_add_asset_endpoints(self):
        """Test add asset to portfolio API"""
        print("\n➕ Testing Add Asset APIs...")
        
        # First get available stocks
        success, response = self.make_request('GET', '/markets/stocks')
        if success and 'data' in response:
            stocks = response['data']
            if stocks:
                # Test add asset
                success, response = self.make_request('POST', '/portfolio/add-asset', {
                    'symbol': stocks[0]['symbol'],
                    'quantity': 5,
                    'buyPrice': stocks[0]['currentPrice']
                })
                if success and 'data' in response:
                    data = response['data']
                    required_fields = ['asset', 'updatedHealth']
                    all_present = all(field in data for field in required_fields)
                    self.log("Add asset to portfolio", all_present)
                else:
                    self.log("Add asset to portfolio failed", False)
            else:
                self.log("No stocks available for add asset test", False)
        else:
            self.log("Cannot get stocks for add asset test", False)

    def run_all_tests(self):
        """Run complete API test suite"""
        print("🚀 Starting DHAN-DRAFT API Testing...")
        print(f"📡 Base URL: {self.base_url}")
        
        # Test authentication first
        if not self.test_auth_endpoints():
            print("❌ Authentication failed - stopping tests")
            return False
            
        # Test all other endpoints
        self.test_overview_endpoints()
        self.test_learn_endpoints() 
        self.test_markets_endpoints()
        self.test_portfolio_endpoints()
        self.test_risk_endpoints()
        self.test_advisor_endpoints()
        
        # Test new features
        print("\n🆕 Testing NEW FEATURES...")
        self.test_alerts_endpoints()
        self.test_community_endpoints()  
        self.test_add_asset_endpoints()
        
        # Print summary
        print(f"\n📈 Test Results: {self.tests_passed}/{self.tests_run} passed ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend APIs working perfectly!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} API endpoints need attention")
            return False

def main():
    tester = DhanDraftAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())