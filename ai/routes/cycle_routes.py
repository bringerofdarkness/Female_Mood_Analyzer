"""FastAPI routes for Cycle & Fertility endpoint."""

import logging
from fastapi import APIRouter, HTTPException

from ai.models.cycle_models import CycleRequest, CycleOverviewResponse
from ai.services.cycle_service import get_cycle_overview

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post(
    "/cycle-overview",
    response_model=CycleOverviewResponse,
    summary="Get Cycle & Fertility Overview",
    description="Analyze current menstrual cycle, calculate fertile window, and provide AI-powered insights"
)
async def cycle_overview(request: CycleRequest) -> CycleOverviewResponse:
    """
    Get comprehensive cycle and fertility overview for a user.
    
    Provides:
    - Current cycle metrics (day, phase, dates)
    - Fertile window calculation
    - Optional BBT (basal body temperature) analysis
    - Historical cycle patterns
    - AI-powered personalized insights
    
    Args:
        request: CycleRequest containing user_id, mode (standard/tracking/premium), and include_bbt flag
        
    Returns:
        CycleOverviewResponse with metrics, fertile window, analysis, and insights
        
    Raises:
        HTTPException 404: If user has no active cycle
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(f"Processing cycle overview for user {request.user_id}")
        result = get_cycle_overview(request)
        logger.info(f"Successfully returned cycle overview for user {request.user_id}")
        return result
    
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(
            status_code=404,
            detail=str(ve)
        )
    
    except Exception as exc:
        logger.error(f"Error processing cycle overview: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate cycle analysis. Please try again later."
        )
