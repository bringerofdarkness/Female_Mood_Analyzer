"""Test suite for Cycle & Fertility endpoint."""

import logging
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8002/api"

# Test user with sample data
TEST_USER_ID = 2

# Test payloads
CYCLE_STANDARD_REQUEST = {
    "user_id": TEST_USER_ID,
    "mode": "standard",
    "include_bbt": False
}

CYCLE_TRACKING_REQUEST = {
    "user_id": TEST_USER_ID,
    "mode": "tracking",
    "include_bbt": True
}

CYCLE_PREMIUM_REQUEST = {
    "user_id": TEST_USER_ID,
    "mode": "premium",
    "include_bbt": True
}

CYCLE_INVALID_USER = {
    "user_id": 99999,
    "mode": "standard",
    "include_bbt": False
}


def test_cycle_standard_mode():
    """Test cycle overview in standard mode."""
    logger.info("Testing Cycle Overview - Standard Mode...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cycle-overview",
            json=CYCLE_STANDARD_REQUEST,
            timeout=30
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✓ Standard mode successful")
            logger.info(f"  Current Phase: {data.get('current_metrics', {}).get('current_phase')}")
            logger.info(f"  Cycle Day: {data.get('current_metrics', {}).get('current_cycle_day')}")
            logger.info(f"  Fertile Now: {data.get('fertile_window', {}).get('is_fertile_now')}")
            logger.info(f"  BBT Analysis: {data.get('bbt_analysis') is not None}")
            return True
        else:
            logger.error(f"✗ Failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Exception: {e}")
        return False


def test_cycle_tracking_mode():
    """Test cycle overview in tracking mode with BBT."""
    logger.info("\nTesting Cycle Overview - Tracking Mode with BBT...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cycle-overview",
            json=CYCLE_TRACKING_REQUEST,
            timeout=30
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✓ Tracking mode successful")
            logger.info(f"  Cycle History Count: {data.get('cycle_history', {}).get('previous_cycles_count')}")
            logger.info(f"  Avg Cycle Length: {data.get('cycle_history', {}).get('avg_cycle_length')}")
            logger.info(f"  Regularity Score: {data.get('cycle_history', {}).get('cycle_regularity_score')}")
            
            bbt = data.get('bbt_analysis')
            if bbt:
                logger.info(f"  BBT Entries: {bbt.get('temperature_entries')}")
                logger.info(f"  Temp Shift Detected: {bbt.get('temp_rise_detected')}")
            else:
                logger.info("  No BBT data available for this user")
            
            return True
        else:
            logger.error(f"✗ Failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Exception: {e}")
        return False


def test_cycle_premium_mode():
    """Test cycle overview in premium mode."""
    logger.info("\nTesting Cycle Overview - Premium Mode...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cycle-overview",
            json=CYCLE_PREMIUM_REQUEST,
            timeout=30
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✓ Premium mode successful")
            
            insights = data.get('ai_insights', {})
            logger.info(f"  Cycle Assessment: {insights.get('cycle_assessment', 'N/A')[:50]}...")
            logger.info(f"  Optimal Timing: {insights.get('optimal_timing', 'N/A')[:50]}...")
            logger.info(f"  Recommendations: {len(insights.get('recommendations', []))} items")
            logger.info(f"  Confidence Score: {insights.get('confidence_score')}%")
            
            return True
        else:
            logger.error(f"✗ Failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Exception: {e}")
        return False


def test_cycle_invalid_user():
    """Test cycle overview with invalid user ID."""
    logger.info("\nTesting Cycle Overview - Invalid User...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cycle-overview",
            json=CYCLE_INVALID_USER,
            timeout=30
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 404:
            logger.info("✓ Correctly returned 404 for invalid user")
            return True
        else:
            logger.error(f"✗ Expected 404, got {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Exception: {e}")
        return False


def test_cycle_response_structure():
    """Test that response structure matches expected schema."""
    logger.info("\nTesting Cycle Response Structure...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cycle-overview",
            json=CYCLE_STANDARD_REQUEST,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"✗ Request failed: {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify structure
        required_fields = [
            'current_metrics',
            'fertile_window',
            'cycle_history',
            'ai_insights'
        ]
        
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            logger.error(f"✗ Missing fields: {missing}")
            return False
        
        # Check nested structure
        metrics = data.get('current_metrics', {})
        required_metrics = [
            'current_cycle_day',
            'cycle_length',
            'current_phase',
            'predicted_ovulation_day'
        ]
        
        missing_metrics = [f for f in required_metrics if f not in metrics]
        
        if missing_metrics:
            logger.error(f"✗ Missing metric fields: {missing_metrics}")
            return False
        
        # Check fertile window
        fertile = data.get('fertile_window', {})
        required_fertile = [
            'fertile_start_day',
            'fertile_end_day',
            'ovulation_probability',
            'is_fertile_now'
        ]
        
        missing_fertile = [f for f in required_fertile if f not in fertile]
        
        if missing_fertile:
            logger.error(f"✗ Missing fertile window fields: {missing_fertile}")
            return False
        
        logger.info("✓ Response structure is valid")
        return True
    
    except Exception as e:
        logger.error(f"✗ Exception: {e}")
        return False


def run_all_tests():
    """Run all cycle endpoint tests."""
    logger.info("=" * 60)
    logger.info("CYCLE & FERTILITY ENDPOINT TEST SUITE")
    logger.info("=" * 60)
    
    results = {
        "standard_mode": test_cycle_standard_mode(),
        "tracking_mode": test_cycle_tracking_mode(),
        "premium_mode": test_cycle_premium_mode(),
        "invalid_user": test_cycle_invalid_user(),
        "response_structure": test_cycle_response_structure(),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
