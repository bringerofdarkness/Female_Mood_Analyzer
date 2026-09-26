"""Pregnancy & Postpartum API routes."""

from fastapi import APIRouter, Query
from ai.services.pregnancy_service import (
    pregnancy_summary,
    pregnancy_milestones,
    pregnancy_clinical_timeline,
    postpartum_recovery,
    support_groups,
    miscarriage_support
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
    user_id: int = Query(..., ge=1, description="User ID")
):
    """
    **Pregnancy Milestones by Current Week**
    
    Get detailed pregnancy milestones for the user's current pregnancy week including:
    - Baby development
    - Body changes and symptoms
    - Nutrition recommendations
    - Safe exercises
    - Clinical monitoring needed
    
    **Parameters:**
    - `user_id` (int, required): User identifier
    
    **Week Source:**
    Automatically calculates from user's menstrual cycle data (period_start_date).
    
    **Response includes:**
    - Baby size, weight, and development features
    - Physical changes and symptoms
    - Macro nutrients and food groups
    - Safe and unsafe exercises
    - Recommended screenings and tests
    
    **Example:**
    ```
    GET /api/v1/pregnancy/milestones?user_id=6
    ```
    
    **Response (200 OK):**
    ```json
    {
      "week": 36,
      "trimester": "Third",
      "baby_development": "Baby weighs about 5.5 lbs and is ideally in head-down position...",
      "your_body": "Your belly may drop (lightening)...",
      "nutrition_focus": "Easy-to-digest proteins and iron-rich foods...",
      "safe_exercises": "Gentle walking, pelvic floor exercises...",
      "clinical_monitoring": [
        {
          "name": "GBS Swab & Birth Plan",
          "week": "W36",
          "date": "Jan 31"
        }
      ],
      "clinical_warning_signs": "Contact hospital if contractions are regular..."
    }
    ```
    """
    return pregnancy_milestones(user_id)


@router.get("/pregnancy/clinical-timeline")
async def get_pregnancy_clinical_timeline(
    user_id: int = Query(..., ge=1, description="User ID")
):
    """
    **Clinical Tests Timeline - Figma UI View**
    
    Get all clinical tests scheduled across entire pregnancy with dates.
    Perfect for displaying a timeline view in UI showing all upcoming and past tests.
    
    **Parameters:**
    - `user_id` (int, required): User identifier
    
    **Week Source:**
    Automatically calculates from user's menstrual cycle data (period_start_date).
    
    **Response includes:**
    - Current week and trimester
    - All clinical tests from all weeks with dates
    - Warning signs for current week
    
    **Example:**
    ```
    GET /api/v1/pregnancy/clinical-timeline?user_id=6
    ```
    
    **Response (200 OK):**
    ```json
    {
      "week": 24,
      "trimester": "Second",
      "clinical_tests": [
        {
          "name": "Anatomy Scan",
          "week": "W20",
          "date": "Oct 2"
        },
        {
          "name": "Glucose Tolerance Test",
          "week": "W24",
          "date": "Nov 8 (Today)"
        },
        {
          "name": "Anti-D Injection",
          "week": "W28",
          "date": "Dec 6"
        },
        {
          "name": "Growth Scan",
          "week": "W32",
          "date": "Jan 3"
        },
        {
          "name": "GBS Swab + Birth Plan",
          "week": "W36",
          "date": "Jan 31"
        }
      ],
      "clinical_warning_signs": "Seek immediate care for..."
    }
    ```
    """
    return pregnancy_clinical_timeline(user_id)


@router.get("/pregnancy/miscarriage-support")
async def get_miscarriage_support(
    user_id: int = Query(..., ge=1, description="User ID")
):
    """
    **Miscarriage Support & Mental Health Resources**
    
    Detects pregnancy loss and provides comprehensive mental health support, 
    counseling resources, and community support groups for users experiencing miscarriage.
    
    **Parameters:**
    - `user_id` (int, required): User identifier
    
    **Detection:**
    Automatically checks health logs for miscarriage indicators:
    - Keywords: "miscarriage", "pregnancy loss", "heavy bleeding", "severe cramping", etc.
    
    **Response includes (if miscarriage detected):**
    - Miscarriage detection date
    - Immediate crisis support hotlines
    - Mental health resources and counseling options
    - Support communities for pregnancy loss
    - Physical recovery guidelines
    - Self-care recommendations
    - Next steps for healing
    
    **Example:**
    ```
    GET /api/v1/pregnancy/miscarriage-support?user_id=6
    ```
    
    **Response (200 OK - If Miscarriage Detected):**
    ```json
    {
      "has_miscarriage": true,
      "miscarriage_detected_date": "2026-09-20",
      "status": "support_needed",
      "message": "We're deeply sorry for your loss...",
      "support_communities": [
        {
          "name": "Miscarriage Support Group",
          "description": "Community support for pregnancy loss",
          "member_count": 245,
          "type": "pregnancy_loss"
        }
      ],
      "mental_health_resources": {
        "immediate_support": {
          "crisis_hotline": "1-800-273-8255 (24/7 Suicide & Crisis Lifeline)",
          "pregnancy_loss_hotline": "1-888-495-2288 (MISSCARRIAGE Support)"
        },
        "professional_help": {
          "grief_counseling": "Specialized counselors for pregnancy loss grief",
          "therapy_options": ["Individual counseling", "Couples counseling", "Support groups"]
        }
      },
      "next_steps": [
        "Allow time for emotional and physical healing",
        "Connect with support communities...",
        "Consider professional grief counseling..."
      ]
    }
    ```
    
    **Response (200 OK - If No Miscarriage):**
    ```json
    {
      "has_miscarriage": false,
      "message": "No miscarriage detected..."
    }
    ```
    """
    return miscarriage_support(user_id)


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
