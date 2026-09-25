"""
Comprehensive API Response Validation Script
Tests all major endpoints and validates response quality
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8002/api/v1"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class APITester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def print_header(self, title):
        print(f"\n{BOLD}{BLUE}{'='*100}{RESET}")
        print(f"{BOLD}{BLUE}{title.center(100)}{RESET}")
        print(f"{BOLD}{BLUE}{'='*100}{RESET}\n")

    def print_test(self, endpoint, result, message=""):
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status}  {endpoint:50} {message}")
        
        self.total_tests += 1
        if result:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def validate_response(self, endpoint: str, user_id: int = 2) -> Tuple[bool, str, Dict]:
        """Test an API endpoint and validate response structure."""
        try:
            url = f"{BASE_URL}{endpoint}?user_id={user_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return False, f"Status {response.status_code}", {}
            
            data = response.json()
            return True, "OK", data
        except Exception as e:
            return False, str(e), {}

    def test_athlete_api(self):
        """Test Athlete Performance API"""
        self.print_header("🏃 ATHLETE PERFORMANCE API TESTS")
        
        success, msg, data = self.validate_response("/athlete/readiness", user_id=2)
        self.print_test("/athlete/readiness", success, msg)
        
        if success and data:
            # Validate required fields
            required_fields = ["readiness_score", "readiness_level", "hrv", "recovery", "training_load", "metrics", "fatigue_alerts", "cycle_info", "recommendations"]
            
            all_present = all(field in data for field in required_fields)
            self.print_test("└─ All required fields present", all_present)
            
            if all_present:
                # Check metrics structure
                metrics = data.get("metrics", {})
                has_sleep_percentage = "percentage" in metrics.get("sleep", {})
                self.print_test("└─ Sleep uses percentage (not hours)", has_sleep_percentage, 
                              f"sleep: {metrics.get('sleep', {})}")
                
                # Check recovery status
                recovery_status = data.get("recovery", {}).get("status")
                valid_recovery = recovery_status in ["high", "low", "moderate"]
                self.print_test("└─ Recovery status is badge (high/low/moderate)", valid_recovery, 
                              f"status: {recovery_status}")
                
                # Check alerts generated
                alerts = data.get("fatigue_alerts", [])
                has_alerts = len(alerts) > 0
                self.print_test("└─ Personalized fatigue alerts generated", has_alerts, 
                              f"count: {len(alerts)}")
                
                if alerts:
                    alert_types = [a.get("type") for a in alerts]
                    expected_types = ["overtraining_risk", "injury_risk_index", "cumulative_fatigue"]
                    has_expected = any(t in alert_types for t in expected_types)
                    self.print_test("  └─ Alert types are personalized", has_expected, 
                                  f"types: {alert_types}")
                
                # Verify no readiness_message
                has_no_message = "readiness_message" not in data
                self.print_test("└─ readiness_message removed from response", has_no_message)
                
                # Verify no avoid in recommendations
                avoid_present = "avoid" in data.get("recommendations", {})
                self.print_test("└─ 'avoid' removed from recommendations", not avoid_present)
                
                print(f"\n{YELLOW}Sample Response:{RESET}")
                print(json.dumps({
                    "readiness_score": data.get("readiness_score"),
                    "readiness_level": data.get("readiness_level"),
                    "hrv": data.get("hrv"),
                    "recovery": data.get("recovery"),
                    "training_load": data.get("training_load"),
                    "metrics_available": list(data.get("metrics", {}).keys()),
                    "alerts_count": len(data.get("fatigue_alerts", [])),
                }, indent=2))

    def test_beauty_api(self):
        """Test Beauty/Radiance API"""
        self.print_header("💄 BEAUTY/RADIANCE API TESTS")
        
        success, msg, data = self.validate_response("/beauty/radiance", user_id=2)
        self.print_test("/beauty/radiance", success, msg)
        
        if success and data:
            # Validate required fields
            required_fields = ["date", "overall_assessment", "findings", "terra_correlation", "cycle_insights", "recommendations"]
            
            all_present = all(field in data for field in required_fields)
            self.print_test("└─ All required fields present", all_present)
            
            if all_present:
                # Check findings are AI-generated (not hardcoded)
                findings = data.get("findings", {})
                finding_items = findings.get("items", [])
                has_findings = len(finding_items) > 0
                self.print_test("└─ Dynamic findings generated", has_findings, 
                              f"count: {len(finding_items)}")
                
                if finding_items:
                    first_finding = finding_items[0]
                    has_description = len(first_finding.get("description", "")) > 20
                    self.print_test("  └─ Findings have personalized descriptions", has_description)
                
                # Check terra correlation
                terra_corr = data.get("terra_correlation")
                is_object = isinstance(terra_corr, dict)
                self.print_test("└─ Terra correlation data present", is_object)
                
                # Check cycle insights
                cycle_ins = data.get("cycle_insights")
                is_object = isinstance(cycle_ins, dict)
                self.print_test("└─ Cycle phase insights present", is_object)
                
                # Check recommendations
                recs = data.get("recommendations")
                is_list = isinstance(recs, list) and len(recs) > 0
                self.print_test("└─ AI-generated recommendations present", is_list, 
                              f"count: {len(recs) if isinstance(recs, list) else 0}")
                
                print(f"\n{YELLOW}Sample Response:{RESET}")
                print(json.dumps({
                    "overall_assessment": data.get("overall_assessment", "")[:100],
                    "findings_count": len(finding_items),
                    "cycle_phase": data.get("cycle_insights", {}).get("phase"),
                    "recommendations_count": len(recs) if isinstance(recs, list) else 0,
                }, indent=2))

    def test_cycle_api(self):
        """Test Cycle Awareness API"""
        self.print_header("🔄 CYCLE AWARENESS API TESTS")
        
        success, msg, data = self.validate_response("/cycle/phase-insights", user_id=2)
        self.print_test("/cycle/phase-insights", success, msg)
        
        if success and data:
            required_fields = ["current_phase", "cycle_day", "days_remaining", "phase_insights"]
            
            all_present = all(field in data for field in required_fields)
            self.print_test("└─ All required fields present", all_present)
            
            if all_present:
                phase = data.get("current_phase")
                valid_phase = phase in ["menstrual", "follicular", "ovulatory", "luteal", "unknown"]
                self.print_test("└─ Phase is valid", valid_phase, f"phase: {phase}")
                
                cycle_day = data.get("cycle_day")
                valid_day = isinstance(cycle_day, int) and 0 <= cycle_day <= 100
                self.print_test("└─ Cycle day is valid", valid_day, f"day: {cycle_day}")
                
                print(f"\n{YELLOW}Sample Response:{RESET}")
                print(json.dumps({
                    "current_phase": phase,
                    "cycle_day": cycle_day,
                    "days_remaining": data.get("days_remaining"),
                }, indent=2))

    def test_response_structure(self):
        """Test response structure and field types"""
        self.print_header("🔍 RESPONSE STRUCTURE VALIDATION")
        
        # Test Athlete API structure
        success, _, data = self.validate_response("/athlete/readiness", user_id=2)
        
        if success:
            # Check HRV structure
            hrv = data.get("hrv", {})
            hrv_valid = (
                isinstance(hrv.get("value"), int) and
                hrv.get("unit") == "ms" and
                isinstance(hrv.get("trend"), int) and
                hrv.get("status") in ["good", "warning", "poor"]
            )
            self.print_test("└─ HRV structure valid", hrv_valid)
            
            # Check Sleep structure (percentage-based)
            sleep = data.get("metrics", {}).get("sleep", {})
            sleep_valid = (
                isinstance(sleep.get("percentage"), int) and
                0 <= sleep.get("percentage", -1) <= 100 and
                isinstance(sleep.get("trend"), int)
            )
            self.print_test("└─ Sleep structure valid (percentage)", sleep_valid)
            
            # Check Recovery structure (percentage-based)
            recovery = data.get("recovery", {})
            recovery_valid = (
                isinstance(recovery.get("percentage"), int) and
                0 <= recovery.get("percentage", -1) <= 100 and
                recovery.get("status") in ["high", "low", "moderate"]
            )
            self.print_test("└─ Recovery structure valid (percentage + badge)", recovery_valid)
            
            # Check Training Load structure
            training = data.get("training_load", {})
            training_valid = (
                isinstance(training.get("value"), (int, float)) and
                training.get("unit") == "AU" and
                isinstance(training.get("trend"), int) and
                training.get("status") in ["low", "moderate", "high"]
            )
            self.print_test("└─ Training load structure valid", training_valid)

    def test_data_quality(self):
        """Test data quality (no zeros, real values)"""
        self.print_header("📊 DATA QUALITY CHECKS")
        
        success, _, data = self.validate_response("/athlete/readiness", user_id=2)
        
        if success:
            hrv_value = data.get("hrv", {}).get("value", 0)
            hrv_nonzero = hrv_value > 0
            self.print_test("└─ HRV value is non-zero", hrv_nonzero, f"value: {hrv_value}ms")
            
            sleep_pct = data.get("metrics", {}).get("sleep", {}).get("percentage", 0)
            sleep_valid = 0 < sleep_pct <= 100
            self.print_test("└─ Sleep percentage is valid", sleep_valid, f"value: {sleep_pct}%")
            
            recovery_pct = data.get("recovery", {}).get("percentage", 0)
            recovery_valid = 0 < recovery_pct <= 100
            self.print_test("└─ Recovery percentage is valid", recovery_valid, f"value: {recovery_pct}%")
            
            training_value = data.get("training_load", {}).get("value", 0)
            training_nonzero = training_value > 0
            self.print_test("└─ Training load is non-zero", training_nonzero, f"value: {training_value}AU")
            
            readiness = data.get("readiness_score", 0)
            readiness_valid = 0 <= readiness <= 100
            self.print_test("└─ Readiness score in valid range", readiness_valid, f"score: {readiness}")

    def test_multiple_users(self):
        """Test API works for multiple users"""
        self.print_header("👥 MULTI-USER VALIDATION")
        
        test_users = [2, 10, 16, 33]  # Users with various data
        
        for user_id in test_users:
            success, msg, data = self.validate_response("/athlete/readiness", user_id=user_id)
            status = "✅" if success else "❌"
            self.print_test(f"└─ User {user_id}", success, msg)

    def print_summary(self):
        """Print test summary"""
        self.print_header("📋 TEST SUMMARY")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        status_color = GREEN if pass_rate >= 90 else YELLOW if pass_rate >= 70 else RED
        
        print(f"{BOLD}Test Results:{RESET}")
        print(f"  Total Tests:   {self.total_tests}")
        print(f"  {GREEN}Passed:      {self.passed_tests}{RESET}")
        print(f"  {RED}Failed:      {self.failed_tests}{RESET}")
        print(f"  {status_color}Pass Rate:    {pass_rate:.1f}%{RESET}\n")
        
        if pass_rate >= 95:
            print(f"{GREEN}{BOLD}✅ ALL SYSTEMS GO! Backend team can relax 🎉{RESET}\n")
        elif pass_rate >= 80:
            print(f"{YELLOW}{BOLD}⚠️  Most tests passing, minor issues to address{RESET}\n")
        else:
            print(f"{RED}{BOLD}❌ Critical issues detected, needs attention{RESET}\n")

    def run_all_tests(self):
        """Run all test suites"""
        print(f"{BOLD}{BLUE}\n{'='*100}{RESET}")
        print(f"{BOLD}{BLUE}{'COMPREHENSIVE API RESPONSE VALIDATION'.center(100)}{RESET}")
        print(f"{BOLD}{BLUE}{'='*100}{RESET}\n")
        
        self.test_athlete_api()
        self.test_beauty_api()
        self.test_cycle_api()
        self.test_response_structure()
        self.test_data_quality()
        self.test_multiple_users()
        
        self.print_summary()


def main():
    tester = APITester()
    try:
        tester.run_all_tests()
    except Exception as e:
        print(f"{RED}Error running tests: {e}{RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
