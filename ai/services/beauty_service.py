import json
from datetime import datetime, timezone
from typing import Any, Optional

from ai.config import settings
from ai.models.beauty_models import BeautyRequest, BeautyResponse
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
        
        # Build correlations if requested
        correlations = {}
        if request.include_correlations:
            correlations = _calculate_correlations(
                skin_data=history_skin,
                activity_data=activity_data
            )
        
        return BeautyResponse(
            today=today_skin or {},
            history=history_skin or [],
            correlations=correlations,
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
            
            return _format_skin_scan_row(row)
    
    except Exception as exc:
        print(f"Error fetching latest skin scan: {exc}")
        return {}


def _fetch_skin_scan_history(user_id: int, days: int = 30) -> list[dict[str, Any]]:
    """Fetch skin scan history for the past N days."""
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
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, days, days))
            
            rows = cur.fetchall()
            return [_format_skin_scan_row(row) for row in rows]
    
    except Exception as exc:
        print(f"Error fetching skin scan history: {exc}")
        return []


def _fetch_terra_activity_data(user_id: int, days: int = 30) -> dict[str, Any]:
    """Fetch terra activity data (sleep, activity, recovery)."""
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
            
            # Aggregate data
            sleep_values = []
            activity_values = []
            recovery_values = []
            met_values = []
            
            for row in rows:
                if row[1]:  # sleep_score
                    sleep_values.append(float(row[1]))
                if row[2]:  # activity_score
                    activity_values.append(float(row[2]))
                if row[3]:  # recovery_score
                    recovery_values.append(float(row[3]))
                if row[4]:  # met_avg
                    met_values.append(float(row[4]))
            
            return {
                "avg_sleep": round(sum(sleep_values) / len(sleep_values), 2) if sleep_values else None,
                "avg_activity": round(sum(activity_values) / len(activity_values), 2) if activity_values else None,
                "avg_recovery": round(sum(recovery_values) / len(recovery_values), 2) if recovery_values else None,
                "avg_met": round(sum(met_values) / len(met_values), 2) if met_values else None,
                "data_points": len(rows)
            }
    
    except Exception as exc:
        print(f"Error fetching terra activity data: {exc}")
        return {}


def _fetch_menstrual_cycle_context(user_id: int) -> dict[str, Any]:
    """Fetch current menstrual cycle context."""
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
                return {}
            
            return {
                "current_phase": row[0],
                "current_cycle_day": row[1],
                "cycle_length": row[2],
                "period_start_date": str(row[3]) if row[3] else None,
                "predicted_ovulation_day": row[4],
                "is_completed": row[5]
            }
    
    except Exception as exc:
        print(f"Error fetching menstrual cycle context: {exc}")
        return {}


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
    
    # Activity/sleep correlation
    if activity_data:
        context_parts.append("\nLIFESTYLE METRICS (past 30 days avg):")
        if activity_data.get('avg_sleep'):
            context_parts.append(f"  Sleep Quality Score: {activity_data['avg_sleep']}/100")
        if activity_data.get('avg_activity'):
            context_parts.append(f"  Activity Score: {activity_data['avg_activity']}/100")
        if activity_data.get('avg_recovery'):
            context_parts.append(f"  Recovery Score: {activity_data['avg_recovery']}/100")
        if activity_data.get('avg_met'):
            context_parts.append(f"  Avg MET Level: {activity_data['avg_met']}")
    
    # Cycle phase
    if cycle_data:
        context_parts.append("\nMENSTRUAL CYCLE CONTEXT:")
        context_parts.append(f"  Current Phase: {cycle_data.get('current_phase')}")
        context_parts.append(f"  Cycle Day: {cycle_data.get('current_cycle_day')}/{cycle_data.get('cycle_length')}")
    
    return "\n".join(context_parts)


def _generate_beauty_insights(context: str) -> str:
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
        return insights_json
    
    except Exception as exc:
        print(f"Error generating beauty insights: {exc}")
        return {
            "overall_assessment": "Unable to generate insights at this time",
            "phase_impact": "",
            "sleep_correlation": "",
            "key_focus_areas": [],
            "recommendations": [],
            "routine_suggestion": "",
            "confidence_score": 0
        }


def _calculate_correlations(
    skin_data: list[dict[str, Any]],
    activity_data: dict[str, Any]
) -> dict[str, Any]:
    """Calculate correlations between skin metrics and lifestyle."""
    
    if not skin_data or not activity_data:
        return {}
    
    # Simple correlation analysis
    skin_scores = [s.get('overall_score', 0) for s in skin_data]
    avg_skin = sum(skin_scores) / len(skin_scores) if skin_scores else 0
    
    return {
        "skin_trend": "improving" if skin_scores and skin_scores[0] > avg_skin else "stable",
        "sleep_impact": "high" if activity_data.get('avg_sleep', 0) > 70 else "moderate",
        "activity_impact": "high" if activity_data.get('avg_activity', 0) > 70 else "moderate",
        "recovery_status": "good" if activity_data.get('avg_recovery', 0) > 70 else "needs_improvement",
        "lifestyle_score": round(
            (activity_data.get('avg_sleep', 0) + 
             activity_data.get('avg_activity', 0) + 
             activity_data.get('avg_recovery', 0)) / 3, 1
        ) if activity_data else 0
    }


def _format_skin_scan_row(row: tuple) -> dict[str, Any]:
    """Format a skin scan database row into a dictionary."""
    return {
        "id": row[0],
        "user_id": row[1],
        "image_path": row[2],
        "overall_score": row[3],
        "hydration_score": row[4],
        "redness_score": row[5],
        "texture_score": row[6],
        "glow_index": row[7],
        "pore_health_score": row[8],
        "elasticity_score": row[9],
        "hydration_status": row[10],
        "redness_status": row[11],
        "texture_status": row[12],
        "glow_status": row[13],
        "pore_health_status": row[14],
        "elasticity_status": row[15],
        "neumera_insight": row[16],
        "created_at": str(row[17]) if row[17] else None,
        "updated_at": str(row[18]) if row[18] else None
    }
