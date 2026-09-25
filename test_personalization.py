"""
Test script to verify whether AI-generated insights are personalized or hardcoded
Calls the same endpoints for different users and compares responses
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

# Test users
TEST_USERS = [1, 2, 3, 4, 5]

print("=" * 80)
print("PERSONALIZATION TEST - Checking if AI insights are user-specific")
print("=" * 80)

# Test 1: Athlete API
print("\n\n[TEST 1] ATHLETE READINESS API - /api/v1/athlete/readiness")
print("-" * 80)

athlete_responses = {}
for user_id in TEST_USERS:
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/athlete/readiness",
            params={"user_id": user_id},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            athlete_responses[user_id] = data
            print(f"\n✅ User {user_id}: Status {response.status_code}")
            print(f"   Readiness Score: {data.get('readiness_score')}")
            print(f"   Readiness Level: {data.get('readiness_level')}")
            print(f"   HRV Value: {data.get('hrv', {}).get('value')} ms")
            print(f"   Sleep: {data.get('metrics', {}).get('sleep', {}).get('percentage')}%")
            
            # Show first alert message (should be personalized)
            alerts = data.get('fatigue_alerts', [])
            if alerts:
                print(f"   Alert 1: {alerts[0].get('message')[:80]}...")
        else:
            print(f"\n❌ User {user_id}: Status {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"\n❌ User {user_id}: {str(e)}")

# Compare Alert Messages
print("\n\n" + "=" * 80)
print("ALERT MESSAGE COMPARISON - Are they personalized?")
print("=" * 80)

print("\nFirst Alert (Overtraining Risk):")
for user_id, data in athlete_responses.items():
    alerts = data.get('fatigue_alerts', [])
    if alerts:
        msg = alerts[0].get('message', '')[:100]
        print(f"  User {user_id}: {msg}")

print("\nSecond Alert (Injury Risk):")
for user_id, data in athlete_responses.items():
    alerts = data.get('fatigue_alerts', [])
    if len(alerts) > 1:
        msg = alerts[1].get('message', '')[:100]
        print(f"  User {user_id}: {msg}")

print("\nThird Alert (Cumulative Fatigue):")
for user_id, data in athlete_responses.items():
    alerts = data.get('fatigue_alerts', [])
    if len(alerts) > 2:
        msg = alerts[2].get('message', '')[:100]
        print(f"  User {user_id}: {msg}")

# Test 2: Beauty API
print("\n\n[TEST 2] BEAUTY API - /api/beauty-overview")
print("-" * 80)

beauty_responses = {}
for user_id in TEST_USERS:
    try:
        response = requests.post(
            f"{BASE_URL}/api/beauty-overview",
            json={"user_id": user_id},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            beauty_responses[user_id] = data
            print(f"\n✅ User {user_id}: Status {response.status_code}")
            
            today = data.get('today', {})
            print(f"   Overall Score: {today.get('overall_score')}")
            print(f"   Hydration: {today.get('hydration_score')}")
            print(f"   Glow Index: {today.get('glow_index')}")
            
            # Show AI insight (should be personalized)
            ai_insights = data.get('ai_insights', {})
            if ai_insights:
                assessment = ai_insights.get('overall_assessment', '')[:80]
                print(f"   Assessment: {assessment}...")
        else:
            print(f"\n❌ User {user_id}: Status {response.status_code}")
    except Exception as e:
        print(f"\n❌ User {user_id}: {str(e)}")

# Compare AI Insights
print("\n\n" + "=" * 80)
print("BEAUTY AI INSIGHTS COMPARISON - Are they personalized?")
print("=" * 80)

print("\nOverall Assessment:")
for user_id, data in beauty_responses.items():
    ai_insights = data.get('ai_insights', {})
    if ai_insights:
        msg = ai_insights.get('overall_assessment', '')[:100]
        print(f"  User {user_id}: {msg}")

print("\nPhase Impact:")
for user_id, data in beauty_responses.items():
    ai_insights = data.get('ai_insights', {})
    if ai_insights:
        msg = ai_insights.get('phase_impact', '')[:100]
        print(f"  User {user_id}: {msg}")

# ANALYSIS
print("\n\n" + "=" * 80)
print("ANALYSIS RESULTS")
print("=" * 80)

# Check if athlete alerts are identical
print("\n[ATHLETE API] Alert Uniqueness:")
athlete_alerts = {}
for user_id, data in athlete_responses.items():
    alerts = data.get('fatigue_alerts', [])
    if alerts:
        athlete_alerts[user_id] = alerts[0]['message']

unique_athlete_alerts = len(set(athlete_alerts.values()))
total_athlete_users = len(athlete_alerts)
print(f"  Total users with data: {total_athlete_users}")
print(f"  Unique alert messages: {unique_athlete_alerts}")
if unique_athlete_alerts == total_athlete_users:
    print(f"  ✅ PERSONALIZED - Each user has different alerts!")
elif unique_athlete_alerts == 1:
    print(f"  ❌ HARDCODED - All users have identical alerts!")
else:
    print(f"  ⚠️  PARTIALLY PERSONALIZED - {unique_athlete_alerts} unique variations")

# Check if beauty insights are identical
print("\n[BEAUTY API] Insight Uniqueness:")
beauty_insights = {}
for user_id, data in beauty_responses.items():
    ai_insights = data.get('ai_insights', {})
    if ai_insights:
        beauty_insights[user_id] = ai_insights.get('overall_assessment', '')

unique_beauty_insights = len(set(beauty_insights.values()))
total_beauty_users = len(beauty_insights)
print(f"  Total users with data: {total_beauty_users}")
print(f"  Unique insights: {unique_beauty_insights}")
if unique_beauty_insights == total_beauty_users:
    print(f"  ✅ PERSONALIZED - Each user has different insights!")
elif unique_beauty_insights == 1:
    print(f"  ❌ HARDCODED - All users have identical insights!")
else:
    print(f"  ⚠️  PARTIALLY PERSONALIZED - {unique_beauty_insights} unique variations")

print("\n" + "=" * 80)
print(f"Test completed at {datetime.now().isoformat()}")
print("=" * 80)
