from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.api_key:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid auth header")
            token = auth_header.replace("Bearer ", "")
            if token != settings.api_key:
                raise HTTPException(status_code=401, detail="Invalid API key")
        return await call_next(request)