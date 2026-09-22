from fastapi import APIRouter, HTTPException

from ai.models.beauty_models import BeautyRequest, BeautyResponse
from ai.services.beauty_service import get_beauty_overview


router = APIRouter()


@router.post("/beauty-overview", response_model=BeautyResponse)
async def beauty_overview(request: BeautyRequest) -> BeautyResponse:
    """
    POST /api/beauty-overview
    
    Get beauty & radiance analysis for a user.
    
    Request body:
    {
        "user_id": 2,
        "days": 30,
        "include_correlations": true
    }
    
    Returns:
    {
        "today": { skin metrics for today },
        "history": [ past skin scans ],
        "correlations": { lifestyle-skin correlations },
        "ai_insights": { Claude-generated personalized insights }
    }
    """
    try:
        return get_beauty_overview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Beauty overview analysis failed: {exc}")
