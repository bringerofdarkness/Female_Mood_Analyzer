"""Pregnancy & Postpartum API routes."""

from fastapi import APIRouter, Query
from ai.services.pregnancy_service import (
    pregnancy_summary,
    pregnancy_milestones,
    postpartum_recovery,
    support_groups
)

router = APIRouter()


@router.get("/pregnancy/summary")
async def get_pregnancy_summary(user_id: int = Query(..., ge=1, description="User ID")):
    """
    **Pregnancy Summary & Status**
    
    Get current pregnancy status, week, trimester, and relevant alerts.
    
    **Parameters:**
    - `user_id` (int, required): User identifier
    
    **Response includes:**
    - Current pregnancy week (0-40)
    - Current trimester (First/Second/Third)
    - Due date calculation
    - Days until due
    - Health status
    - Pregnancy alerts
    
    **Example:**
    ```
    GET /api/v1/pregnancy/summary?user_id=2
    ```
    
    **Response (200 OK):**
    ```json
    {
      "is_pregnant": true,
      "current_week": 24,
      "current_trimester": "Second",
      "due_date": "2026-12-20",
      "days_until_due": 88,
      "health_status": "good",
      "alerts": [...]
    }
    ```
    """
    return pregnancy_summary(user_id)


@router.get("/pregnancy/milestones")
async def get_pregnancy_milestones(
    user_id: int = Query(..., ge=1, description="User ID"),
    week: int = Query(None, ge=0, le=40, description="Specific pregnancy week (0-40, optional)")
):
    """
    **Pregnancy Milestones by Week**
    
    Get detailed pregnancy milestones for a specific week including:
    - Baby development
    - Body changes and symptoms
    - Nutrition recommendations
    - Safe exercises
    - Clinical monitoring needed
    
    **Parameters:**
    - `user_id` (int, required): User identifier
    - `week` (int, optional): Specific week (0-40). If omitted, uses current week.
    
    **Response includes:**
    - Baby size, weight, and development features
    - Physical changes and symptoms
    - Macro nutrients and food groups
    - Safe and unsafe exercises
    - Recommended screenings and tests
    
    **Example:**
    ```
    GET /api/v1/pregnancy/milestones?user_id=2&week=24
    ```
    
    **Response (200 OK):**
    ```json
    {
      "week": 24,
      "trimester": "Second",
      "baby_development": {
        "size": "Corn on the cob",
        "weight": "1.3 lbs",
        "features": ["Lungs producing surfactant", ...]
      },
      "your_body": {...},
      "nutrition_focus": {...},
      "safe_exercises": {...},
      "clinical_monitoring": {...}
    }
    ```
    """
    return pregnancy_milestones(user_id, week)


@router.get("/postpartum/recovery")
async def get_postpartum_recovery(user_id: int = Query(..., ge=1, description="User ID")):
    """
    **Postpartum Recovery Status**
    
    Get comprehensive postpartum recovery overview including:
    - Physical recovery metrics
    - Mental health assessment
    - Activity level recommendations
    - Sleep quality
    - Postpartum alerts
    
    **Parameters:**
    - `user_id` (int, required): User identifier
    
    **Response includes:**
    - Postpartum week (0-12)
    - Delivery method
    - Recovery metrics (physical recovery %, bleeding level, pelvic floor status)
    - Mental health (mood stability, anxiety, depression screening)
    - Activity level
    - Sleep hours
    - Postpartum alerts
    
    **Example:**
    ```
    GET /api/v1/postpartum/recovery?user_id=2
    ```
    
    **Response (200 OK):**
    ```json
    {
      "postpartum_week": 6,
      "delivery_method": "vaginal",
      "recovery_metrics": {
        "physical_recovery_percent": 72,
        "bleeding_level": "light",
        "pelvic_floor_status": "healing"
      },
      "mental_health": {
        "mood_stability": 65,
        "anxiety_level": 3,
        "depression_screening": "low_risk"
      },
      "activity_level": "moderate",
      "sleep_hours": 4.5,
      "postpartum_alerts": [...]
    }
    ```
    """
    return postpartum_recovery(user_id)


@router.get("/community/support-groups")
async def get_support_groups(
    life_stage: str = Query(..., description="pregnancy or postpartum"),
    limit: int = Query(10, ge=1, le=50, description="Max groups to return")
):
    """
    **Support Communities & Groups**
    
    Get available support communities for pregnancy or postpartum.
    
    **Parameters:**
    - `life_stage` (string, required): "pregnancy" or "postpartum"
    - `limit` (int, optional): Maximum groups to return (default: 10, max: 50)
    
    **Response includes:**
    - Group ID, name, description
    - Member count
    - Active users today
    - Latest posts count
    - Whether professionally moderated
    - User's join status
    
    **Example:**
    ```
    GET /api/v1/community/support-groups?life_stage=postpartum&limit=10
    ```
    
    **Response (200 OK):**
    ```json
    {
      "groups": [
        {
          "id": 1,
          "name": "Postpartum Support Group",
          "description": "Safe space for postpartum journeys",
          "life_stage": "postpartum",
          "member_count": 347,
          "active_users_today": 23,
          "latest_posts_count": 5,
          "is_moderated": true,
          "join_status": "joined"
        },
        ...
      ],
      "total_groups": 8,
      "user_joined_count": 1
    }
    ```
    """
    return support_groups(life_stage, limit)
