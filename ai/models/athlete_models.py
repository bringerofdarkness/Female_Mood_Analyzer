"""Pydantic models for Athlete Performance API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HRVMetric(BaseModel):
    """Heart rate variability metric."""
    value: int = Field(..., ge=0, description="HRV value in milliseconds")
    unit: str = "ms"
    score: int = Field(..., ge=0, le=100, description="HRV converted to 0-100 score")
    trend: int = Field(..., description="Change from previous day (negative=declining)")
    status: str = Field(..., description="good | warning | poor")


class SleepMetric(BaseModel):
    """Sleep quality metric."""
    hours: float = Field(..., ge=0, le=24, description="Sleep duration in hours")
    score: int = Field(..., ge=0, le=100, description="Sleep quality score 0-100")
    status: str = Field(..., description="good | fair | poor")


class RecoveryMetric(BaseModel):
    """Recovery status metric."""
    score: int = Field(..., ge=0, le=100, description="Recovery score 0-100")
    status: str = Field(..., description="recovered | partial | depleted")


class TrainingLoadMetric(BaseModel):
    """Training load/strain metric."""
    value: float = Field(..., ge=0, description="Training load in AU (arbitrary units)")
    unit: str = "AU"
    status: str = Field(..., description="low | moderate | high")


class Metrics(BaseModel):
    """All performance metrics."""
    hrv: HRVMetric
    sleep: SleepMetric
    recovery: RecoveryMetric
    training_load: TrainingLoadMetric


class FatigueAlert(BaseModel):
    """Individual fatigue alert."""
    type: str = Field(..., description="overtraining_risk | recovery_deficit | cumulative_fatigue | sleep_debt")
    level: str = Field(..., description="low | moderate | high")
    message: str


class CycleInfo(BaseModel):
    """Cycle phase information."""
    phase: str = Field(..., description="menstrual | follicular | ovulatory | luteal | unknown")
    cycle_day: int = Field(..., ge=0, le=100, description="Current day of cycle (0 if unknown)")
    days_to_next_phase: int = Field(..., ge=0, le=100, description="Days until next phase")
    phase_boost: int = Field(..., ge=-15, le=15, description="Readiness score adjustment from phase")
    phase_description: str


class PhaseRecommendation(BaseModel):
    """Phase-based workout recommendation."""
    workout_type: str = Field(..., description="high_intensity | strength | endurance | recovery")
    intensity_level: str = Field(..., description="maximum | high | moderate | low")
    suggested_workouts: list[str]
    avoid: list[str]


class AthleteReadinessResponse(BaseModel):
    """Complete athlete performance readiness response."""
    date: str = Field(..., description="ISO date of readiness assessment")
    readiness_score: int = Field(..., ge=0, le=100, description="Overall readiness 0-100")
    readiness_level: str = Field(..., description="Peak Ready | Ready | Adequate | Fatigued | Depleted")
    readiness_message: str
    
    metrics: Metrics
    fatigue_alerts: list[FatigueAlert]
    cycle_info: CycleInfo
    recommendations: PhaseRecommendation
    
    next_update: str = Field(..., description="ISO timestamp of next scheduled update")


class AthleteReadinessRequest(BaseModel):
    """Request for athlete readiness."""
    user_id: int = Field(..., ge=1, description="User ID")
