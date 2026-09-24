"""Pregnancy & Postpartum API service with business logic."""

from datetime import datetime, timedelta, date
from typing import Any, Dict, Optional
from pymysql.cursors import DictCursor

from ai.models.pregnancy_models import (
    PregnancySummary, PregnancyAlert, PregnancyMilestones,
    BabyDevelopment, BodyChanges, NutritionFocus, SafeExercise, ClinicalMonitoring,
    PostpartumRecovery, RecoveryMetrics, MentalHealth, PostpartumAlert,
    SupportGroup, SupportGroupResponse
)


# ============================================================================
# PREGNANCY MILESTONES DATA (Hardcoded by Week)
# ============================================================================

PREGNANCY_MILESTONES_DATA = {
    # Format: week: {baby_dev, body_changes, nutrition, exercises, clinical}
    0: {
        "baby": {"size": "Fertilized egg", "weight": "Microscopic", "features": ["Conception", "Cell division begins"]},
        "body": {"changes": ["None yet", "Implantation"], "symptoms": ["None yet"]},
        "nutrition": {"macros": {"Folic Acid": "400 mcg/day", "Iron": "27 mg/day", "Calcium": "1000 mg/day"}, "foods": ["Leafy greens", "Fortified cereals", "Dairy"], "avoid": ["Raw fish", "Alcohol", "Caffeine (limit)"]},
        "exercises": {"recommended": ["Walking", "Yoga", "Swimming"], "avoid": ["Contact sports"], "intensity": "moderate"},
        "clinical": {"screenings": [], "tests": [], "vitals": ["Baseline blood pressure"]}
    },
    8: {
        "baby": {"size": "Raspberry", "weight": "0.04 oz", "features": ["Heart forming", "Limb buds visible", "Neural tube closing"]},
        "body": {"changes": ["Fatigue", "Breast tenderness", "Nausea possible"], "symptoms": ["Morning sickness", "Food aversions"]},
        "nutrition": {"macros": {"Protein": "70g/day", "Calcium": "1000 mg/day", "Iron": "27 mg/day"}, "foods": ["Eggs", "Nuts", "Yogurt"], "avoid": ["Unpasteurized cheese", "Deli meats", "High mercury fish"]},
        "exercises": {"recommended": ["Walking", "Swimming", "Prenatal yoga"], "avoid": ["High-impact"], "intensity": "moderate"},
        "clinical": {"screenings": ["Confirm pregnancy"], "tests": ["Ultrasound"], "vitals": ["Blood pressure", "Weight"]}
    },
    12: {
        "baby": {"size": "Plum", "weight": "0.5 oz", "features": ["Fingers and toes forming", "Reflexes developing", "External genitalia forming"]},
        "body": {"changes": ["Belly growth begins", "Hormonal changes", "Increased urination"], "symptoms": ["Mood swings", "Fatigue", "Nausea"]},
        "nutrition": {"macros": {"Protein": "70g/day", "Folic Acid": "600 mcg/day", "Iron": "27 mg/day"}, "foods": ["Citrus fruits", "Broccoli", "Red meat"], "avoid": ["Alcohol", "Undercooked meat", "Unpasteurized dairy"]},
        "exercises": {"recommended": ["Walking", "Swimming", "Prenatal yoga", "Pelvic floor exercises"], "avoid": ["Heavy lifting", "Contact sports"], "intensity": "moderate"},
        "clinical": {"screenings": ["First trimester screening"], "tests": ["Nuchal translucency ultrasound", "Blood tests"], "vitals": ["Weight", "Blood pressure", "Urine test"]}
    },
    16: {
        "baby": {"size": "Avocado", "weight": "2.8 oz", "features": ["Facial features more defined", "Ears moving to side of head", "Hair follicles forming"]},
        "body": {"changes": ["Visible belly", "Skin changes", "Weight gain ~3-5 lbs"], "symptoms": ["Reduced nausea", "Increased appetite", "Backaches"]},
        "nutrition": {"macros": {"Protein": "70g/day", "Calcium": "1000 mg/day", "Iron": "27 mg/day"}, "foods": ["Salmon", "Almonds", "Sweet potatoes"], "avoid": ["Caffeine >200mg/day", "Raw sprouts"]},
        "exercises": {"recommended": ["Walking 30min", "Swimming", "Prenatal yoga"], "avoid": ["Lying flat on back >10min"], "intensity": "moderate"},
        "clinical": {"screenings": ["Quad screen (optional)"], "tests": ["Maternal serum alpha-fetoprotein"], "vitals": ["Weight", "Blood pressure"]}
    },
    20: {
        "baby": {"size": "Banana", "weight": "10.2 oz", "features": ["Unique fingerprints forming", "Swallowing and hiccupping", "Hair and eyebrows visible"]},
        "body": {"changes": ["Pronounced belly", "Stretch marks appear", "Weight gain ~10 lbs"], "symptoms": ["Braxton Hicks contractions", "Leg cramps", "Back pain"]},
        "nutrition": {"macros": {"Protein": "70g/day", "Calcium": "1000 mg/day", "Iron": "27 mg/day"}, "foods": ["Legumes", "Whole grains", "Leafy greens"], "avoid": ["Unpasteurized soft cheese", "High mercury fish"]},
        "exercises": {"recommended": ["Walking", "Swimming", "Prenatal yoga", "Pelvic exercises"], "avoid": ["Heavy lifting >25 lbs"], "intensity": "moderate"},
        "clinical": {"screenings": ["Mid-pregnancy ultrasound"], "tests": ["Structural ultrasound"], "vitals": ["Weight", "Glucose screening check"]}
    },
    24: {
        "baby": {"size": "Corn on the cob", "weight": "1.3 lbs", "features": ["Lungs producing surfactant", "Can hear mother's heartbeat", "Beginning to blink"]},
        "body": {"changes": ["Weight gain ~12-18 lbs", "Braxton Hicks contractions", "Back pain common"], "symptoms": ["Swollen ankles", "Heartburn", "Fatigue"]},
        "nutrition": {"macros": {"Iron": "27 mg/day", "Calcium": "1000 mg/day", "Protein": "70g/day"}, "foods": ["Iron-rich: spinach, beef", "Calcium: yogurt, cheese", "Protein: eggs, tofu"], "avoid": ["Limit caffeine", "No alcohol"]},
        "exercises": {"recommended": ["Walking", "Swimming", "Prenatal yoga", "Kegel exercises"], "avoid": ["Excessive steady-state cardio"], "intensity": "moderate"},
        "clinical": {"screenings": ["Glucose tolerance test"], "tests": ["Blood glucose test", "Full blood count"], "vitals": ["Weight", "Blood pressure", "Urine check"]}
    },
    28: {
        "baby": {"size": "Large eggplant", "weight": "2.2 lbs", "features": ["Opening and closing eyes", "Responds to sounds and light", "Sleep-wake cycles"]},
        "body": {"changes": ["Increased swelling", "Darkened skin patches", "Leaky breasts possible"], "symptoms": ["Insomnia", "Leg cramps", "Constipation"]},
        "nutrition": {"macros": {"Iron": "27 mg/day", "Fiber": "25-35g/day", "Calcium": "1000 mg/day"}, "foods": ["Whole grain bread", "Beans", "Prunes"], "avoid": ["Spicy foods if heartburn"]},
        "exercises": {"recommended": ["Walking 30-40min", "Prenatal yoga", "Pelvic floor exercises"], "avoid": ["High-impact activities"], "intensity": "light to moderate"},
        "clinical": {"screenings": ["Complete blood count"], "tests": ["Rh antibody screen", "Repeat glucose test if needed"], "vitals": ["Weight", "Blood pressure"]}
    },
    32: {
        "baby": {"size": "Jicama/squash", "weight": "3.8 lbs", "features": ["Fingernails form", "Toenails form", "Coordination improves"]},
        "body": {"changes": ["Weight gain ~20-25 lbs total", "Shortness of breath", "Difficulty sleeping"], "symptoms": ["Hemorrhoids", "Varicose veins", "Muscle aches"]},
        "nutrition": {"macros": {"Protein": "70g/day", "Calcium": "1000 mg/day", "Omega-3": "200-300 mg/day"}, "foods": ["Fish (low mercury)", "Nuts", "Seeds"], "avoid": []},
        "exercises": {"recommended": ["Walking", "Swimming", "Modified yoga"], "avoid": ["Lying on back", "Heavy lifting"], "intensity": "light"},
        "clinical": {"screenings": ["Check for gestational diabetes complications"], "tests": ["Blood pressure monitoring"], "vitals": ["Weight", "Blood pressure check"]}
    },
    36: {
        "baby": {"size": "Head of romaine lettuce", "weight": "5.5 lbs", "features": ["Fingernails grown to fingertips", "Position to head-down (ideally)", "Able to turn head side to side"]},
        "body": {"changes": ["Belly drops (lightening)", "Increased Braxton Hicks", "Pelvic pressure"], "symptoms": ["Frequent urination", "Pelvic pain", "Insomnia"]},
        "nutrition": {"macros": {"Protein": "70g/day", "Iron": "27 mg/day", "Calcium": "1000 mg/day"}, "foods": ["Easy-to-digest proteins", "Iron-rich foods"], "avoid": ["Heavy meals before bed"]},
        "exercises": {"recommended": ["Gentle walking", "Pelvic floor exercises", "Relaxation"], "avoid": ["Strenuous activities"], "intensity": "very light"},
        "clinical": {"screenings": ["Check fetal position"], "tests": ["Non-stress test if indicated"], "vitals": ["Weight", "Blood pressure", "Baby position check"]}
    },
    40: {
        "baby": {"size": "Small watermelon", "weight": "6.5-8.5 lbs", "features": ["Fully developed", "Ready for birth", "All systems functional"]},
        "body": {"changes": ["Extreme fatigue", "Mood swings", "Cervical changes"], "symptoms": ["Labor signs", "Bloody show", "Contractions"]},
        "nutrition": {"macros": {"Calories": "2500-2700/day", "Protein": "70g/day"}, "foods": ["Light, nutritious meals", "Hydration"], "avoid": ["Heavy meals"]},
        "exercises": {"recommended": ["Light walking", "Relaxation techniques"], "avoid": ["All except light walking"], "intensity": "minimal"},
        "clinical": {"screenings": ["Prepare for delivery"], "tests": ["Non-stress tests", "Cervical exams"], "vitals": ["Daily monitoring", "Ready for labor"]}
    }
}


# ============================================================================
# POSTPARTUM MILESTONES DATA (by Week)
# ============================================================================

POSTPARTUM_ACTIVITIES = {
    0: "Rest and recovery - avoid all strenuous activity",
    1: "Light activity, pelvic floor awareness, rest",
    2: "Gentle walking, continuing recovery",
    3: "Increase walking duration, start pelvic floor exercises",
    4: "Resume gentle stretching, continue exercises",
    6: "Can resume gentle exercise if approved by doctor",
    8: "Can increase exercise intensity if healing well",
    12: "Can resume most activities if cleared by doctor"
}


# ============================================================================
# MAIN API FUNCTIONS
# ============================================================================

def pregnancy_summary(user_id: int) -> Dict[str, Any]:
    """Get pregnancy summary for user."""
    try:
        from ai.utils.db import get_connection, get_user_profile
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user is in pregnancy life stage
            profile = get_user_profile(user_id)
            if not profile or profile.get("life_stage_id") != 3:  # 3 = Pregnancy
                return {
                    "is_pregnant": False,
                    "message": "User is not currently in pregnancy life stage"
                }
            
            # Get last positive pregnancy test
            cursor.execute("""
                SELECT test_date 
                FROM pregnancy_test_logs 
                WHERE cycle_id IN (
                    SELECT id FROM menstrual_cycles WHERE user_id = %s
                ) 
                AND result = 'positive'
                ORDER BY test_date DESC
                LIMIT 1
            """, (user_id,))
            test_log = cursor.fetchone()
            
            # Get current cycle/pregnancy period
            cursor.execute("""
                SELECT period_start_date, period_end_date
                FROM menstrual_cycles
                WHERE user_id = %s AND is_completed = 0
                ORDER BY period_start_date DESC
                LIMIT 1
            """, (user_id,))
            cycle = cursor.fetchone()
            
            if not cycle or not cycle.get("period_start_date"):
                return {"is_pregnant": False, "message": "No active pregnancy cycle found"}
            
            # Calculate pregnancy week
            pregnancy_start = cycle.get("period_start_date")
            current_date = date.today()
            current_week = (current_date - pregnancy_start).days // 7
            
            # Validate week range
            if current_week < 0 or current_week > 40:
                current_week = max(0, min(40, current_week))
            
            # Determine trimester
            if current_week <= 12:
                trimester = "First"
            elif current_week <= 27:
                trimester = "Second"
            else:
                trimester = "Third"
            
            # Calculate due date
            due_date = pregnancy_start + timedelta(days=280)
            days_until_due = (due_date - current_date).days
            
            # Generate alerts based on week
            alerts = _generate_pregnancy_alerts(current_week, trimester)
            
            return PregnancySummary(
                is_pregnant=True,
                current_week=current_week,
                current_trimester=trimester,
                due_date=due_date.isoformat(),
                days_until_due=max(0, days_until_due),
                last_prenatal_visit=None,
                next_appointment=None,
                health_status="good",
                alerts=alerts
            ).model_dump(exclude_none=False)
    
    except Exception as e:
        print(f"[ERROR] pregnancy_summary failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}


def pregnancy_milestones(user_id: int, week: Optional[int] = None) -> Dict[str, Any]:
    """Get pregnancy milestones for specific week."""
    try:
        from ai.utils.db import get_connection
        
        # Get current week if not specified
        if week is None:
            summary = pregnancy_summary(user_id)
            if summary.get("is_pregnant"):
                week = summary.get("current_week", 20)
            else:
                week = 20  # Default to mid-pregnancy
        
        # Validate week
        week = max(0, min(40, week))
        
        # Find closest milestone data
        milestone_week = _find_closest_milestone_week(week)
        data = PREGNANCY_MILESTONES_DATA.get(milestone_week, PREGNANCY_MILESTONES_DATA[20])
        
        # Determine trimester
        if week <= 12:
            trimester = "First"
        elif week <= 27:
            trimester = "Second"
        else:
            trimester = "Third"
        
        return PregnancyMilestones(
            week=week,
            trimester=trimester,
            baby_development=BabyDevelopment(**data["baby"], week=week),
            your_body=BodyChanges(
                week=week,
                physical_changes=data["body"]["changes"],
                common_symptoms=data["body"]["symptoms"]
            ),
            nutrition_focus=NutritionFocus(
                macro_nutrients=data["nutrition"]["macros"],
                food_groups=data["nutrition"]["foods"],
                avoid=data["nutrition"]["avoid"]
            ),
            safe_exercises=SafeExercise(
                recommended=data["exercises"]["recommended"],
                avoid=data["exercises"]["avoid"],
                intensity_level=data["exercises"]["intensity"]
            ),
            clinical_monitoring=ClinicalMonitoring(
                week=week,
                screenings=data["clinical"]["screenings"],
                tests=data["clinical"]["tests"],
                vital_checks=data["clinical"]["vitals"]
            )
        ).model_dump(exclude_none=False)
    
    except Exception as e:
        print(f"[ERROR] pregnancy_milestones failed for user {user_id}, week {week}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}


def postpartum_recovery(user_id: int) -> Dict[str, Any]:
    """Get postpartum recovery overview."""
    try:
        from ai.utils.db import get_connection, get_user_profile
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user is in postpartum life stage
            profile = get_user_profile(user_id)
            if not profile or profile.get("life_stage_id") != 4:  # 4 = Postpartum
                return {
                    "is_postpartum": False,
                    "message": "User is not currently in postpartum life stage"
                }
            
            # Get completed pregnancy cycle (delivery date)
            cursor.execute("""
                SELECT period_end_date, is_completed
                FROM menstrual_cycles
                WHERE user_id = %s AND is_completed = 1
                ORDER BY period_end_date DESC
                LIMIT 1
            """, (user_id,))
            cycle = cursor.fetchone()
            
            if not cycle or not cycle.get("period_end_date"):
                return {"is_postpartum": False, "message": "No completed pregnancy found"}
            
            delivery_date = cycle.get("period_end_date")
            current_date = date.today()
            postpartum_week = (current_date - delivery_date).days // 7
            postpartum_week = max(0, min(12, postpartum_week))
            
            # Fetch health logs for postpartum data
            cursor.execute("""
                SELECT mood, energy_level, symptoms, notes, log_date
                FROM health_logs
                WHERE user_id = %s AND log_date >= %s
                ORDER BY log_date DESC
                LIMIT 14
            """, (user_id, delivery_date))
            health_logs = cursor.fetchall()
            
            # Calculate recovery metrics from health logs
            recovery_metrics = _calculate_recovery_metrics(health_logs, postpartum_week)
            mental_health = _calculate_mental_health(health_logs)
            alerts = _generate_postpartum_alerts(postpartum_week, recovery_metrics, mental_health)
            
            return PostpartumRecovery(
                postpartum_week=postpartum_week,
                delivery_method="vaginal",  # Would need separate table to track
                recovery_metrics=recovery_metrics,
                mental_health=mental_health,
                activity_level=POSTPARTUM_ACTIVITIES.get(postpartum_week, "Consult doctor"),
                sleep_hours=_estimate_sleep_hours(health_logs) if health_logs else 4.0,
                postpartum_alerts=alerts,
                next_follow_up=(delivery_date + timedelta(days=42)).isoformat()
            ).model_dump(exclude_none=False)
    
    except Exception as e:
        print(f"[ERROR] postpartum_recovery failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}


def support_groups(life_stage: str, limit: int = 10) -> Dict[str, Any]:
    """Get support communities for pregnancy/postpartum."""
    try:
        from ai.utils.db import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Map life stages to community tags
            if life_stage.lower() == "pregnancy":
                tag_filter = "%pregnancy%"
                life_stage_id = 3
            elif life_stage.lower() == "postpartum":
                tag_filter = "%postpartum%"
                life_stage_id = 4
            else:
                return {"groups": [], "total_groups": 0, "user_joined_count": 0}
            
            # Fetch community posts related to life stage
            cursor.execute("""
                SELECT DISTINCT 
                    cp.id,
                    cp.title as name,
                    cp.content as description,
                    COUNT(DISTINCT cp.user_id) as member_count,
                    COUNT(DISTINCT CASE WHEN cp.posted_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN cp.id END) as latest_posts_count,
                    cp.created_at
                FROM community_posts cp
                WHERE cp.tags LIKE %s OR cp.is_approved = 1
                GROUP BY cp.id
                ORDER BY member_count DESC, cp.created_at DESC
                LIMIT %s
            """, (tag_filter, limit))
            
            community_rows = cursor.fetchall()
            
            groups = []
            for row in community_rows:
                groups.append(SupportGroup(
                    id=row.get("id"),
                    name=row.get("name", "Community Group"),
                    description=row.get("description", "Support community"),
                    life_stage=life_stage,
                    member_count=row.get("member_count", 0),
                    active_users_today=max(5, row.get("member_count", 10) // 4),  # Estimate
                    latest_posts_count=row.get("latest_posts_count", 0),
                    is_moderated=True,
                    join_status="not_joined",
                    created_at=row.get("created_at").isoformat() if row.get("created_at") else None
                ))
            
            return SupportGroupResponse(
                groups=groups,
                total_groups=len(groups),
                user_joined_count=0
            ).model_dump(exclude_none=False)
    
    except Exception as e:
        print(f"[ERROR] support_groups failed for {life_stage}: {e}")
        return {"groups": [], "total_groups": 0, "user_joined_count": 0, "error": str(e)}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _find_closest_milestone_week(target_week: int) -> int:
    """Find closest milestone week from available data."""
    available_weeks = [0, 8, 12, 16, 20, 24, 28, 32, 36, 40]
    return min(available_weeks, key=lambda x: abs(x - target_week))


def _generate_pregnancy_alerts(week: int, trimester: str) -> list:
    """Generate relevant alerts based on pregnancy week."""
    alerts = []
    
    if week < 12:
        alerts.append(PregnancyAlert(
            message="Ensure adequate folic acid intake (600 mcg/day)",
            severity="low",
            action_required=False
        ))
    
    if 24 <= week < 28:
        alerts.append(PregnancyAlert(
            message="Glucose tolerance test due this week",
            severity="medium",
            action_required=True
        ))
    
    if week >= 36:
        alerts.append(PregnancyAlert(
            message="Monitor for signs of labor (contractions, bloody show)",
            severity="medium",
            action_required=False
        ))
    
    return alerts


def _generate_postpartum_alerts(week: int, recovery: RecoveryMetrics, mental_health: MentalHealth) -> list:
    """Generate postpartum alerts based on recovery status."""
    alerts = []
    
    if recovery.bleeding_level == "heavy":
        alerts.append(PostpartumAlert(
            type="bleeding",
            level="high",
            message="Excessive bleeding detected. Contact doctor if more than 1 pad/hour"
        ))
    
    if mental_health.depression_screening == "moderate_risk":
        alerts.append(PostpartumAlert(
            type="mental_health",
            level="moderate",
            message="Depression risk detected. Consider speaking with mental health professional"
        ))
    
    if mental_health.anxiety_level > 7:
        alerts.append(PostpartumAlert(
            type="mental_health",
            level="high",
            message="High anxiety levels. Professional support recommended"
        ))
    
    return alerts


def _calculate_recovery_metrics(logs: list, postpartum_week: int) -> RecoveryMetrics:
    """Calculate recovery metrics from health logs."""
    if not logs:
        return RecoveryMetrics(
            physical_recovery_percent=50,
            bleeding_level="light",
            pelvic_floor_status="healing",
            energy_level=3
        )
    
    # Estimate recovery based on week and energy levels
    recovery_percent = min(100, 20 + (postpartum_week * 10))
    
    # Parse energy from logs
    avg_energy = 5
    if logs:
        energy_mapping = {"Very Low": 1, "Low": 3, "Moderate": 5, "High": 7, "Very High": 9}
        energies = [energy_mapping.get(log.get("energy_level"), 5) for log in logs if log.get("energy_level")]
        if energies:
            avg_energy = sum(energies) / len(energies)
    
    return RecoveryMetrics(
        physical_recovery_percent=int(recovery_percent),
        bleeding_level="light" if postpartum_week > 2 else "moderate",
        pelvic_floor_status="healing" if postpartum_week < 6 else "recovered",
        energy_level=int(avg_energy)
    )


def _calculate_mental_health(logs: list) -> MentalHealth:
    """Calculate mental health metrics from health logs."""
    if not logs:
        return MentalHealth(
            mood_stability=60,
            anxiety_level=5,
            depression_screening="low_risk",
            mood_trend="stable",
            supportive_resources=["Postpartum Support Group", "Mental Health Hotline"]
        )
    
    # Parse mood from logs
    mood_mapping = {"Happy": 8, "Neutral": 5, "Sad": 2, "Anxious": 3, "Overwhelmed": 2}
    moods = [mood_mapping.get(log.get("mood"), 5) for log in logs if log.get("mood")]
    
    avg_mood = sum(moods) / len(moods) if moods else 5
    mood_stability = int((avg_mood / 10) * 100)
    
    # Detect trend
    if len(moods) >= 2:
        trend = "improving" if moods[-1] > moods[0] else "declining" if moods[-1] < moods[0] else "stable"
    else:
        trend = "stable"
    
    return MentalHealth(
        mood_stability=mood_stability,
        anxiety_level=5,  # Would need specific anxiety tracking
        depression_screening="low_risk" if mood_stability > 70 else "moderate_risk",
        last_mood_entry=logs[0].get("log_date").isoformat() if logs else None,
        mood_trend=trend,
        supportive_resources=["Postpartum Support Group", "Mental Health Helpline", "Partner Support"]
    )


def _estimate_sleep_hours(logs: list) -> float:
    """Estimate sleep hours from health logs (would be more accurate with dedicated field)."""
    if not logs:
        return 4.0
    
    # Default estimate for postpartum sleep
    return 4.5


