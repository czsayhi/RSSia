"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

// 用户信息类型
export interface User {
  user_id: number
  username: string
  email?: string
  role?: string
  avatar?: string
  created_at?: string
}

// 认证状态类型
interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
}

// 认证Context类型
interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

// 创建Context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token存储键名
const TOKEN_KEY = 'rss_auth_token'
const USER_KEY = 'rss_user_info'

// AuthProvider组件
interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  })

  // 初始化认证状态
  useEffect(() => {
    initializeAuth()
  }, [])

  // 从localStorage初始化认证状态
  const initializeAuth = async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY)
      const userStr = localStorage.getItem(USER_KEY)
      
      if (token && userStr) {
        const user = JSON.parse(userStr)
        setAuthState({
          user,
          token,
          isLoading: false,
          isAuthenticated: true,
        })
        
        // 验证token是否仍然有效
        await validateToken(token)
      } else {
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
        }))
      }
    } catch (error) {
      console.error('初始化认证状态失败:', error)
      clearAuthData()
    }
  }

  // 验证token有效性
  const validateToken = async (token: string) => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Token验证失败')
      }
      
      const userData = await response.json()
      updateAuthState(userData, token)
    } catch (error) {
      console.error('Token验证失败:', error)
      clearAuthData()
    }
  }

  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '登录失败')
      }

      const data = await response.json()
      
      // 处理后端返回的数据结构
      const user: User = {
        user_id: data.user_info.user_id,
        username: data.user_info.username,
        email: `${data.user_info.username}@example.com`, // 生成临时邮箱
        role: data.user_info.role,
        created_at: data.user_info.created_at,
      }
      
      const token = data.access_token
      
      // 保存认证信息
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      
      updateAuthState(user, token)
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  // 注册
  const register = async (username: string, email: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '注册失败')
      }

      const data = await response.json()
      
      // 注册成功，返回结果但不自动登录
      return data
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  // 登出
  const logout = async () => {
    try {
      // 调用后端登出接口
      if (authState.token) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authState.token}`,
          },
        })
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuthData()
    }
  }

  // 刷新用户信息
  const refreshUser = async () => {
    if (!authState.token) return
    
    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${authState.token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('获取用户信息失败')
      }
      
      const userData = await response.json()
      updateAuthState(userData, authState.token)
    } catch (error) {
      console.error('刷新用户信息失败:', error)
      clearAuthData()
    }
  }

  // 更新认证状态
  const updateAuthState = (user: User, token: string) => {
    setAuthState({
      user,
      token,
      isLoading: false,
      isAuthenticated: true,
    })
  }

  // 清除认证数据
  const clearAuthData = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setAuthState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    })
  }

  const contextValue: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    refreshUser,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

// 使用认证Context的Hook
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// 认证状态检查Hook
export function useRequireAuth() {
  const auth = useAuth()
  
  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      // 可以在这里处理未认证的情况，比如跳转到登录页
      console.warn('用户未认证')
    }
  }, [auth.isLoading, auth.isAuthenticated])
  
  return auth
} 