"""
Bot control routes for starting, stopping, and monitoring the LinkedIn bot.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import User
from backend.api.auth import get_current_user
from backend.services.bot_service import bot_service

router = APIRouter(prefix="/bot", tags=["Bot Control"])


class BotStatus(BaseModel):
    is_running: bool
    current_action: Optional[str] = None
    jobs_applied_today: int = 0
    jobs_applied_total: int = 0
    current_job: Optional[dict] = None
    started_at: Optional[str] = None
    last_activity: Optional[str] = None


@router.post("/start")
async def start_bot(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start the LinkedIn bot for the current user."""
    state = bot_service.get_state(current_user.id)
    
    if state["is_running"]:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    # Check if user has LinkedIn credentials
    if not current_user.linkedin_credentials or not current_user.linkedin_credentials.get("email"):
        raise HTTPException(
            status_code=400, 
            detail="LinkedIn credentials not configured. Please complete onboarding."
        )
    
    # Start bot using service
    success = await bot_service.start_bot(current_user)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start bot")
    
    return {"message": "Bot started", "status": "running"}


@router.post("/stop")
async def stop_bot(current_user: User = Depends(get_current_user)):
    """Stop the LinkedIn bot for the current user."""
    state = bot_service.get_state(current_user.id)
    
    if not state["is_running"]:
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    bot_service.stop_bot(current_user.id)
    
    return {"message": "Bot stop requested", "status": "stopping"}


@router.get("/status", response_model=BotStatus)
async def get_bot_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current bot status for the user."""
    state = bot_service.get_state(current_user.id)
    
    return BotStatus(
        is_running=state["is_running"],
        current_action=state["current_action"],
        jobs_applied_today=state["jobs_applied_today"],
        jobs_applied_total=current_user.total_applications or 0,
        current_job=state["current_job"],
        started_at=state["started_at"],
        last_activity=state["last_activity"]
    )


@router.get("/logs")
async def get_bot_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """Get bot execution logs for the current user."""
    return bot_service.get_logs(current_user.id, limit)


@router.delete("/logs")
async def clear_bot_logs(current_user: User = Depends(get_current_user)):
    """Clear bot logs for the current user."""
    state = bot_service.get_state(current_user.id)
    state["logs"] = []
    return {"message": "Logs cleared"}
