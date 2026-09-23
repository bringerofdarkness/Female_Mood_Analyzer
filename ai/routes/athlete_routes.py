"""Athlete Performance API routes."""

from fastapi import APIRouter, Query

from ai.services.athlete_service import athlete_readiness

router = APIRouter()


@router.get("/athlete/readiness")
async def get_athlete_readiness(user_id: int = Query(..., description="User ID")):
    """
    **Athlete Performance Readiness Score**
    
    Calculates comprehensive readiness score based on:
    - HRV (Heart Rate Variability)
    - Sleep Quality
    - Recovery Status
    - Training Load
    - Menstrual Cycle Phase
    
    **Response (0-100):**
    - 85-100: Peak Ready
    - 70-84: Ready
    - 50-69: Adequate
    - 30-49: Fatigued
    - 0-29: Depleted
    
    **Includes:**
    - Real-time metrics from Terra API data
    - Fatigue risk alerts
    - Cycle-phase specific training recommendations
    - Next update timestamp
    """
    return athlete_readiness(user_id)
