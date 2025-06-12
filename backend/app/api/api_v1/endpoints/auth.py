"""
用户认证端点
提供用户登录、注册、登出等认证功能
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel
from loguru import logger

from app.core.config import settings
from app.services.user_service import user_service, User

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]


class UserResponse(BaseModel):
    """用户信息响应模型"""
    user_id: int
    username: str
    role: str
    subscription_count: int
    created_at: str


def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """获取当前用户（依赖注入）"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息"
        )
    
    # 解析Bearer token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("无效的认证方案")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证格式"
        )
    
    # 验证token
    user = user_service.get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    return user


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(request: LoginRequest) -> TokenResponse:
    """
    用户登录接口
    支持用户名或邮箱登录
    """
    try:
        # 用户认证
        user = user_service.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        return TokenResponse(
            access_token=user.access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "user_id": user.user_id,
                "username": user.username,
                "role": "user",  # 默认角色
                "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误"
        )


@router.post("/register", summary="用户注册")
async def register(request: RegisterRequest) -> Dict[str, Any]:
    """
    用户注册接口
    创建新用户账号
    """
    try:
        # 基本验证
        if len(request.username) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名至少2个字符"
            )
        
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码至少6个字符"
            )
        
        # 创建用户（这里暂时使用用户名作为邮箱，实际应该分开）
        email = f"{request.username}@example.com"  # 临时邮箱格式
        user = user_service.create_user(request.username, email, request.password)
        
        logger.info(f"新用户注册成功: {request.username} (ID: {user.user_id})")
        
        return {
            "message": "注册成功",
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
        }
        
    except ValueError as e:
        # 用户输入错误（用户名已存在等）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误"
        )


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """
    用户登出接口
    使当前用户的token失效
    """
    try:
        if current_user.access_token:
            user_service.invalidate_token(current_user.access_token)
        
        logger.info(f"用户登出: {current_user.username} (ID: {current_user.user_id})")
        
        return {
            "message": "登出成功"
        }
    except Exception as e:
        logger.error(f"登出失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出过程中发生错误"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    获取当前用户信息
    需要有效的认证token
    """
    try:
        # TODO: 获取用户的订阅数量
        subscription_count = 0  # 暂时返回0
        
        return UserResponse(
            user_id=current_user.user_id,
            username=current_user.username,
            role="user",  # 默认角色
            subscription_count=subscription_count,
            created_at=current_user.created_at.isoformat() if current_user.created_at else datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息过程中发生错误"
        ) 