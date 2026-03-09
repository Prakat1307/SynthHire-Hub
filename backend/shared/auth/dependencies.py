
from fastapi import Header, HTTPException, Query
from typing import Optional
from .jwt_handler import JWTHandler
import os

_jwt_handler: Optional[JWTHandler] = None

def init_jwt_handler(public_key_path: str, private_key_path: str = None, algorithm: str = "RS256"):
    global _jwt_handler
    _jwt_handler = JWTHandler(public_key_path, private_key_path, algorithm)
    return _jwt_handler

def get_jwt_handler() -> JWTHandler:
    if _jwt_handler is None:
        raise RuntimeError("JWT handler not initialized. Call init_jwt_handler() first.")
    return _jwt_handler

async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_internal_service: Optional[str] = Header(None, alias="X-Internal-Service")
) -> str:

    if x_internal_service == "true" and x_user_id:
        return x_user_id
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
        
    handler = get_jwt_handler()
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
    token = authorization.replace("Bearer ", "")
    payload = handler.validate_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user ID")
        
    return user_id

async def verify_ws_token(token: str) -> Optional[str]:

    handler = get_jwt_handler()
    payload = handler.validate_access_token(token)
    if payload:
        return payload.get("sub")
    return None

async def get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:

    if not authorization or not authorization.startswith("Bearer "):
        return None
        
    handler = get_jwt_handler()
    token = authorization.replace("Bearer ", "")
    payload = handler.validate_access_token(token)
    
    if payload:
        return payload.get("sub")
    return None