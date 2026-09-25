"""
Mock database data for testing Lifelong Thriving API
Provides realistic test data with DIFFERENT values per user to verify calculations are dynamic
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Any

# ============================================================================
# MOCK DATA - Each user has DIFFERENT data to verify calculations vary
# ============================================================================

MOCK_HEALTH_LOGS = {
    2: [],  # No health logs (fallback scenario)
    9: [
        {
            "log_date": date(2026, 9, 25),
            "mood": "8",
            "energy_level": "High",
            "symptoms": '{"focus": "good", "energy": "high"}',
            "notes": "Feeling great, strong mobility"
        },
        {
            "log_date": date(2026, 9, 24),
            "mood": "7",
            "energy_level": "High",
            "symptoms": '{"focus": "good"}',
            "notes": "Good sleep, alert"
        },
        {
            "log_date": date(2026, 9, 23),
            "mood": "8",
            "energy_level": "Very High",
            "symptoms": '{"energy": "very high"}',
            "notes": "Excellent day"
        },
        {
            "log_date": date(2026, 9, 22),
            "mood": "7",
            "energy_level": "High",
            "symptoms": '{"mood": "positive"}',
            "notes": "Strong"
        },
    ],
    10: [
        {
            "log_date": date(2026, 9, 25),
            "mood": "6",
            "energy_level": "Moderate",
            "symptoms": '{"brain_fog": "mild"}',
            "notes": "Moderate day, some fatigue"
        },
        {
            "log_date": date(2026, 9, 24),
            "mood": "5",
            "energy_level": "Low",
            "symptoms": '{"fatigue": "yes"}',
            "notes": "Tired, exhausted"
        },
        {
            "log_date": date(2026, 9, 23),
            "mood": "6",
            "energy_level": "Moderate",
            "symptoms": '{}',
            "notes": "Okay"
        },
    ],
    19: [
        {
            "log_date": date(2026, 9, 25),
            "mood": "9",
            "energy_level": "Very High",
            "symptoms": '{"energy": "excellent", "focus": "sharp"}',
            "notes": "Best day, thriving"
        },
        {
            "log_date": date(2026, 9, 24),
            "mood": "8",
            "energy_level": "Very High",
            "symptoms": '{"mood": "excellent"}',
            "notes": "Strong"
        },
    ],
}

MOCK_MENSTRUAL_CYCLES = {
    2: [
        {
            "period_start_date": date(2026, 9, 10),
            "cycle_length": 28,
            "current_phase": "luteal"
        },
    ],
    9: [
        {
            "period_start_date": date(2026, 9, 15),
            "cycle_length": 28,
            "current_phase": "follicular"
        },
        {
            "period_start_date": date(2026, 8, 18),
            "cycle_length": 28,
            "current_phase": "complete"
        },
    ],
    10: [
        {
            "period_start_date": date(2026, 9, 20),
            "cycle_length": 30,
            "current_phase": "menstrual"
        },
        {
            "period_start_date": date(2026, 8, 21),
            "cycle_length": 30,
            "current_phase": "complete"
        },
    ],
    19: [
        {
            "period_start_date": date(2026, 9, 8),
            "cycle_length": 26,
            "current_phase": "luteal"
        },
        {
            "period_start_date": date(2026, 8, 13),
            "cycle_length": 26,
            "current_phase": "complete"
        },
    ],
}

MOCK_LAB_REPORTS = {
    2: [],
    9: [
        {
            "test_type": "Metabolic Panel",
            "biomarkers": '{"glucose": 95, "cholesterol": 190}',
            "analysis_status": "complete",
            "created_at": date(2026, 8, 15),
        },
    ],
    10: [
        {
            "test_type": "Thyroid Panel",
            "biomarkers": '{"tsh": 2.1}',
            "analysis_status": "complete",
            "created_at": date(2026, 9, 1),
        },
        {
            "test_type": "Cardiovascular",
            "biomarkers": '{"heart_rate": 68}',
            "analysis_status": "complete",
            "created_at": date(2026, 8, 20),
        },
    ],
    19: [
        {
            "test_type": "Comprehensive Metabolic Panel",
            "biomarkers": '{"glucose": 92, "cholesterol": 160, "triglycerides": 85}',
            "analysis_status": "complete",
            "created_at": date(2026, 7, 15),
        },
    ],
}

MOCK_PROFILES = {
    2: {"activity_level": "sedentary", "life_stage": "perimenopause", "date_of_birth": date(1975, 5, 15)},
    9: {"activity_level": "very_active", "life_stage": "perimenopause", "date_of_birth": date(1972, 3, 20)},
    10: {"activity_level": "moderately_active", "life_stage": "menopause", "date_of_birth": date(1968, 11, 10)},
    19: {"activity_level": "very_active", "life_stage": "perimenopause", "date_of_birth": date(1970, 7, 25)},
}

# Health goals for fitness/wellness milestones
MOCK_HEALTH_GOALS = {
    2: [],  # No goals
    9: [
        {
            "goal_id": 1,
            "user_id": 9,
            "goal_type": "fitness",
            "title": "Started strength training",
            "description": "Build muscle and improve bone density",
            "start_date": date(2026, 6, 1),
            "target_date": date(2026, 12, 31),
            "status": "in_progress",
            "progress": 60,
            "category": "Fitness"
        },
        {
            "goal_id": 2,
            "user_id": 9,
            "goal_type": "nutrition",
            "title": "Diet overhaul — Mediterranean",
            "description": "Switch to Mediterranean diet for heart health",
            "start_date": date(2026, 7, 15),
            "target_date": date(2027, 1, 31),
            "status": "in_progress",
            "progress": 45,
            "category": "Nutrition"
        },
        {
            "goal_id": 3,
            "user_id": 9,
            "goal_type": "cognitive",
            "title": "Cognitive health baseline set",
            "description": "Establish baseline cognitive performance",
            "start_date": date(2026, 5, 20),
            "target_date": date(2026, 12, 31),
            "status": "completed",
            "progress": 100,
            "category": "Cognitive"
        },
    ],
    10: [
        {
            "goal_id": 4,
            "user_id": 10,
            "goal_type": "fitness",
            "title": "Morning walks routine",
            "description": "30-minute walks 5 times per week",
            "start_date": date(2026, 8, 1),
            "target_date": date(2026, 12, 31),
            "status": "in_progress",
            "progress": 35,
            "category": "Fitness"
        },
    ],
    19: [
        {
            "goal_id": 5,
            "user_id": 19,
            "goal_type": "fitness",
            "title": "Yoga practice",
            "description": "3x per week yoga for flexibility",
            "start_date": date(2026, 9, 1),
            "target_date": date(2027, 3, 31),
            "status": "in_progress",
            "progress": 20,
            "category": "Fitness"
        },
    ],
}

# Life journey milestones (life stage transitions)
MOCK_LIFE_JOURNEYS = {
    2: [],
    9: [
        {
            "journey_id": 1,
            "user_id": 9,
            "journey_type": "perimenopause_onset",
            "title": "Perimenopause onset tracked",
            "milestone_date": date(2026, 8, 15),
            "description": "Started tracking perimenopause symptoms",
            "status": "active",
            "details": {"symptoms_tracked": True, "doctor_consultation": True},
            "category": "Health"
        },
        {
            "journey_id": 2,
            "user_id": 9,
            "journey_type": "wellness_achievement",
            "title": "Vitality Index peaked at 82",
            "milestone_date": date(2026, 9, 20),
            "description": "Achieved personal best wellness score",
            "status": "completed",
            "details": {"previous_best": 79, "improvement": 3},
            "category": "Wellness"
        },
    ],
    10: [
        {
            "journey_id": 3,
            "user_id": 10,
            "journey_type": "postmenopause_transition",
            "title": "Postmenopause transition confirmed",
            "milestone_date": date(2026, 6, 10),
            "description": "Officially entered postmenopause phase",
            "status": "completed",
            "details": {"months_without_cycle": 12, "symptoms_managed": True},
            "category": "Health"
        },
        {
            "journey_id": 4,
            "user_id": 10,
            "journey_type": "screening_milestone",
            "title": "First bone density scan",
            "milestone_date": date(2026, 7, 12),
            "description": "Completed first bone density screening",
            "status": "completed",
            "details": {"result": "normal", "next_scan": "2028-07-12"},
            "category": "Screening"
        },
        {
            "journey_id": 5,
            "user_id": 10,
            "journey_type": "health_milestone",
            "title": "Sleep apnea diagnosis & treatment",
            "milestone_date": date(2026, 6, 5),
            "description": "Diagnosed and started treatment for sleep apnea",
            "status": "in_progress",
            "details": {"treatment_type": "CPAP", "compliance": "good"},
            "category": "Health"
        },
    ],
    19: [
        {
            "journey_id": 6,
            "user_id": 19,
            "journey_type": "wellness_achievement",
            "title": "Achieved thriving wellness level",
            "milestone_date": date(2026, 9, 10),
            "description": "Achieved thriving wellness status - best vitality level",
            "status": "completed",
            "details": {"vitality_score": 86.0, "achievement_type": "wellness_peak"},
            "category": "Wellness"
        },
    ],
}

# ============================================================================
# MOCK QUERY FUNCTIONS
# ============================================================================

def mock_query_db(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Mock query_db that returns test data based on query and params.
    Simulates database queries without needing AWS RDS connection.
    """
    
    if not params:
        params = ()
    
    user_id = params[0] if params else None
    
    # Parse query to determine which table
    query_lower = query.lower()
    
    if "health_logs" in query_lower:
        return MOCK_HEALTH_LOGS.get(user_id, [])
    
    elif "menstrual_cycles" in query_lower:
        return MOCK_MENSTRUAL_CYCLES.get(user_id, [])
    
    elif "lab_reports" in query_lower:
        return MOCK_LAB_REPORTS.get(user_id, [])
    
    elif "health_goals" in query_lower:
        return MOCK_HEALTH_GOALS.get(user_id, [])
    
    elif "life_journeys" in query_lower or "life_journey" in query_lower:
        return MOCK_LIFE_JOURNEYS.get(user_id, [])
    
    elif "profiles" in query_lower:
        profile = MOCK_PROFILES.get(user_id, {})
        return [profile] if profile else []
    
    elif "health_trends" in query_lower:
        return []  # No health trends in mock data
    
    return []


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================
"""
To use mock data instead of real database:

1. In ai/services/lifelong_thriving_service.py, replace:
    from ai.utils.db import query_db
   
   With:
    from ai.utils.mock_data import mock_query_db as query_db

2. All subsequent query_db() calls will use mock data

3. Mock data provides DIFFERENT values for each user:
   - User 2: No health data (tests fallback)
   - User 9: High energy/mood (high vitality scores)
   - User 10: Low energy/mood (low vitality scores)
   - User 19: Very high energy/mood (very high vitality scores)

4. This allows verifying that API calculations are DYNAMIC, not hardcoded
"""
