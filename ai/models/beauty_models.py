from pydantic import BaseModel

class BeautyRequest(BaseModel):
    user_id: int
    days: int = 30
    include_correlations: bool = True

class BeautyResponse(BaseModel):
    today: dict
    history: list
    correlations: dict
    ai_insights: dict