#!/usr/bin/env python3
"""Test script for Beauty & Radiance API endpoint."""

import json
import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/beauty-overview"

# Test user ID (from your database - user 2 has skin_scans data)
TEST_USER_ID = 2


def test_beauty_overview():
    """Test the /api/beauty-overview endpoint."""
    
    print("=" * 80)
    print("TESTING: POST /api/beauty-overview")
    print("=" * 80)
    
    # Request payload
    request_body = {
        "user_id": TEST_USER_ID,
        "days": 30,
        "include_correlations": True
    }
    
    print(f"\n📤 REQUEST:")
    print(f"   URL: {ENDPOINT}")
    print(f"   Method: POST")
    print(f"   Body: {json.dumps(request_body, indent=2)}")
    
    try:
        # Make request
        response = requests.post(ENDPOINT, json=request_body, timeout=30)
        
        print(f"\n📥 RESPONSE:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        # Parse response
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!\n")
            print(json.dumps(data, indent=2))
            
            # Validate response structure
            print(f"\n🔍 RESPONSE STRUCTURE VALIDATION:")
            print(f"   ✓ Has 'today': {bool(data.get('today'))}")
            print(f"   ✓ Has 'history': {bool(data.get('history'))}")
            print(f"   ✓ Has 'correlations': {bool(data.get('correlations'))}")
            print(f"   ✓ Has 'ai_insights': {bool(data.get('ai_insights'))}")
            
            # Check ai_insights structure
            if data.get('ai_insights'):
                ai = data['ai_insights']
                print(f"\n📊 AI INSIGHTS STRUCTURE:")
                print(f"   ✓ Has 'overall_assessment': {bool(ai.get('overall_assessment'))}")
                print(f"   ✓ Has 'phase_impact': {bool(ai.get('phase_impact'))}")
                print(f"   ✓ Has 'sleep_correlation': {bool(ai.get('sleep_correlation'))}")
                print(f"   ✓ Has 'key_focus_areas': {bool(ai.get('key_focus_areas'))}")
                print(f"   ✓ Has 'recommendations': {bool(ai.get('recommendations'))}")
                print(f"   ✓ Has 'confidence_score': {bool(ai.get('confidence_score'))}")
            
            return True
        
        else:
            print(f"\n❌ ERROR!")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR")
        print(f"   Could not connect to {BASE_URL}")
        print(f"   Make sure the FastAPI server is running: python main.py")
        return False
    
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT ERROR")
        print(f"   Request took too long")
        return False
    
    except Exception as exc:
        print(f"\n❌ UNEXPECTED ERROR: {exc}")
        return False


def test_without_correlations():
    """Test with correlations disabled."""
    
    print("\n\n" + "=" * 80)
    print("TESTING: POST /api/beauty-overview (without correlations)")
    print("=" * 80)
    
    request_body = {
        "user_id": TEST_USER_ID,
        "days": 30,
        "include_correlations": False
    }
    
    print(f"\n📤 REQUEST:")
    print(f"   URL: {ENDPOINT}")
    print(f"   Body: {json.dumps(request_body, indent=2)}")
    
    try:
        response = requests.post(ENDPOINT, json=request_body, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"   Correlations empty: {len(data.get('correlations', {})) == 0}")
            return True
        else:
            print(f"\n❌ ERROR: {response.text}")
            return False
    
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}")
        return False


def test_invalid_user():
    """Test with invalid user ID."""
    
    print("\n\n" + "=" * 80)
    print("TESTING: POST /api/beauty-overview (invalid user)")
    print("=" * 80)
    
    request_body = {
        "user_id": 99999,  # Non-existent user
        "days": 30,
        "include_correlations": True
    }
    
    print(f"\n📤 REQUEST:")
    print(f"   User ID: 99999 (non-existent)")
    
    try:
        response = requests.post(ENDPOINT, json=request_body, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Should return empty data gracefully
            print(f"\n✅ Gracefully handled - returned empty data")
            print(f"   Today: {data.get('today')}")
            print(f"   History: {data.get('history')}")
            return True
        else:
            print(f"\n❌ Got error (expected): {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}")
        return False


if __name__ == "__main__":
    print("\n🚀 BEAUTY API TEST SUITE\n")
    
    results = []
    
    # Run tests
    results.append(("Basic Test", test_beauty_overview()))
    results.append(("Without Correlations", test_without_correlations()))
    results.append(("Invalid User", test_invalid_user()))
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
