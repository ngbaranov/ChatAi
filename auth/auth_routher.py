from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import Response
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from auth.service.token_refresh import create_refresh_token, SECRET_KEY, ALGORITHM
from database.db_depends import get_db
from dao.dao import UserDAO
from auth.service.authenticate import authenticate_user
from auth.service.token_jvt import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=["auth/templates", "app/templates", "admin_panel/templates"])
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")





@router.get("/reg")
async def read_item(request: Request):
    title = "Главная страница"
    return templates.TemplateResponse("reg.html", {"request": request, "title": title})


@router.post("/forms")
async def create_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    username: str = Form(),
    password: str = Form()

):
    """Регистрация (аутентификация нового пользователя)"""

    # Проверяем, что пользователь с таким именем уже существует
    user = await UserDAO.get_by_field(db, username=username)

    if user:
        answer = "Пользователь с таким именем уже существует"
        return templates.TemplateResponse(request=request, name="forms.html", context={"answer": answer})
    # Хешируем пароль
    password = bcrypt_context.hash(password)
    # Добавляем нового пользователя в базу
    new_user = await UserDAO.add(db, username=username, password=password)
    # Генерируем JWT токен
    new_token = await create_access_token(new_user.username, new_user.id, new_user.is_admin,
                                          expires_delta=timedelta(minutes=20))
    refresh_token = await create_refresh_token(new_user.id, expires_delta=timedelta(days=30))

    # Перенаправляем пользователя на главную страницу
    response = RedirectResponse(url="/", status_code=302)

    # Копируем куки из response в redirect_response
    response.set_cookie(key='access_token', value=new_token, httponly=True, max_age=20 * 60)
    response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, max_age=30 * 24 * 60 * 60)



    return response

@router.get("/login")
async def read_item(request: Request):
    title = "Авторизация"
    return templates.TemplateResponse("login.html", {"request": request, "title": title})


@router.post('/token')
async def login(response: Response, request: Request, db: Annotated[AsyncSession, Depends(get_db)], form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Аутентификация пользователя и установка токена в Set-Cookie"""
    # Аутентификация пользователя
    user = await authenticate_user(db, form_data.username, form_data.password)
    #Формируем токен
    access_token = await create_access_token(user.username, user.id, user.is_admin, expires_delta=timedelta(minutes=20))
    refresh_token = await create_refresh_token(user.id, expires_delta=timedelta(days=30))
    #Установка токена в cookie
    response.set_cookie(key='access_token', value=access_token, httponly=True, max_age=20 * 60)
    response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, max_age=30 * 24 * 60 * 60)


    redirect_response = RedirectResponse(url="/", status_code=302)

    # Копируем куки из response в redirect_response
    for key, value in response.headers.items():
        if key.lower() == "set-cookie":
            redirect_response.headers.append(key, value)

    return redirect_response


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: Annotated[AsyncSession, Depends(get_db)]):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = int(payload.get("sub"))
    user = await UserDAO.get_by_field(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = await create_access_token(
        user.username, user.id, user.is_admin, expires_delta=timedelta(minutes=20)
    )

    response.set_cookie("access_token", new_access_token, httponly=True, max_age=20*60)
    return {"access_token": new_access_token}