"""FastAPI routes for Cycle & Fertility endpoint."""

import logging
from fastapi import APIRouter, HTTPException, Query

from ai.models.cycle_models import CycleOverviewResponse
from ai.services.cycle_service import get_cycle_overview

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get(
    "/cycle-overview",
    response_model=CycleOverviewResponse,
    summary="Get Cycle & Fertility Overview",
    description="Analyze current menstrual cycle, calculate fertile window, and provide AI-powered insights"
)
async def cycle_overview(
    user_id: int = Query(..., gt=0, description="User ID (must be positive integer)"),
    mode: str = Query("standard", regex="^(standard|tracking|premium)$", description="Cycle tracking mode"),
    include_bbt: bool = Query(False, description="Include BBT (Basal Body Temperature) analysis")
) -> CycleOverviewResponse:
    """
    Get comprehensive cycle and fertility overview for a user.
    
    Provides:
    - Current cycle metrics (day, phase, dates)
    - Fertile window calculation
    - Optional BBT (basal body temperature) analysis
    - Historical cycle patterns
    - AI-powered personalized insights
    
    Query Parameters:
        user_id: User ID (required, must be > 0)
        mode: Tracking mode - 'standard' (default), 'tracking', or 'premium'
        include_bbt: Include BBT analysis (default: false)
        
    Returns:
        CycleOverviewResponse with metrics, fertile window, analysis, and insights
        
    Raises:
        HTTPException 404: If user not found or has no active cycle
        HTTPException 500: If analysis fails
        
    Example:
        GET /api/v1/cycle-overview?user_id=2&mode=standard&include_bbt=false
    """
    try:
        logger.info(f"Processing cycle overview for user {user_id}, mode={mode}")
        result = get_cycle_overview(user_id, mode, include_bbt)
        logger.info(f"Successfully returned cycle overview for user {user_id}")
        return result
    
    except ValueError as ve:
        logger.warning(f"Validation error for user {user_id}: {ve}")
        raise HTTPException(
            status_code=404,
            detail=str(ve)
        )
    
    except Exception as exc:
        logger.error(f"Error processing cycle overview for user {user_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate cycle analysis. Please try again later."
        )
