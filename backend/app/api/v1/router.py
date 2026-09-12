from fastapi import APIRouter

from app.api.v1.endpoints.prompt_history import router as prompt_history_router

router = APIRouter()
router.include_router(prompt_history_router)
