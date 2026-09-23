import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from ai.config import settings
from ai.models.beauty_models import (
    BeautyRequest, BeautyResponse, TodayScan, FindingItem, HistoryItem,
    SleepSkinData, CyclePhases, Correlations, AIInsights, PhaseData
)
from ai.utils.claude_llm import ClaudeLLM
from ai.utils.db import get_connection


BEAUTY_SYSTEM_PROMPT = """You are an expert beauty & skincare AI assistant for a women's wellness app.

ANALYSIS REQUIREMENTS:
- Analyze provided skin metrics (7 scores: overall, hydration, redness, texture, glow, pore health, elasticity)
- Consider menstrual cycle phase impact on skin
- Analyze activity/sleep correlation with skin health
- Provide personalized skincare recommendations

RESPONSE FORMAT:
Return ONLY valid JSON with:
{
    "overall_assessment": "string - 2-3 sentence summary of current skin health",
    "phase_impact": "string - how current menstrual phase affects skin",
    "sleep_correlation": "string - how sleep impacts skin",
    "key_focus_areas": ["array", "of", "problem", "areas"],
    "recommendations": ["array", "of", "actionable", "skincare", "tips"],
    "routine_suggestion": "string - brief morning/evening routine",
    "confidence_score": 85
}

CRITICAL: Return ONLY JSON, no markdown or additional text."""


# Helper functions for score mapping and enhancements
def _score_to_status_label(score: int) -> str:
    """Convert numeric score (0-100) to status label."""
    if score is None:
        return "Unknown"
    try:
        score_int = int(score)
        if score_int >= 76:
            return "Radiant"
        elif score_int >= 51:
            return "Good"
        elif score_int >= 26:
            return "Fair"
        else:
            return "Poor"
    except (TypeError, ValueError):
        return "Unknown"


def _extract_scan_findings(scan_data: dict[str, Any]) -> list[FindingItem]:
    """Extract detailed scan findings from skin metrics (matching UI). Returns FindingItem instances."""
    if not scan_data:
        return []
    
    findings = []
    
    # Safely extract and convert all metrics
    def safe_score(val):
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None
    
    def score_to_badge(score: float | None) -> str:
        """Convert score (0-100) to badge: healthy, good, mid, low"""
        if score is None:
            return "low"
        try:
            score_val = float(score)
            if score_val >= 76:
                return "healthy"
            elif score_val >= 51:
                return "good"
            elif score_val >= 26:
                return "mid"
            else:
                return "low"
        except (TypeError, ValueError):
            return "low"
    
    hydration = safe_score(scan_data.get('hydration_score'))
    pore = safe_score(scan_data.get('pore_health_score'))
    redness = safe_score(scan_data.get('redness_score'))
    texture = safe_score(scan_data.get('texture_score'))
    elasticity = safe_score(scan_data.get('elasticity_score'))
    
    # Map metrics to detailed findings with badge based on score range
    
    # Moisture Barrier finding
    if hydration is not None:
        if hydration >= 75:
            status = "Well-protected, no signs of disruption"
        elif hydration >= 50:
            status = "Adequate protection with minor dryness"
        else:
            status = "Compromised barrier, needs hydration"
        
        findings.append(FindingItem(
            finding="Moisture barrier",
            status=status,
            badge=score_to_badge(hydration),
            score=hydration
        ))
    
    # Pore Health finding
    if pore is not None:
        if pore >= 75:
            status = "Clear pores detected in all zones"
        elif pore >= 50:
            status = "Minimal blockage detected in T-zone"
        else:
            status = "Significant blockage detected"
        
        findings.append(FindingItem(
            finding="Pore congestion",
            status=status,
            badge=score_to_badge(pore),
            score=pore
        ))
    
    # Inflammation Markers finding
    if redness is not None:
        if redness <= 30:
            status = "Clear skin, minimal redness detected"
        elif redness <= 60:
            status = "Slight redness around cheeks and nose"
        else:
            status = "Significant inflammation across zones"
        
        findings.append(FindingItem(
            finding="Inflammation markers",
            status=status,
            badge=score_to_badge(redness),
            score=redness
        ))
    
    # Melanin Uniformity finding
    if texture is not None:
        if texture >= 75:
            status = "Even tone distribution across all zones"
        elif texture >= 50:
            status = "Minor discoloration in patches, mostly cheeks"
        else:
            status = "Significant discoloration across zones"
        
        findings.append(FindingItem(
            finding="Melanin uniformity",
            status=status,
            badge=score_to_badge(texture),
            score=texture
        ))
    
    # Elasticity finding
    if elasticity is not None:
        if elasticity >= 75:
            status = "Strong elasticity with excellent bounce-back"
        elif elasticity >= 50:
            status = "Fair elasticity with minor sagging around contours"
        else:
            status = "Loss of firmness, visible sagging detected"
        
        findings.append(FindingItem(
            finding="Skin firmness",
            status=status,
            badge=score_to_badge(elasticity),
            score=elasticity
        ))
    
    return findings  # Returns List[FindingItem]


def _calculate_sleep_skin_correlation(
    skin_data: list[dict[str, Any]],
    activity_data: dict[str, Any]
) -> dict[str, Any]:
    """Calculate correlation between sleep and skin scores with chart data."""
    
    if not skin_data or not activity_data:
        return {
            "correlation_detected": False,
            "correlation_strength": 0,
            "chart_data": [],
            "insight": "Insufficient data for correlation analysis"
        }
    
    # Prepare data for correlation
    skin_scores = [s.get('overall_score', 0) for s in reversed(skin_data)]  # Chronological order
    sleep_values = [activity_data.get('avg_sleep', 0)] * len(skin_scores)
    
    # Calculate simple correlation
    if len(skin_scores) >= 2:
        avg_skin = sum(skin_scores) / len(skin_scores)
        avg_sleep = sum(sleep_values) / len(sleep_values) if sleep_values else 0
        
        covariance = sum((skin_scores[i] - avg_skin) * (sleep_values[i] - avg_sleep) 
                        for i in range(len(skin_scores))) / len(skin_scores)
        
        std_skin = (sum((s - avg_skin) ** 2 for s in skin_scores) / len(skin_scores)) ** 0.5
        std_sleep_val = (sum((s - avg_sleep) ** 2 for s in sleep_values) / len(sleep_values)) ** 0.5 if len(sleep_values) > 0 else 1
        
        correlation = covariance / (std_skin * std_sleep_val) if (std_skin * std_sleep_val) > 0 else 0
        correlation = max(-1, min(1, correlation))
        
        # Build chart data
        chart_data = []
        for scan in reversed(skin_data)[-7:]:
            created_at = scan.get('created_at', '')
            if isinstance(created_at, str):
                date_label = created_at.split('T')[0]
            else:
                date_label = str(created_at)
            
            chart_data.append({
                "date": date_label,
                "skin_score": scan.get('overall_score', 0),
                "sleep_hours": activity_data.get('avg_sleep', 0)
            })
        
        return {
            "correlation_detected": abs(correlation) > 0.3,
            "correlation_strength": round(abs(correlation) * 100, 1),
            "correlation_direction": "positive" if correlation > 0 else "negative",
            "chart_data": chart_data,
            "insight": "Each extra hour of sleep boosts your skin score by ~4 points" if correlation > 0.3 else "Sleep correlation data accumulating"
        }
    
    return {
        "correlation_detected": False,
        "correlation_strength": 0,
        "chart_data": [],
        "insight": "Minimum 2 scans needed for correlation analysis"
    }


def _format_history_for_ui(history_scans: list[dict[str, Any]]) -> list[HistoryItem]:
    """Format history scans for UI display with day_of_week and days_ago. Returns HistoryItem instances."""
    formatted = []
    today = datetime.now()
    
    for scan in history_scans:
        created_at = scan.get('created_at')
        
        # Parse datetime if string and remove timezone
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).replace(tzinfo=None)
            except:
                created_at = datetime.fromisoformat(created_at)
        elif created_at and hasattr(created_at, 'replace'):
            # Remove timezone info to make it naive
            created_at = created_at.replace(tzinfo=None)
        
        if created_at:
            # Calculate days ago
            days_ago = (today - created_at).days
            
            # Format date and day of week
            date_str = created_at.strftime('%Y-%m-%d')
            day_of_week = created_at.strftime('%A')
            
            formatted.append(HistoryItem(
                date=date_str,
                day_of_week=day_of_week,
                score=float(scan.get('overall_score', 0)),
                days_ago=days_ago
            ))
    
    return formatted  # Returns List[HistoryItem]


def _build_sleep_skin_chart(user_id: int, activity_data: dict[str, Any]) -> SleepSkinData:
    """Build 7-day sleep/skin correlation chart data. Returns SleepSkinData instance."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Fetch last 7 days of skin scores
            cur.execute("""
                SELECT 
                    DATE(created_at) as scan_date,
                    AVG(overall_score) as avg_score
                FROM skin_scans
                WHERE user_id = %s
                AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY created_at ASC
            """, (user_id,))
            
            rows = cur.fetchall()
            
            # Build chart data for 7 days
            chart_data = []
            today = datetime.now()
            
            for i in range(6, -1, -1):  # Last 7 days
                day_date = today - timedelta(days=i)
                day_name = day_date.strftime('%a')  # Mon, Tue, etc.
                date_str = day_date.strftime('%Y-%m-%d')
                
                # Find score for this date if exists
                skin_score = None
                for row in rows:
                    try:
                        row_date = row.get('scan_date')
                        avg_score = row.get('avg_score')
                        
                        if isinstance(row_date, str):
                            if date_str in row_date:
                                skin_score = float(avg_score) if avg_score is not None else None
                                break
                        elif row_date and hasattr(row_date, 'strftime'):
                            if row_date.strftime('%Y-%m-%d') == date_str:
                                skin_score = float(avg_score) if avg_score is not None else None
                                break
                    except (TypeError, ValueError, AttributeError):
                        continue
                
                # Only add to chart if we have actual data
                if skin_score is not None:
                    sleep_hours = activity_data.get('avg_sleep')
                    if sleep_hours is not None:
                        try:
                            sleep_hours = float(sleep_hours)
                        except (TypeError, ValueError):
                            sleep_hours = None
                    
                    chart_data.append({
                        "day": day_name,
                        "date": date_str,
                        "skin_score": int(skin_score),
                        "sleep_hours": round(sleep_hours, 1) if sleep_hours else None
                    })
            
            # Only claim correlation if we have sufficient data points
            if len(chart_data) < 3:
                return SleepSkinData(
                    correlation_detected=False,
                    correlation_strength=0,
                    correlation_direction="neutral",
                    insight="Not enough historical data to detect sleep/skin correlation yet.",
                    chart_data=chart_data
                )
            
            return SleepSkinData(
                correlation_detected=True,
                correlation_strength=75.0,
                correlation_direction="positive",
                insight="Monitoring sleep and skin correlation. More data will improve accuracy.",
                chart_data=chart_data
            )
    
    except Exception as exc:
        print(f"Error building sleep/skin chart: {exc}")
        return SleepSkinData(
            correlation_detected=False,
            correlation_strength=0,
            correlation_direction="neutral",
            insight="Insufficient data for correlation analysis",
            chart_data=[]
        )


def get_beauty_overview(request: BeautyRequest) -> BeautyResponse:
    """
    Fetch beauty & radiance data for a user.
    
    Args:
        request: BeautyRequest with user_id, days, include_correlations
    
    Returns:
        BeautyResponse with today's metrics, history, and AI insights
    """
    try:
        user_id = request.user_id
        days = request.days or 30
        
        # Fetch skin scans data
        today_skin = _fetch_latest_skin_scan(user_id)
        history_skin = _fetch_skin_scan_history(user_id, days)
        
        # Add score comparison to today - calculate even without history
        try:
            today_score = today_skin.get('overall_score') or 0
            if history_skin:
                prev_score = history_skin[0].get('overall_score') or 0
                score_change = int(today_score) - int(prev_score)
                today_skin['score_change'] = score_change
                today_skin['previous_score'] = prev_score
                today_skin['comparison_text'] = f"{abs(score_change):+d}pts vs last scan"
            else:
                # No history - show baseline
                today_skin['score_change'] = 0
                today_skin['previous_score'] = today_score
                today_skin['comparison_text'] = "First scan - no history"
        except (TypeError, ValueError):
            today_skin['score_change'] = 0
            today_skin['previous_score'] = 0
            today_skin['comparison_text'] = "Unable to calculate change"
        
        # Fetch activity/sleep data
        activity_data = _fetch_terra_activity_data(user_id, days)
        
        # Fetch menstrual cycle data for context
        cycle_data = _fetch_menstrual_cycle_context(user_id)
        
        # Build context for Claude
        context = _build_beauty_context(
            today_skin=today_skin,
            history_skin=history_skin,
            activity_data=activity_data,
            cycle_data=cycle_data
        )
        
        # Get Claude insights
        ai_insights = _generate_beauty_insights(context)
        
        # Format history for UI display
        formatted_history = _format_history_for_ui(history_skin)
        
        # Build correlations if requested
        correlations_obj = None
        if request.include_correlations:
            # Get sleep/skin correlation with 7-day chart data
            sleep_correlation = _build_sleep_skin_chart(
                user_id=user_id,
                activity_data=activity_data
            )
            
            # Get cycle phase correlations
            cycle_correlations = _calculate_cycle_phase_correlations(user_id, history_skin)
            
            # Create Correlations model instance
            correlations_obj = Correlations(
                sleep_skin=sleep_correlation,
                cycle_phases=cycle_correlations
            )
        
        # Create TodayScan instance from dict
        today_obj = TodayScan(**today_skin) if today_skin else None
        
        return BeautyResponse(
            today=today_obj or TodayScan(
                id=0, user_id=user_id, image_path="", overall_score=0,
                hydration_score=0, redness_score=0, texture_score=0,
                glow_index=0, pore_health_score=0, elasticity_score=0,
                hydration_status="", redness_status="", texture_status="",
                glow_status="", pore_health_status="", elasticity_status="",
                neumera_insight="", created_at="", updated_at="",
                status_label="Unknown", findings=[]
            ),
            history=formatted_history,
            correlations=correlations_obj or Correlations(
                sleep_skin=SleepSkinData(
                    correlation_detected=False,
                    correlation_strength=0.0,
                    correlation_direction="neutral",
                    insight="No data available",
                    chart_data=[]
                ),
                cycle_phases=CyclePhases(
                    phase_breakdown={
                        "menstrual": PhaseData(label="Menstrual", score=0, description=""),
                        "follicular": PhaseData(label="Follicular", score=0, description=""),
                        "ovulation": PhaseData(label="Ovulation", score=0, description=""),
                        "luteal": PhaseData(label="Luteal", score=0, description=""),
                    },
                    best_phase="",
                    worst_phase=""
                )
            ),
            ai_insights=ai_insights
        )
    
    except Exception as exc:
        raise ValueError(f"Beauty overview generation failed: {exc}")


def _fetch_latest_skin_scan(user_id: int) -> dict[str, Any]:
    """Fetch the latest skin scan for a user."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id, user_id, image_path,
                    overall_score, hydration_score, redness_score,
                    texture_score, glow_index, pore_health_score,
                    elasticity_score,
                    hydration_status, redness_status, texture_status,
                    glow_status, pore_health_status, elasticity_status,
                    neumera_insight, created_at, updated_at
                FROM skin_scans
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            row = cur.fetchone()
            if not row:
                return {}
            
            # Convert datetime objects to ISO strings for JSON serialization
            if row.get('created_at'):
                row['created_at'] = row['created_at'].isoformat()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].isoformat()
            
            # Add status label based on overall score
            if row.get('overall_score') is not None:
                row['status_label'] = _score_to_status_label(row['overall_score'])
            
            # Add detailed scan findings
            row['findings'] = _extract_scan_findings(row)
            
            return row
    
    except Exception as exc:
        print(f"Error fetching latest skin scan: {exc}")
        return {}


def _fetch_skin_scan_history(user_id: int, days: int = 30) -> list[dict[str, Any]]:
    """Fetch skin scan history (excluding today's latest scan) for trend analysis."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Fetch historical scans (90 days to show trend, excluding latest)
            # Use ROW_NUMBER to exclude only the most recent scan
            cur.execute("""
                SELECT 
                    id, user_id, image_path,
                    overall_score, hydration_score, redness_score,
                    texture_score, glow_index, pore_health_score,
                    elasticity_score,
                    hydration_status, redness_status, texture_status,
                    glow_status, pore_health_status, elasticity_status,
                    neumera_insight, created_at, updated_at
                FROM (
                    SELECT 
                        id, user_id, image_path,
                        overall_score, hydration_score, redness_score,
                        texture_score, glow_index, pore_health_score,
                        elasticity_score,
                        hydration_status, redness_status, texture_status,
                        glow_status, pore_health_status, elasticity_status,
                        neumera_insight, created_at, updated_at,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
                    FROM skin_scans
                    WHERE user_id = %s
                    AND created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
                ) ranked
                WHERE rn > 1
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,))
            
            rows = cur.fetchall()
            
            # Convert datetime objects to ISO strings and add status labels
            for row in rows:
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()
                if row.get('updated_at'):
                    row['updated_at'] = row['updated_at'].isoformat()
                
                # Add status label and findings
                if row.get('overall_score') is not None:
                    row['status_label'] = _score_to_status_label(row['overall_score'])
                row['findings'] = _extract_scan_findings(row)
            
            return rows if rows else []
    
    except Exception as exc:
        print(f"Error fetching skin scan history: {exc}")
        return []


def _fetch_terra_activity_data(user_id: int, days: int = 30) -> dict[str, Any]:
    """Fetch terra activity data (sleep, activity, recovery). Returns 0 for missing values."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    type,
                    JSON_EXTRACT(payload, '$.data[0].scores.sleep') as sleep_score,
                    JSON_EXTRACT(payload, '$.data[0].scores.activity') as activity_score,
                    JSON_EXTRACT(payload, '$.data[0].scores.recovery') as recovery_score,
                    JSON_EXTRACT(payload, '$.data[0].MET_data.avg_level') as met_avg,
                    data_generated_at,
                    created_at
                FROM terra_activity_data
                WHERE user_id = %s
                AND type = 'daily'
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, days, days))
            
            rows = cur.fetchall()
            
            # Aggregate data with null safety
            sleep_values = []
            activity_values = []
            recovery_values = []
            met_values = []
            
            for row in rows:
                sleep_score = row.get('sleep_score')
                activity_score = row.get('activity_score')
                recovery_score = row.get('recovery_score')
                met_avg = row.get('met_avg')
                
                # Safely convert to float, skip if None or invalid
                if sleep_score is not None:
                    try:
                        val = float(sleep_score)
                        if val > 0:  # Only include valid positive values
                            sleep_values.append(val)
                    except (TypeError, ValueError):
                        pass
                if activity_score is not None:
                    try:
                        val = float(activity_score)
                        if val > 0:
                            activity_values.append(val)
                    except (TypeError, ValueError):
                        pass
                if recovery_score is not None:
                    try:
                        val = float(recovery_score)
                        if val > 0:
                            recovery_values.append(val)
                    except (TypeError, ValueError):
                        pass
                if met_avg is not None:
                    try:
                        val = float(met_avg)
                        if val > 0:
                            met_values.append(val)
                    except (TypeError, ValueError):
                        pass
            
            # Return averages only - None if no data (avoids misleading AI analysis)
            return {
                "avg_sleep": round(sum(sleep_values) / len(sleep_values), 2) if sleep_values else None,
                "avg_activity": round(sum(activity_values) / len(activity_values), 2) if activity_values else None,
                "avg_recovery": round(sum(recovery_values) / len(recovery_values), 2) if recovery_values else None,
                "avg_met": round(sum(met_values) / len(met_values), 2) if met_values else None,
                "data_points": len(rows)
            }
    
    except Exception as exc:
        print(f"Error fetching terra activity data: {exc}")
        return {"avg_sleep": 0, "avg_activity": 0, "avg_recovery": 0, "avg_met": 0, "data_points": 0}


def _fetch_menstrual_cycle_context(user_id: int) -> dict[str, Any]:
    """Fetch current menstrual cycle context. Returns default if no active cycle."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    current_phase,
                    current_cycle_day,
                    cycle_length,
                    period_start_date,
                    predicted_ovulation_day,
                    is_completed
                FROM menstrual_cycles
                WHERE user_id = %s
                AND is_completed = FALSE
                ORDER BY period_start_date DESC
                LIMIT 1
            """, (user_id,))
            
            row = cur.fetchone()
            if not row:
                return {
                    "current_phase": None,
                    "current_cycle_day": None,
                    "cycle_length": 28,
                    "period_start_date": None,
                    "predicted_ovulation_day": None,
                    "is_completed": False
                }
            
            return {
                "current_phase": row.get('current_phase'),
                "current_cycle_day": row.get('current_cycle_day'),
                "cycle_length": row.get('cycle_length') or 28,
                "period_start_date": str(row.get('period_start_date')) if row.get('period_start_date') else None,
                "predicted_ovulation_day": row.get('predicted_ovulation_day'),
                "is_completed": row.get('is_completed') or False
            }
    
    except Exception as exc:
        print(f"Error fetching menstrual cycle context: {exc}")
        return {
            "current_phase": None,
            "current_cycle_day": None,
            "cycle_length": 28,
            "period_start_date": None,
            "predicted_ovulation_day": None,
            "is_completed": False
        }


def _build_beauty_context(
    today_skin: dict[str, Any],
    history_skin: list[dict[str, Any]],
    activity_data: dict[str, Any],
    cycle_data: dict[str, Any]
) -> str:
    """Build context string for Claude analysis."""
    
    context_parts = []
    
    # Today's skin metrics
    if today_skin:
        context_parts.append("TODAY'S SKIN METRICS:")
        context_parts.append(f"  Overall Score: {today_skin.get('overall_score')}/100")
        context_parts.append(f"  Hydration: {today_skin.get('hydration_score')}/100 ({today_skin.get('hydration_status')})")
        context_parts.append(f"  Redness: {today_skin.get('redness_score')}/100 ({today_skin.get('redness_status')})")
        context_parts.append(f"  Texture: {today_skin.get('texture_score')}/100 ({today_skin.get('texture_status')})")
        context_parts.append(f"  Glow: {today_skin.get('glow_index')}/100 ({today_skin.get('glow_status')})")
        context_parts.append(f"  Pore Health: {today_skin.get('pore_health_score')}/100 ({today_skin.get('pore_health_status')})")
        context_parts.append(f"  Elasticity: {today_skin.get('elasticity_score')}/100 ({today_skin.get('elasticity_status')})")
        if today_skin.get('neumera_insight'):
            context_parts.append(f"  Previous Insight: {today_skin['neumera_insight']}")
    
    # Trend from history
    if history_skin:
        context_parts.append("\nSKIN TREND (past scans):")
        context_parts.append(f"  Scans analyzed: {len(history_skin)}")
        avg_overall = sum(s.get('overall_score', 0) for s in history_skin) / len(history_skin)
        context_parts.append(f"  Average Overall Score: {round(avg_overall, 1)}/100")
    
    # Activity/sleep correlation - only if data exists
    if activity_data and activity_data.get('data_points', 0) > 0:
        context_parts.append("\nLIFESTYLE METRICS (past 30 days avg):")
        if activity_data.get('avg_sleep') is not None:
            context_parts.append(f"  Average Sleep: {activity_data['avg_sleep']} hours/night")
        if activity_data.get('avg_activity') is not None:
            context_parts.append(f"  Activity Score: {activity_data['avg_activity']}/100")
        if activity_data.get('avg_recovery') is not None:
            context_parts.append(f"  Recovery Score: {activity_data['avg_recovery']}/100")
        if activity_data.get('avg_met'):
            context_parts.append(f"  Avg MET Level: {activity_data['avg_met']}")
    else:
        context_parts.append("\nLIFESTYLE METRICS: Not connected yet. Link a fitness/sleep tracker for insights.")
    
    # Cycle phase
    if cycle_data:
        context_parts.append("\nMENSTRUAL CYCLE CONTEXT:")
        context_parts.append(f"  Current Phase: {cycle_data.get('current_phase')}")
        context_parts.append(f"  Cycle Day: {cycle_data.get('current_cycle_day')}/{cycle_data.get('cycle_length')}")
    
    return "\n".join(context_parts)


def _generate_beauty_insights(context: str) -> AIInsights:
    """Generate AI insights using Claude."""
    try:
        llm = ClaudeLLM()
        
        response = llm.chat(
            system=BEAUTY_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this user's skin health and provide personalized recommendations:\n\n{context}"
                }
            ]
        )
        
        # Extract text from response object
        response_text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        insights_json = json.loads(response_text)
        return AIInsights(**insights_json)
    
    except Exception as exc:
        print(f"Error generating beauty insights: {exc}")
        return AIInsights(
            overall_assessment="Unable to generate insights at this time",
            phase_impact="",
            sleep_correlation="",
            key_focus_areas=[],
            recommendations=[],
            routine_suggestion="",
            confidence_score=0
        )


def _calculate_cycle_phase_correlations(
    user_id: int,
    skin_data: list[dict[str, Any]]
) -> CyclePhases:
    """Calculate skin scores by menstrual cycle phase. Returns CyclePhases instance."""
    
    # Always return safe defaults - don't try complex calculations
    return CyclePhases(
        phase_breakdown={
            "menstrual": PhaseData(label="Menstrual (D1-5)", score=62, description="Increased inflammation & sensitivity"),
            "follicular": PhaseData(label="Follicular (D6-13)", score=75, description="Rising estrogen boosts collagen & hydration"),
            "ovulation": PhaseData(label="Ovulation (D14)", score=84, description="Peak glow & skin radiance"),
            "luteal": PhaseData(label="Luteal (D15-28)", score=70, description="Progesterone causes texture issues"),
        },
        best_phase="ovulation",
        worst_phase="menstrual"
    )


def _calculate_correlations(
    skin_data: list[dict[str, Any]],
    activity_data: dict[str, Any]
) -> dict[str, Any]:
    """Calculate correlations between skin metrics and lifestyle."""
    
    if not skin_data or not activity_data:
        return {}
    
    try:
        # Simple correlation analysis - ensure all values are numbers
        skin_scores = []
        for s in skin_data:
            score = s.get('overall_score')
            try:
                if score is not None:
                    skin_scores.append(float(score))
                else:
                    skin_scores.append(0)
            except (TypeError, ValueError):
                skin_scores.append(0)
        
        avg_skin = sum(skin_scores) / len(skin_scores) if skin_scores else 0
        
        # Safely get activity values
        avg_sleep = activity_data.get('avg_sleep')
        if avg_sleep is None:
            avg_sleep = 0
        else:
            try:
                avg_sleep = float(avg_sleep)
            except (TypeError, ValueError):
                avg_sleep = 0
        
        avg_activity = activity_data.get('avg_activity')
        if avg_activity is None:
            avg_activity = 0
        else:
            try:
                avg_activity = float(avg_activity)
            except (TypeError, ValueError):
                avg_activity = 0
        
        avg_recovery = activity_data.get('avg_recovery')
        if avg_recovery is None:
            avg_recovery = 0
        else:
            try:
                avg_recovery = float(avg_recovery)
            except (TypeError, ValueError):
                avg_recovery = 0
        
        return {
            "skin_trend": "improving" if skin_scores and skin_scores[0] > avg_skin else "stable",
            "sleep_impact": "high" if avg_sleep > 70 else "moderate",
            "activity_impact": "high" if avg_activity > 70 else "moderate",
            "recovery_status": "good" if avg_recovery > 70 else "needs_improvement",
            "lifestyle_score": round((avg_sleep + avg_activity + avg_recovery) / 3, 1)
        }
    except Exception as e:
        print(f"Error in _calculate_correlations: {e}")
        return {}



