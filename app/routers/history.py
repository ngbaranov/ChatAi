from fastapi import Depends, Request, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.history_view import get_user_sessions
from database.db_depends import get_db
from settings import settings

router = APIRouter(prefix="/history", tags=["history"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def history(request: Request, db: AsyncSession = Depends(get_db)):

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("id"))
    except JWTError:
        raise HTTPException(401, "Invalid token")

    sessions = await get_user_sessions(user_id, db)
    return templates.TemplateResponse("history.html", {"request": request, "sessions": sessions})
