#!/usr/bin/env python
"""
Simple API Response Validation - No emoji issues
"""

import requests
import json

BASE_URL = "http://localhost:8002"

def test_athlete():
    print("\n" + "="*80)
    print("TEST: ATHLETE PERFORMANCE API")
    print("="*80)
    try:
        url = f"{BASE_URL}/api/v1/athlete/readiness?user_id=2"
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Readiness Score: {data.get('readiness_score')}")
            print(f"✓ Readiness Level: {data.get('readiness_level')}")
            print(f"✓ Recovery: {data.get('recovery')}")
            print(f"✓ Alerts: {len(data.get('fatigue_alerts', []))} alerts")
            return True
        else:
            print(f"✗ Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_beauty():
    print("\n" + "="*80)
    print("TEST: BEAUTY API (POST)")
    print("="*80)
    try:
        url = f"{BASE_URL}/api/beauty-overview"
        payload = {"user_id": 2, "days": 30, "include_correlations": True}
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Overall Assessment: {str(data.get('overall_assessment'))[:80]}")
            print(f"✓ Findings: {len(data.get('findings', {}).get('items', []))} items")
            print(f"✓ Recommendations: {len(data.get('recommendations', []))} items")
            return True
        else:
            print(f"✗ Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_cycle():
    print("\n" + "="*80)
    print("TEST: CYCLE AWARENESS API")
    print("="*80)
    try:
        url = f"{BASE_URL}/api/cycle-awareness?user_id=2"
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Cycle Phase: {data.get('current_phase')}")
            print(f"✓ Cycle Day: {data.get('cycle_day')}")
            print(f"✓ AI Insights: {len(str(data.get('ai_insights', ''))) } chars")
            return True
        else:
            print(f"✗ Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_multi_user_athlete():
    print("\n" + "="*80)
    print("TEST: MULTI-USER ATHLETE API")
    print("="*80)
    users = [2, 10, 16, 33]
    results = []
    for user_id in users:
        try:
            url = f"{BASE_URL}/api/v1/athlete/readiness?user_id={user_id}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                score = data.get('readiness_score')
                results.append((user_id, score, True))
                print(f"✓ User {user_id}: Score {score}")
            else:
                results.append((user_id, None, False))
                print(f"✗ User {user_id}: Status {response.status_code}")
        except Exception as e:
            results.append((user_id, None, False))
            print(f"✗ User {user_id}: {e}")
    return all(r[2] for r in results)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPREHENSIVE API RESPONSE VALIDATION")
    print("="*80)
    
    results = {
        "Athlete API": test_athlete(),
        "Beauty API": test_beauty(),
        "Cycle API": test_cycle(),
        "Multi-User": test_multi_user_athlete(),
    }
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    pass_count = sum(1 for r in results.values() if r)
    print(f"\nTotal: {pass_count}/{len(results)} passed")
