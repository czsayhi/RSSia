"""
用户认证端点
MVP阶段使用简化的本地Token认证
"""

from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from app.core.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(request: LoginRequest) -> TokenResponse:
    """
    用户登录接口
    MVP阶段使用简化认证，后期将集成完整的用户系统
    """
    try:
        # MVP阶段：简化认证逻辑
        # TODO: 后期替换为真实的用户验证
        if request.username == "admin" and request.password == "admin123":
            # 生成简单的token（实际应用中应使用JWT）
            token = f"token_{request.username}_{datetime.now().timestamp()}"
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_info={
                    "user_id": 1,
                    "username": request.username,
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误"
        )


@router.post("/register", summary="用户注册")
async def register(request: LoginRequest) -> Dict[str, Any]:
    """
    用户注册接口
    MVP阶段的简化注册功能
    """
    try:
        # MVP阶段：简化注册逻辑
        # TODO: 后期添加真实的用户注册逻辑
        logger.info(f"新用户注册: {request.username}")
        
        return {
            "message": "注册成功",
            "user_id": 1,
            "username": request.username,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误"
        )


@router.post("/logout", summary="用户登出")
async def logout() -> Dict[str, str]:
    """
    用户登出接口
    """
    return {
        "message": "登出成功"
    }


@router.get("/me", summary="获取当前用户信息")
async def get_current_user() -> Dict[str, Any]:
    """
    获取当前用户信息
    MVP阶段返回模拟数据
    """
    # TODO: 后期从Token中解析真实用户信息
    return {
        "user_id": 1,
        "username": "admin",
        "role": "admin",
        "subscription_count": 0,
        "created_at": datetime.now().isoformat()
    } 