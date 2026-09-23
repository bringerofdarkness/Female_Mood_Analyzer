"""Athlete Performance & Readiness API Service."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from ai.models.athlete_models import (
    AthleteReadinessResponse,
    CycleInfo,
    FatigueAlert,
    HRVMetric,
    Metrics,
    PhaseRecommendation,
    RecoveryMetric,
    SleepMetric,
    TrainingLoadMetric,
)
from ai.utils.db import get_current_cycle, get_snapshot, get_user_profile


def athlete_readiness(user_id: int) -> AthleteReadinessResponse | dict[str, Any]:
    """
    Calculate athlete performance readiness score (0-100).
    Integrates HRV, sleep, recovery, training load, and menstrual cycle phase.
    
    **Formula:**
    Readiness = (HRV_score * 0.30 + Sleep_score * 0.35 + Recovery_score * 0.35) + Phase_Boost
    
    **Returns:**
    Comprehensive readiness assessment with alerts and phase-based recommendations.
    """
    try:
        # Fetch user data
        profile = get_user_profile(user_id)
        if not profile:
            return {
                "status": "error",
                "message": f"User {user_id} not found",
                "user_id": user_id,
            }
        
        # Fetch today's performance data from Terra
        hrv_data = _fetch_hrv_data(user_id)
        sleep_data = _fetch_sleep_data(user_id)
        recovery_data = _fetch_recovery_data(user_id)
        training_load = _fetch_training_load(user_id)
        
        # Get cycle info
        cycle_info_dict = _get_cycle_info(user_id)
        
        # Calculate readiness components
        hrv_metric = _calculate_hrv_score(hrv_data)
        sleep_metric = _calculate_sleep_score(sleep_data)
        recovery_metric = _calculate_recovery_score(recovery_data)
        training_load_metric = TrainingLoadMetric(
            value=training_load["value"],
            status=training_load["status"],
        )
        
        # Calculate base readiness score
        base_score = (
            hrv_metric.score * 0.30 +
            sleep_metric.score * 0.35 +
            recovery_metric.score * 0.35
        )
        
        # Apply cycle phase modifier
        phase_boost = cycle_info_dict["phase_boost"]
        final_score = min(100, max(0, base_score + phase_boost))
        
        # Determine readiness level
        readiness_level = _get_readiness_level(final_score)
        readiness_message = _get_readiness_message(
            readiness_level, 
            cycle_info_dict["phase"],
            hrv_metric.status,
            recovery_metric.status
        )
        
        # Generate fatigue alerts
        alerts = _generate_fatigue_alerts(
            sleep_data,
            recovery_data,
            training_load,
            hrv_data
        )
        
        # Generate recommendations
        recommendations = _generate_phase_recommendations(cycle_info_dict["phase"])
        
        # Build cycle info object
        cycle_info = CycleInfo(
            phase=cycle_info_dict["phase"],
            cycle_day=cycle_info_dict["cycle_day"],
            days_to_next_phase=cycle_info_dict["days_to_next_phase"],
            phase_boost=phase_boost,
            phase_description=cycle_info_dict["phase_description"],
        )
        
        # Build metrics object
        metrics = Metrics(
            hrv=hrv_metric,
            sleep=sleep_metric,
            recovery=recovery_metric,
            training_load=training_load_metric,
        )
        
        # Build response
        response = AthleteReadinessResponse(
            date=date.today().isoformat(),
            readiness_score=int(final_score),
            readiness_level=readiness_level,
            readiness_message=readiness_message,
            metrics=metrics,
            fatigue_alerts=alerts,
            cycle_info=cycle_info,
            recommendations=recommendations,
            next_update=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        )
        
        return response.model_dump(exclude_none=False)
    
    except Exception as e:
        print(f"[ERROR] athlete_readiness failed for user {user_id}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "user_id": user_id,
        }


def _fetch_hrv_data(user_id: int) -> dict[str, Any]:
    """Fetch HRV data from terra_activity_data for today and yesterday."""
    try:
        from ai.utils.db import get_connection
        from pymysql.cursors import DictCursor
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    JSON_EXTRACT(payload, '$.data[0].heart_data.heart_rate_data.summary.avg_hrv_rmssd') as hrv_value,
                    created_at
                FROM terra_activity_data
                WHERE user_id = %s AND type = 'body'
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            
            if not row:
                return {"value": 0, "high": 0, "low": 0, "trend": 0, "available": False}
            
            # Handle JSON null (comes as string "null")
            hrv_raw = row.get("hrv_value")
            hrv_value = 0
            if hrv_raw and hrv_raw != "null":
                try:
                    hrv_value = float(hrv_raw)
                except (ValueError, TypeError):
                    hrv_value = 0
            
            return {
                "value": int(hrv_value),
                "high": 0,
                "low": 0,
                "trend": 0,
                "available": hrv_value > 0,
            }
    except Exception as e:
        print(f"[ERROR] _fetch_hrv_data: {e}")
        return {"value": 0, "trend": 0, "available": False}


def _fetch_sleep_data(user_id: int) -> dict[str, Any]:
    """Fetch sleep data from terra_activity_data."""
    try:
        from ai.utils.db import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    JSON_EXTRACT(payload, '$.data[0].scores.sleep') as sleep_score
                FROM terra_activity_data
                WHERE user_id = %s AND type = 'daily'
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            
            if not row:
                return {"hours": 0, "score": 60, "available": False}
            
            sleep_score = int(float(row.get("sleep_score") or 0)) if row.get("sleep_score") else None
            
            # If Terra doesn't have sleep score, use safe baseline (60 = adequate)
            if sleep_score is None or sleep_score == 0:
                sleep_score = 60
                available = False
            else:
                available = True
            
            return {
                "hours": 0,  # Terra data doesn't include duration_seconds
                "score": sleep_score,
                "available": available,
            }
    except Exception as e:
        print(f"[ERROR] _fetch_sleep_data: {e}")
        return {"hours": 0, "score": 60, "available": False}


def _fetch_recovery_data(user_id: int) -> dict[str, Any]:
    """Fetch recovery score from terra_activity_data, or estimate from MET level."""
    try:
        from ai.utils.db import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    JSON_EXTRACT(payload, '$.data[0].scores.recovery') as recovery_score,
                    JSON_EXTRACT(payload, '$.data[0].MET_data.avg_level') as avg_met
                FROM terra_activity_data
                WHERE user_id = %s AND type = 'daily'
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            
            if not row:
                return {"score": 55, "available": False}
            
            # Handle JSON null (comes as string "null")
            recovery_raw = row.get("recovery_score")
            avg_met_raw = row.get("avg_met")
            
            recovery_score = None
            if recovery_raw and recovery_raw != "null":
                try:
                    recovery_score = int(float(recovery_raw))
                except (ValueError, TypeError):
                    recovery_score = None
            
            avg_met = 0
            if avg_met_raw and avg_met_raw != "null":
                try:
                    avg_met = float(avg_met_raw)
                except (ValueError, TypeError):
                    avg_met = 0
            
            # If Terra has recovery score, use it
            if recovery_score and recovery_score > 0:
                return {"score": recovery_score, "available": True}
            
            # Otherwise, estimate from MET level (inverse relationship)
            # MET 10-15 is moderate activity: recovery = 50-70
            if avg_met > 0:
                estimated_recovery = min(80, max(30, int(100 - (avg_met * 3))))
                print(f"[DEBUG] user {user_id}: estimated recovery from MET {avg_met} = {estimated_recovery}")
                return {"score": estimated_recovery, "available": False}
            
            # Safe baseline
            return {"score": 55, "available": False}
    except Exception as e:
        print(f"[ERROR] _fetch_recovery_data: {e}")
        return {"score": 55, "available": False}


def _fetch_training_load(user_id: int) -> dict[str, Any]:
    """Calculate training load from MET level or activity seconds."""
    try:
        from ai.utils.db import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    JSON_EXTRACT(payload, '$.data[0].MET_data.avg_level') as avg_met,
                    JSON_EXTRACT(payload, '$.data[0].active_durations_data.activity_seconds') as activity_seconds
                FROM terra_activity_data
                WHERE user_id = %s AND type = 'daily'
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            
            if not row:
                return {"value": 0, "status": "low", "available": False}
            
            # Handle JSON null (comes as string "null")
            avg_met_raw = row.get("avg_met")
            activity_raw = row.get("activity_seconds")
            
            avg_met = 0
            if avg_met_raw and avg_met_raw != "null":
                try:
                    avg_met = float(avg_met_raw)
                except (ValueError, TypeError):
                    avg_met = 0
            
            activity_seconds = 0
            if activity_raw and activity_raw != "null":
                try:
                    activity_seconds = float(activity_raw)
                except (ValueError, TypeError):
                    activity_seconds = 0
            
            # Training Load AU = (activity_minutes * 0.8) + (MET * 5)
            activity_minutes = activity_seconds / 60
            training_load = (activity_minutes * 0.8) + (avg_met * 5) if (activity_minutes or avg_met) else 0
            
            status = "low" if training_load < 100 else "moderate" if training_load < 300 else "high"
            
            print(f"[DEBUG] user {user_id}: activity_min={activity_minutes}, MET={avg_met}, load={training_load}")
            
            return {
                "value": round(training_load, 1),
                "status": status,
                "available": (activity_minutes > 0 or avg_met > 0),
            }
    except Exception as e:
        print(f"[ERROR] _fetch_training_load: {e}")
        return {"value": 0, "status": "low", "available": False}


def _get_cycle_info(user_id: int) -> dict[str, Any]:
    """Get current menstrual cycle phase and information."""
    try:
        cycle = get_current_cycle(user_id)
        
        if not cycle or not cycle.get("period_start_date"):
            return {
                "phase": "unknown",
                "cycle_day": 0,
                "days_to_next_phase": 0,
                "phase_boost": 0,
                "phase_description": "No cycle data available",
            }
        
        period_start = cycle.get("period_start_date")
        if isinstance(period_start, str):
            from datetime import datetime as dt
            period_start = dt.fromisoformat(period_start).date()
        
        today = date.today()
        cycle_day = (today - period_start).days + 1
        
        # Phase definitions
        if 1 <= cycle_day <= 5:
            phase = "menstrual"
            phase_boost = -7
            next_phase_day = 6
            description = "Menstrual phase - prioritize recovery and rest"
        elif 6 <= cycle_day <= 13:
            phase = "follicular"
            phase_boost = 2
            next_phase_day = 14
            description = "Follicular phase - building energy, good for strength training"
        elif 14 <= cycle_day <= 16:
            phase = "ovulatory"
            phase_boost = 12
            next_phase_day = 17
            description = "Ovulatory phase - peak energy and performance window"
        else:  # 17-28+
            phase = "luteal"
            phase_boost = -3
            next_phase_day = (28 - cycle_day) + 1
            description = "Luteal phase - stable energy, good for endurance"
        
        days_to_next_phase = max(0, next_phase_day - cycle_day)
        
        return {
            "phase": phase,
            "cycle_day": cycle_day,
            "days_to_next_phase": days_to_next_phase,
            "phase_boost": phase_boost,
            "phase_description": description,
        }
    except Exception as e:
        print(f"[ERROR] _get_cycle_info: {e}")
        return {
            "phase": "unknown",
            "cycle_day": 0,
            "days_to_next_phase": 0,
            "phase_boost": 0,
            "phase_description": "Cycle data unavailable",
        }


def _calculate_hrv_score(hrv_data: dict[str, Any]) -> HRVMetric:
    """Convert HRV (ms) to 0-100 score. Higher HRV = better readiness."""
    # HRV typically ranges 20-200ms. Map to score.
    # < 30ms = poor (0-25), 30-50 = fair (25-50), 50-100 = good (50-85), > 100 = excellent (85-100)
    hrv_value = hrv_data.get("value", 0)
    
    if hrv_value < 30:
        score = max(0, int((hrv_value / 30) * 25))
        status = "poor"
    elif hrv_value < 50:
        score = int(25 + ((hrv_value - 30) / 20) * 25)
        status = "warning"
    elif hrv_value < 100:
        score = int(50 + ((hrv_value - 50) / 50) * 35)
        status = "good"
    else:
        score = min(100, int(85 + ((hrv_value - 100) / 100) * 15))
        status = "good"
    
    return HRVMetric(
        value=hrv_value,
        score=score,
        trend=hrv_data.get("trend", 0),
        status=status,
    )


def _calculate_sleep_score(sleep_data: dict[str, Any]) -> SleepMetric:
    """Calculate sleep quality score."""
    sleep_score = sleep_data.get("score", 0)
    sleep_hours = sleep_data.get("hours", 0)
    
    # If Terra didn't provide score, estimate from hours (7-9 hours is optimal)
    if sleep_score == 0:
        if sleep_hours >= 7 and sleep_hours <= 9:
            sleep_score = 90
        elif sleep_hours >= 6 and sleep_hours < 7:
            sleep_score = 70
        elif sleep_hours >= 9 and sleep_hours < 10:
            sleep_score = 80
        else:
            sleep_score = max(20, int((sleep_hours / 8) * 100))
    
    status = "good" if sleep_score > 75 else "fair" if sleep_score > 50 else "poor"
    
    return SleepMetric(
        hours=sleep_hours,
        score=sleep_score,
        status=status,
    )


def _calculate_recovery_score(recovery_data: dict[str, Any]) -> RecoveryMetric:
    """Calculate recovery metric."""
    recovery_score = recovery_data.get("score", 0)
    
    status = "recovered" if recovery_score > 80 else "partial" if recovery_score > 50 else "depleted"
    
    return RecoveryMetric(
        score=recovery_score,
        status=status,
    )


def _get_readiness_level(score: int) -> str:
    """Determine readiness level from score."""
    if score >= 85:
        return "Peak Ready"
    elif score >= 70:
        return "Ready"
    elif score >= 50:
        return "Adequate"
    elif score >= 30:
        return "Fatigued"
    else:
        return "Depleted"


def _get_readiness_message(
    level: str,
    phase: str,
    hrv_status: str,
    recovery_status: str,
) -> str:
    """Generate personalized readiness message."""
    if level == "Peak Ready":
        if phase == "ovulatory":
            return "You're at peak performance during your ovulatory phase. Ideal for high-intensity workouts, competitions, or setting new PRs."
        return "You're at peak performance. Ideal for high-intensity workouts or competitions."
    
    elif level == "Ready":
        return f"You're ready for training. Your {phase} phase supports good workout performance with {recovery_status} recovery."
    
    elif level == "Adequate":
        return "You're adequately recovered for moderate training. Consider listening to your body today."
    
    elif level == "Fatigued":
        return "You're showing signs of fatigue. Consider active recovery or lighter intensity training today."
    
    else:  # Depleted
        return "You're significantly fatigued. Prioritize rest, sleep, and recovery today."


def _generate_fatigue_alerts(
    sleep_data: dict[str, Any],
    recovery_data: dict[str, Any],
    training_load: dict[str, Any],
    hrv_data: dict[str, Any],
) -> list[FatigueAlert]:
    """Generate fatigue risk alerts."""
    alerts = []
    
    # Recovery alert
    recovery_score = recovery_data.get("score", 0)
    if recovery_score < 50:
        alerts.append(FatigueAlert(
            type="recovery_deficit",
            level="high",
            message="Your recovery score is low. Consider reducing training intensity today.",
        ))
    elif recovery_score < 70:
        alerts.append(FatigueAlert(
            type="recovery_deficit",
            level="moderate",
            message="Recovery is partial. Monitor fatigue levels throughout the day.",
        ))
    else:
        alerts.append(FatigueAlert(
            type="recovery_status",
            level="low",
            message="Fully recovered. Adequate energy for training.",
        ))
    
    # Sleep debt alert
    sleep_hours = sleep_data.get("hours", 0)
    if sleep_hours < 6:
        alerts.append(FatigueAlert(
            type="sleep_debt",
            level="high",
            message=f"Sleep debt: only {sleep_hours}h slept. Prioritize rest today.",
        ))
    elif sleep_hours < 7:
        alerts.append(FatigueAlert(
            type="sleep_debt",
            level="moderate",
            message=f"Sleep below optimal: {sleep_hours}h. Consider earlier bedtime.",
        ))
    
    # Training load alert
    load = training_load.get("value", 0)
    if load > 300:
        alerts.append(FatigueAlert(
            type="overtraining_risk",
            level="high",
            message="Training load is very high. Consider deload or active recovery.",
        ))
    elif load > 200:
        alerts.append(FatigueAlert(
            type="overtraining_risk",
            level="moderate",
            message="Training load is elevated. Monitor cumulative fatigue.",
        ))
    else:
        alerts.append(FatigueAlert(
            type="overtraining_risk",
            level="low",
            message="Training load is manageable.",
        ))
    
    # HRV alert (deviation from baseline)
    hrv_value = hrv_data.get("value", 0)
    if hrv_value < 30:
        alerts.append(FatigueAlert(
            type="cumulative_fatigue",
            level="high",
            message="Low HRV indicates accumulated stress/fatigue. Prioritize recovery.",
        ))
    elif hrv_value < 50:
        alerts.append(FatigueAlert(
            type="cumulative_fatigue",
            level="moderate",
            message="HRV is below optimal. Some accumulated fatigue detected.",
        ))
    
    return alerts


def _generate_phase_recommendations(phase: str) -> PhaseRecommendation:
    """Generate phase-specific training recommendations."""
    recommendations = {
        "menstrual": PhaseRecommendation(
            workout_type="recovery",
            intensity_level="low",
            suggested_workouts=[
                "Restorative yoga",
                "Light walking or leisurely cycling",
                "Stretching and mobility work",
                "Meditation or breathing exercises",
            ],
            avoid=[
                "High-intensity interval training (HIIT)",
                "Heavy weightlifting",
                "Long endurance sessions",
                "New intense training protocols",
            ],
        ),
        "follicular": PhaseRecommendation(
            workout_type="strength",
            intensity_level="high",
            suggested_workouts=[
                "Heavy strength training (3-6 rep range)",
                "Hypertrophy-focused resistance training",
                "High-intensity interval training (HIIT)",
                "New fitness challenges or skill work",
            ],
            avoid=[
                "Excessive steady-state cardio",
                "Very high volume training",
                "Complete deload/rest days",
            ],
        ),
        "ovulatory": PhaseRecommendation(
            workout_type="high_intensity",
            intensity_level="maximum",
            suggested_workouts=[
                "Competitive activities or races",
                "Maximum effort strength/power testing",
                "High-intensity interval training (HIIT)",
                "Personal record (PR) attempts",
                "Demanding metabolic conditioning",
            ],
            avoid=[
                "Light/easy sessions",
                "Recovery-focused workouts",
                "Experimenting with new heavy lifts",
            ],
        ),
        "luteal": PhaseRecommendation(
            workout_type="endurance",
            intensity_level="moderate",
            suggested_workouts=[
                "Steady-state cardio (running, cycling, rowing)",
                "Moderate-intensity strength training",
                "Longer duration, lower intensity sessions",
                "Active recovery paired with strength",
                "Stability and balance work",
            ],
            avoid=[
                "Very high-intensity efforts",
                "Extreme training volume",
                "Multiple intense sessions per day",
            ],
        ),
        "unknown": PhaseRecommendation(
            workout_type="moderate",
            intensity_level="moderate",
            suggested_workouts=[
                "Balanced training with varied intensity",
                "Moderate strength and conditioning",
                "Listen to your body for intensity cues",
            ],
            avoid=[],
        ),
    }
    
    return recommendations.get(phase, recommendations["unknown"])
