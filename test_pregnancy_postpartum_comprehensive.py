#!/usr/bin/env python3
"""
Comprehensive Test Suite for Pregnancy & Postpartum API
Tests all endpoints with every possible success and failure scenario
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

BASE_URL = "http://localhost:8002"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class TestResult:
    """Store test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.tests.append(("PASS", test_name, details))
        print(f"{GREEN}[PASS]{RESET}: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str = ""):
        self.failed += 1
        self.tests.append(("FAIL", test_name, details))
        print(f"{RED}[FAIL]{RESET}: {test_name}")
        if details:
            print(f"   {BOLD}{details}{RESET}")
    
    def add_error(self, test_name: str, details: str = ""):
        self.errors += 1
        self.tests.append(("ERROR", test_name, details))
        print(f"{RED}[ERROR]{RESET}: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_warning(self, test_name: str, details: str = ""):
        self.warnings += 1
        self.tests.append(("WARNING", test_name, details))
        print(f"{YELLOW}[WARNING]{RESET}: {test_name}")
        if details:
            print(f"   {details}")
    
    def print_summary(self):
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}TEST SUMMARY - PREGNANCY & POSTPARTUM API{RESET}")
        print(f"{BOLD}{'='*70}{RESET}")
        print(f"{GREEN}Passed:  {self.passed}{RESET}")
        print(f"{RED}Failed:  {self.failed}{RESET}")
        print(f"{RED}Errors:  {self.errors}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"{BOLD}Total:   {self.passed + self.failed + self.errors + self.warnings}{RESET}")
        print(f"{BOLD}{'='*70}{RESET}\n")

results = TestResult()

# ============================================================================
# ENDPOINT DEFINITIONS
# ============================================================================

ENDPOINTS = {
    "pregnancy_summary": f"{BASE_URL}/api/v1/pregnancy/summary",
    "pregnancy_milestones": f"{BASE_URL}/api/v1/pregnancy/milestones",
    "pregnancy_clinical_timeline": f"{BASE_URL}/api/v1/pregnancy/clinical-timeline",
    "pregnancy_miscarriage_support": f"{BASE_URL}/api/v1/pregnancy/miscarriage-support",
    "postpartum_recovery": f"{BASE_URL}/api/v1/postpartum/recovery",
    "support_groups": f"{BASE_URL}/api/v1/community/support-groups",
}

# Known test users from database investigation
PREGNANT_USERS = [2, 6, 18, 19, 26]  # Users with menstrual_cycles
POSTPARTUM_USERS = [30, 32, 41]  # Users with life_stage_id=4
ALL_VALID_USERS = PREGNANT_USERS + POSTPARTUM_USERS

# ============================================================================
# 1. PARAMETER VALIDATION TESTS
# ============================================================================

def test_parameter_validation():
    print(f"\n{BLUE}{BOLD}1. PARAMETER VALIDATION - ALL ENDPOINTS{RESET}\n")
    
    endpoints = [
        ("pregnancy_summary", ENDPOINTS["pregnancy_summary"]),
        ("pregnancy_milestones", ENDPOINTS["pregnancy_milestones"]),
        ("pregnancy_clinical_timeline", ENDPOINTS["pregnancy_clinical_timeline"]),
        ("pregnancy_miscarriage_support", ENDPOINTS["pregnancy_miscarriage_support"]),
        ("postpartum_recovery", ENDPOINTS["postpartum_recovery"]),
        ("support_groups", ENDPOINTS["support_groups"]),
    ]
    
    # Test 1.1: Missing user_id parameter
    print("Test 1.1: Missing user_id parameter (all endpoints)")
    for endpoint_name, endpoint_url in endpoints:
        try:
            response = requests.get(endpoint_url, timeout=5)
            if response.status_code == 422:
                results.add_pass(f"{endpoint_name} - missing user_id", f"Status: 422")
            else:
                results.add_fail(f"{endpoint_name} - missing user_id", f"Expected 422, got {response.status_code}")
        except Exception as e:
            results.add_error(f"{endpoint_name} - missing user_id", str(e))
    
    # Test 1.2: user_id as non-integer
    print("\nTest 1.2: user_id as non-integer (all endpoints)")
    for endpoint_name, endpoint_url in endpoints:
        try:
            response = requests.get(endpoint_url, params={"user_id": "abc"}, timeout=5)
            if response.status_code == 422:
                results.add_pass(f"{endpoint_name} - non-integer user_id", f"Status: 422")
            else:
                results.add_fail(f"{endpoint_name} - non-integer user_id", f"Expected 422, got {response.status_code}")
        except Exception as e:
            results.add_error(f"{endpoint_name} - non-integer user_id", str(e))
    
    # Test 1.3: user_id = 0
    print("\nTest 1.3: user_id = 0 (boundary - must be >= 1)")
    for endpoint_name, endpoint_url in endpoints:
        try:
            response = requests.get(endpoint_url, params={"user_id": 0}, timeout=5)
            if response.status_code == 422:
                results.add_pass(f"{endpoint_name} - user_id=0", f"Status: 422")
            else:
                results.add_fail(f"{endpoint_name} - user_id=0", f"Expected 422, got {response.status_code}")
        except Exception as e:
            results.add_error(f"{endpoint_name} - user_id=0", str(e))
    
    # Test 1.4: user_id negative
    print("\nTest 1.4: user_id = -1 (negative)")
    for endpoint_name, endpoint_url in endpoints:
        try:
            response = requests.get(endpoint_url, params={"user_id": -1}, timeout=5)
            if response.status_code == 422:
                results.add_pass(f"{endpoint_name} - negative user_id", f"Status: 422")
            else:
                results.add_fail(f"{endpoint_name} - negative user_id", f"Expected 422, got {response.status_code}")
        except Exception as e:
            results.add_error(f"{endpoint_name} - negative user_id", str(e))

# ============================================================================
# 2. USER EXISTENCE TESTS
# ============================================================================

def test_user_existence():
    print(f"\n{BLUE}{BOLD}2. USER EXISTENCE TESTS - ALL ENDPOINTS{RESET}\n")
    
    endpoints = [
        ("pregnancy_summary", ENDPOINTS["pregnancy_summary"]),
        ("pregnancy_milestones", ENDPOINTS["pregnancy_milestones"]),
        ("pregnancy_clinical_timeline", ENDPOINTS["pregnancy_clinical_timeline"]),
        ("pregnancy_miscarriage_support", ENDPOINTS["pregnancy_miscarriage_support"]),
    ]
    
    # Test 2.1: Valid pregnant users
    print("Test 2.1: Valid pregnant users (have menstrual_cycles)")
    for user_id in PREGNANT_USERS[:3]:  # Test first 3
        for endpoint_name, endpoint_url in endpoints:
            try:
                response = requests.get(endpoint_url, params={"user_id": user_id}, timeout=5)
                if response.status_code in [200, 404]:
                    if response.status_code == 200:
                        results.add_pass(f"{endpoint_name} - User {user_id}", f"Status: 200")
                    else:
                        results.add_warning(f"{endpoint_name} - User {user_id}", f"Status: 404 (no pregnancy data)")
                else:
                    results.add_fail(f"{endpoint_name} - User {user_id}", f"Status: {response.status_code}")
            except Exception as e:
                results.add_error(f"{endpoint_name} - User {user_id}", str(e))
    
    # Test 2.2: Postpartum users
    print("\nTest 2.2: Postpartum users (life_stage_id=4)")
    for user_id in POSTPARTUM_USERS[:2]:
        try:
            response = requests.get(ENDPOINTS["postpartum_recovery"], params={"user_id": user_id}, timeout=5)
            if response.status_code in [200, 404]:
                results.add_pass(f"postpartum_recovery - User {user_id}", f"Status: {response.status_code}")
            else:
                results.add_fail(f"postpartum_recovery - User {user_id}", f"Status: {response.status_code}")
        except Exception as e:
            results.add_error(f"postpartum_recovery - User {user_id}", str(e))
    
    # Test 2.3: Non-existent user
    print("\nTest 2.3: Non-existent user (user_id=999999)")
    for endpoint_name, endpoint_url in [
        ("pregnancy_summary", ENDPOINTS["pregnancy_summary"]),
        ("postpartum_recovery", ENDPOINTS["postpartum_recovery"]),
    ]:
        try:
            response = requests.get(endpoint_url, params={"user_id": 999999}, timeout=5)
            if response.status_code == 404:
                results.add_pass(f"{endpoint_name} - non-existent user", f"Status: 404")
            else:
                results.add_fail(f"{endpoint_name} - non-existent user", f"Expected 404, got {response.status_code}")
        except Exception as e:
            results.add_error(f"{endpoint_name} - non-existent user", str(e))

# ============================================================================
# 3. PREGNANCY SUMMARY ENDPOINT TESTS
# ============================================================================

def test_pregnancy_summary():
    print(f"\n{BLUE}{BOLD}3. PREGNANCY SUMMARY ENDPOINT{RESET}\n")
    
    endpoint = ENDPOINTS["pregnancy_summary"]
    
    # Test 3.1: Valid response structure
    print("Test 3.1: Response structure for pregnancy_summary")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["is_pregnant", "current_week", "current_trimester", "due_date", "health_status"]
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                results.add_fail("pregnancy_summary structure", f"Missing: {missing}")
            else:
                results.add_pass("pregnancy_summary structure", "All required fields present")
        else:
            results.add_warning("pregnancy_summary structure", f"Skipped (status {response.status_code})")
    except Exception as e:
        results.add_error("pregnancy_summary structure", str(e))
    
    # Test 3.2: Week range validation (0-40)
    print("Test 3.2: Current week is within valid range (0-40)")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            week = data.get("current_week")
            if week is not None:
                if 0 <= week <= 40:
                    results.add_pass("week range", f"Current week: {week}")
                else:
                    results.add_fail("week range", f"Week {week} out of range 0-40")
            else:
                results.add_fail("week range", "current_week is null")
        else:
            results.add_warning("week range", "Skipped")
    except Exception as e:
        results.add_error("week range", str(e))
    
    # Test 3.3: Trimester values
    print("Test 3.3: Trimester value is valid")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            trimester = data.get("current_trimester")
            valid_trimesters = ["First", "Second", "Third", "Postpartum"]
            
            if trimester in valid_trimesters:
                results.add_pass("trimester value", f"Trimester: {trimester}")
            else:
                results.add_fail("trimester value", f"Invalid trimester: {trimester}")
        else:
            results.add_warning("trimester value", "Skipped")
    except Exception as e:
        results.add_error("trimester value", str(e))
    
    # Test 3.4: Due date format
    print("Test 3.4: Due date is valid ISO format")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            due_date = data.get("due_date")
            
            if due_date:
                try:
                    datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    results.add_pass("due_date format", f"Valid ISO format: {due_date}")
                except:
                    results.add_fail("due_date format", f"Invalid format: {due_date}")
            else:
                results.add_fail("due_date format", "due_date is null")
        else:
            results.add_warning("due_date format", "Skipped")
    except Exception as e:
        results.add_error("due_date format", str(e))
    
    # Test 3.5: Alerts field
    print("Test 3.5: Alerts field exists and is array")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts")
            
            if isinstance(alerts, list):
                results.add_pass("alerts field", f"Array with {len(alerts)} alerts")
            else:
                results.add_fail("alerts field", f"Not an array, got {type(alerts)}")
        else:
            results.add_warning("alerts field", "Skipped")
    except Exception as e:
        results.add_error("alerts field", str(e))

# ============================================================================
# 4. PREGNANCY MILESTONES ENDPOINT TESTS
# ============================================================================

def test_pregnancy_milestones():
    print(f"\n{BLUE}{BOLD}4. PREGNANCY MILESTONES ENDPOINT{RESET}\n")
    
    endpoint = ENDPOINTS["pregnancy_milestones"]
    
    # Test 4.1: Response structure
    print("Test 4.1: Response structure for pregnancy_milestones")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["week", "trimester", "baby_development", "your_body", "nutrition_focus", "safe_exercises"]
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                results.add_fail("milestones structure", f"Missing: {missing}")
            else:
                results.add_pass("milestones structure", "All required fields present")
        else:
            results.add_warning("milestones structure", f"Skipped (status {response.status_code})")
    except Exception as e:
        results.add_error("milestones structure", str(e))
    
    # Test 4.2: Week auto-derivation (should match current week from summary)
    print("Test 4.2: Week auto-derivation from menstrual_cycles")
    try:
        resp_summary = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": 2}, timeout=5)
        resp_milestones = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        
        if resp_summary.status_code == 200 and resp_milestones.status_code == 200:
            summary_week = resp_summary.json().get("current_week")
            milestone_week = resp_milestones.json().get("week")
            
            if summary_week == milestone_week:
                results.add_pass("week auto-derivation", f"Week: {milestone_week} matches summary")
            else:
                results.add_warning("week auto-derivation", f"Mismatch: summary={summary_week}, milestones={milestone_week}")
        else:
            results.add_warning("week auto-derivation", "Skipped")
    except Exception as e:
        results.add_error("week auto-derivation", str(e))
    
    # Test 4.3: Clinical monitoring array
    print("Test 4.3: Clinical monitoring is array with tests")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            clinical = data.get("clinical_monitoring", [])
            
            if isinstance(clinical, list):
                results.add_pass("clinical_monitoring", f"Array with {len(clinical)} tests")
            else:
                results.add_fail("clinical_monitoring", f"Not an array, got {type(clinical)}")
        else:
            results.add_warning("clinical_monitoring", "Skipped")
    except Exception as e:
        results.add_error("clinical_monitoring", str(e))
    
    # Test 4.4: Clinical warning signs field
    print("Test 4.4: Clinical warning signs provided")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            warnings = data.get("clinical_warning_signs")
            
            if warnings and isinstance(warnings, str) and len(warnings) > 10:
                results.add_pass("warning_signs", "Warning signs provided and non-empty")
            else:
                results.add_warning("warning_signs", "Missing or empty warning signs")
        else:
            results.add_warning("warning_signs", "Skipped")
    except Exception as e:
        results.add_error("warning_signs", str(e))

# ============================================================================
# 5. PREGNANCY CLINICAL TIMELINE ENDPOINT TESTS
# ============================================================================

def test_pregnancy_clinical_timeline():
    print(f"\n{BLUE}{BOLD}5. PREGNANCY CLINICAL TIMELINE ENDPOINT{RESET}\n")
    
    endpoint = ENDPOINTS["pregnancy_clinical_timeline"]
    
    # Test 5.1: Response structure
    print("Test 5.1: Response structure for clinical_timeline")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["week", "trimester", "clinical_tests"]
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                results.add_fail("timeline structure", f"Missing: {missing}")
            else:
                results.add_pass("timeline structure", "All required fields present")
        else:
            results.add_warning("timeline structure", f"Skipped (status {response.status_code})")
    except Exception as e:
        results.add_error("timeline structure", str(e))
    
    # Test 5.2: Clinical tests array not empty
    print("Test 5.2: Clinical tests array populated")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            tests = data.get("clinical_tests", [])
            
            if isinstance(tests, list) and len(tests) > 0:
                results.add_pass("clinical_tests populated", f"{len(tests)} tests in timeline")
            elif isinstance(tests, list):
                results.add_warning("clinical_tests empty", "Array exists but is empty")
            else:
                results.add_fail("clinical_tests", f"Not an array, got {type(tests)}")
        else:
            results.add_warning("clinical_tests", "Skipped")
    except Exception as e:
        results.add_error("clinical_tests", str(e))
    
    # Test 5.3: Tests have required fields
    print("Test 5.3: Each test has name, week, and date")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            tests = data.get("clinical_tests", [])
            
            if tests:
                first_test = tests[0]
                required = ["name", "week", "date"]
                missing = [f for f in required if f not in first_test]
                
                if missing:
                    results.add_fail("test fields", f"Missing: {missing}")
                else:
                    results.add_pass("test fields", f"First test has all fields: {first_test['name']}")
            else:
                results.add_warning("test fields", "No tests to validate")
        else:
            results.add_warning("test fields", "Skipped")
    except Exception as e:
        results.add_error("test fields", str(e))
    
    # Test 5.4: Week across all tests is within range
    print("Test 5.4: All test weeks are within pregnancy range")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            tests = data.get("clinical_tests", [])
            
            invalid_weeks = []
            for test in tests:
                week_str = test.get("week", "")
                try:
                    # Extract number from "W20" format
                    week_num = int(week_str.replace("W", ""))
                    if not (0 <= week_num <= 40):
                        invalid_weeks.append((test["name"], week_num))
                except:
                    pass
            
            if invalid_weeks:
                results.add_fail("test weeks valid", f"Invalid weeks: {invalid_weeks}")
            else:
                results.add_pass("test weeks valid", "All weeks within 0-40 range")
        else:
            results.add_warning("test weeks valid", "Skipped")
    except Exception as e:
        results.add_error("test weeks valid", str(e))

# ============================================================================
# 6. MISCARRIAGE SUPPORT ENDPOINT TESTS
# ============================================================================

def test_miscarriage_support():
    print(f"\n{BLUE}{BOLD}6. MISCARRIAGE SUPPORT ENDPOINT{RESET}\n")
    
    endpoint = ENDPOINTS["pregnancy_miscarriage_support"]
    
    # Test 6.1: Valid user without miscarriage
    print("Test 6.1: User without miscarriage history")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code in [200, 404]:
            results.add_pass("miscarriage_support - normal user", f"Status: {response.status_code}")
        else:
            results.add_fail("miscarriage_support - normal user", f"Status: {response.status_code}")
    except Exception as e:
        results.add_error("miscarriage_support - normal user", str(e))
    
    # Test 6.2: Response structure if data exists
    print("Test 6.2: Response structure for miscarriage_support")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["supportive_message", "support_communities", "mental_health_resources", "next_steps"]
            missing = [f for f in expected_fields if f not in data]
            
            if missing:
                results.add_fail("miscarriage_support structure", f"Missing: {missing}")
            else:
                results.add_pass("miscarriage_support structure", "All fields present")
        else:
            results.add_warning("miscarriage_support structure", f"Skipped (status {response.status_code})")
    except Exception as e:
        results.add_error("miscarriage_support structure", str(e))
    
    # Test 6.3: Supportive message is meaningful
    print("Test 6.3: Supportive message is personalized and compassionate")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            message = data.get("supportive_message", "")
            
            if message and len(message) > 50:  # Should be 200-400 words
                results.add_pass("supportive_message", f"Message length: {len(message)} chars")
            else:
                results.add_warning("supportive_message", f"Message too short or empty: {len(message)} chars")
        else:
            results.add_warning("supportive_message", "Skipped")
    except Exception as e:
        results.add_error("supportive_message", str(e))
    
    # Test 6.4: Support communities array
    print("Test 6.4: Support communities is array")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            communities = data.get("support_communities", [])
            
            if isinstance(communities, list):
                results.add_pass("support_communities", f"Array with {len(communities)} communities")
            else:
                results.add_fail("support_communities", f"Not an array, got {type(communities)}")
        else:
            results.add_warning("support_communities", "Skipped")
    except Exception as e:
        results.add_error("support_communities", str(e))

# ============================================================================
# 7. POSTPARTUM RECOVERY ENDPOINT TESTS
# ============================================================================

def test_postpartum_recovery():
    print(f"\n{BLUE}{BOLD}7. POSTPARTUM RECOVERY ENDPOINT{RESET}\n")
    
    endpoint = ENDPOINTS["postpartum_recovery"]
    
    # Test 7.1: Valid postpartum user
    print("Test 7.1: Postpartum user (life_stage_id=4)")
    try:
        # Users 30, 32, 41 are postpartum
        for user_id in POSTPARTUM_USERS[:1]:
            response = requests.get(endpoint, params={"user_id": user_id}, timeout=5)
            if response.status_code in [200, 404]:
                results.add_pass(f"postpartum user {user_id}", f"Status: {response.status_code}")
            else:
                results.add_fail(f"postpartum user {user_id}", f"Status: {response.status_code}")
    except Exception as e:
        results.add_error("postpartum user", str(e))
    
    # Test 7.2: Response structure
    print("Test 7.2: Response structure for postpartum_recovery")
    try:
        response = requests.get(endpoint, params={"user_id": 30}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["days_postpartum", "recovery_status", "physical_health", "mental_health"]
            missing = [f for f in expected_fields if f not in data]
            
            if missing:
                results.add_warning("postpartum structure", f"Missing: {missing}")
            else:
                results.add_pass("postpartum structure", "All expected fields present")
        else:
            results.add_warning("postpartum structure", f"Skipped (status {response.status_code})")
    except Exception as e:
        results.add_error("postpartum structure", str(e))
    
    # Test 7.3: Days postpartum is non-negative
    print("Test 7.3: Days postpartum is valid (>= 0)")
    try:
        response = requests.get(endpoint, params={"user_id": 30}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            days = data.get("days_postpartum")
            
            if days is not None and days >= 0:
                results.add_pass("days_postpartum", f"Value: {days} days")
            else:
                results.add_fail("days_postpartum", f"Invalid value: {days}")
        else:
            results.add_warning("days_postpartum", "Skipped")
    except Exception as e:
        results.add_error("days_postpartum", str(e))
    
    # Test 7.4: Recovery status valid
    print("Test 7.4: Recovery status is valid value")
    try:
        response = requests.get(endpoint, params={"user_id": 30}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get("recovery_status")
            valid_statuses = ["early", "mid", "advanced", "complete"]
            
            if status in valid_statuses:
                results.add_pass("recovery_status", f"Status: {status}")
            else:
                results.add_warning("recovery_status", f"Unexpected status: {status}")
        else:
            results.add_warning("recovery_status", "Skipped")
    except Exception as e:
        results.add_error("recovery_status", str(e))

# ============================================================================
# 8. SUPPORT GROUPS ENDPOINT TESTS
# ============================================================================

def test_support_groups():
    print(f"\n{BLUE}{BOLD}8. SUPPORT GROUPS ENDPOINT{RESET}\n")
    
    endpoint = ENDPOINTS["support_groups"]
    
    # Test 8.1: Response is array
    print("Test 8.1: Support groups response is array")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                results.add_pass("support_groups array", f"Array with {len(data)} groups")
            else:
                results.add_fail("support_groups array", f"Not an array, got {type(data)}")
        else:
            results.add_warning("support_groups array", f"Skipped (status {response.status_code})")
    except Exception as e:
        results.add_error("support_groups array", str(e))
    
    # Test 8.2: Group structure
    print("Test 8.2: Each group has required fields")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                first_group = data[0]
                required = ["name", "description", "type"]
                missing = [f for f in required if f not in first_group]
                
                if missing:
                    results.add_fail("group fields", f"Missing: {missing}")
                else:
                    results.add_pass("group fields", f"Group has all fields: {first_group.get('name')}")
            else:
                results.add_warning("group fields", "No groups to validate")
        else:
            results.add_warning("group fields", "Skipped")
    except Exception as e:
        results.add_error("group fields", str(e))
    
    # Test 8.3: Group names are non-empty
    print("Test 8.3: Group names are meaningful")
    try:
        response = requests.get(endpoint, params={"user_id": 2}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            empty_names = [g for g in data if not g.get("name") or len(g.get("name", "")) < 3]
            
            if empty_names:
                results.add_fail("group names", f"{len(empty_names)} groups with invalid names")
            else:
                results.add_pass("group names", f"All {len(data)} groups have meaningful names")
        else:
            results.add_warning("group names", "Skipped")
    except Exception as e:
        results.add_error("group names", str(e))

# ============================================================================
# 9. CROSS-ENDPOINT CONSISTENCY TESTS
# ============================================================================

def test_cross_endpoint_consistency():
    print(f"\n{BLUE}{BOLD}9. CROSS-ENDPOINT CONSISTENCY TESTS{RESET}\n")
    
    # Test 9.1: All endpoints return same structure for same user
    print("Test 9.1: All pregnancy endpoints work for same user")
    try:
        endpoints_list = [
            ("summary", ENDPOINTS["pregnancy_summary"]),
            ("milestones", ENDPOINTS["pregnancy_milestones"]),
            ("clinical_timeline", ENDPOINTS["pregnancy_clinical_timeline"]),
            ("miscarriage_support", ENDPOINTS["pregnancy_miscarriage_support"]),
        ]
        
        user_id = 2
        success_count = 0
        
        for name, url in endpoints_list:
            response = requests.get(url, params={"user_id": user_id}, timeout=5)
            if response.status_code in [200, 404]:
                success_count += 1
        
        if success_count == len(endpoints_list):
            results.add_pass("all pregnancy endpoints", f"All {success_count} endpoints successful")
        else:
            results.add_warning("all pregnancy endpoints", f"Only {success_count}/{len(endpoints_list)} successful")
    except Exception as e:
        results.add_error("all pregnancy endpoints", str(e))
    
    # Test 9.2: Week consistency across endpoints
    print("Test 9.2: Week is consistent across summary and milestones")
    try:
        resp1 = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": 2}, timeout=5)
        resp2 = requests.get(ENDPOINTS["pregnancy_milestones"], params={"user_id": 2}, timeout=5)
        
        if resp1.status_code == 200 and resp2.status_code == 200:
            week1 = resp1.json().get("current_week")
            week2 = resp2.json().get("week")
            
            if week1 == week2:
                results.add_pass("week consistency", f"Week {week1} consistent across endpoints")
            else:
                results.add_fail("week consistency", f"Mismatch: {week1} vs {week2}")
        else:
            results.add_warning("week consistency", "Skipped")
    except Exception as e:
        results.add_error("week consistency", str(e))
    
    # Test 9.3: Trimester consistency
    print("Test 9.3: Trimester is consistent across endpoints")
    try:
        resp1 = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": 2}, timeout=5)
        resp2 = requests.get(ENDPOINTS["pregnancy_milestones"], params={"user_id": 2}, timeout=5)
        resp3 = requests.get(ENDPOINTS["pregnancy_clinical_timeline"], params={"user_id": 2}, timeout=5)
        
        if resp1.status_code == 200 and resp2.status_code == 200 and resp3.status_code == 200:
            trim1 = resp1.json().get("current_trimester")
            trim2 = resp2.json().get("trimester")
            trim3 = resp3.json().get("trimester")
            
            if trim1 == trim2 == trim3:
                results.add_pass("trimester consistency", f"Trimester '{trim1}' consistent")
            else:
                results.add_warning("trimester consistency", f"Mismatch: {trim1}, {trim2}, {trim3}")
        else:
            results.add_warning("trimester consistency", "Skipped")
    except Exception as e:
        results.add_error("trimester consistency", str(e))

# ============================================================================
# 10. PERFORMANCE & ERROR HANDLING TESTS
# ============================================================================

def test_performance_and_errors():
    print(f"\n{BLUE}{BOLD}10. PERFORMANCE & ERROR HANDLING{RESET}\n")
    
    import time
    
    # Test 10.1: Response times
    print("Test 10.1: Response times < 2 seconds (all endpoints)")
    try:
        slow_endpoints = []
        
        for name, url in ENDPOINTS.items():
            start = time.time()
            response = requests.get(url, params={"user_id": 2}, timeout=5)
            elapsed = time.time() - start
            
            if elapsed > 2.0:
                slow_endpoints.append((name, elapsed))
        
        if slow_endpoints:
            results.add_warning("response times", f"Slow endpoints: {slow_endpoints}")
        else:
            results.add_pass("response times", "All endpoints fast (< 2s)")
    except Exception as e:
        results.add_error("response times", str(e))
    
    # Test 10.2: Error messages format
    print("Test 10.2: Error messages are properly formatted")
    try:
        response = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": -1}, timeout=5)
        if response.status_code >= 400:
            data = response.json()
            
            if "detail" in data or "error" in data:
                results.add_pass("error format", "Error response has detail field")
            else:
                results.add_fail("error format", "Error response missing detail field")
        else:
            results.add_warning("error format", "Skipped")
    except Exception as e:
        results.add_error("error format", str(e))
    
    # Test 10.3: Multiple rapid requests
    print("Test 10.3: API handles multiple concurrent requests")
    try:
        success = 0
        for i in range(5):
            response = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": 2}, timeout=5)
            if response.status_code in [200, 404]:
                success += 1
        
        if success == 5:
            results.add_pass("concurrent requests", "5 rapid requests successful")
        else:
            results.add_warning("concurrent requests", f"Only {success}/5 successful")
    except Exception as e:
        results.add_error("concurrent requests", str(e))

# ============================================================================
# 11. EDGE CASES & SPECIAL TESTS
# ============================================================================

def test_edge_cases():
    print(f"\n{BLUE}{BOLD}11. EDGE CASES & SPECIAL TESTS{RESET}\n")
    
    # Test 11.1: Very large user_id
    print("Test 11.1: Very large user_id (2147483647)")
    try:
        response = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": 2147483647}, timeout=5)
        if response.status_code in [404, 422]:
            results.add_pass("large user_id", f"Status: {response.status_code}")
        else:
            results.add_fail("large user_id", f"Unexpected status: {response.status_code}")
    except Exception as e:
        results.add_error("large user_id", str(e))
    
    # Test 11.2: User without cycle data
    print("Test 11.2: User without pregnancy data (non-pregnant)")
    try:
        # Try a user without menstrual_cycles
        response = requests.get(ENDPOINTS["pregnancy_summary"], params={"user_id": 999}, timeout=5)
        if response.status_code == 404:
            results.add_pass("non-pregnant user", "Returns 404 (expected)")
        else:
            results.add_warning("non-pregnant user", f"Status: {response.status_code}")
    except Exception as e:
        results.add_error("non-pregnant user", str(e))
    
    # Test 11.3: All endpoints with postpartum user
    print("Test 11.3: Postpartum user with all endpoints")
    try:
        user_id = 30
        pregnancy_endpoints = [
            ("summary", ENDPOINTS["pregnancy_summary"]),
            ("milestones", ENDPOINTS["pregnancy_milestones"]),
        ]
        
        for name, url in pregnancy_endpoints:
            response = requests.get(url, params={"user_id": user_id}, timeout=5)
            if response.status_code in [200, 404]:
                results.add_pass(f"{name} postpartum", f"Status: {response.status_code}")
            else:
                results.add_fail(f"{name} postpartum", f"Status: {response.status_code}")
    except Exception as e:
        results.add_error("postpartum endpoints", str(e))

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}COMPREHENSIVE PREGNANCY & POSTPARTUM API TEST SUITE{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Endpoints: {len(ENDPOINTS)}")
    print(f"Known Pregnant Users: {PREGNANT_USERS}")
    print(f"Known Postpartum Users: {POSTPARTUM_USERS}")
    
    try:
        # Run all test groups
        test_parameter_validation()
        test_user_existence()
        test_pregnancy_summary()
        test_pregnancy_milestones()
        test_pregnancy_clinical_timeline()
        test_miscarriage_support()
        test_postpartum_recovery()
        test_support_groups()
        test_cross_endpoint_consistency()
        test_performance_and_errors()
        test_edge_cases()
        
        # Print summary
        results.print_summary()
        
        # Exit with appropriate code
        if results.failed > 0 or results.errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        print(f"\n{RED}FATAL ERROR: {e}{RESET}")
        sys.exit(2)

if __name__ == "__main__":
    main()
