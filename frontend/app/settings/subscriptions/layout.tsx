"use client"

import type React from "react"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import RSSiaHeader from "@/components/rssia-header"
import { useAuth } from "@/contexts/auth-context"

export default function SettingsSubscriptionsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, isLoading, logout } = useAuth()
  const router = useRouter()

  const handleLogin = () => {
    // 订阅管理页面不处理登录，直接跳转到主页
    router.push("/")
  }

  const handleLogout = () => {
    console.log("Settings page logout triggered")
    logout()
    router.push("/")
  }

  useEffect(() => {
    // 只有在加载完成且未认证时才跳转
    if (!isLoading && !isAuthenticated) {
      console.log("未登录，跳转到主页")
      router.push("/")
    }
  }, [isAuthenticated, isLoading, router])

  // 如果正在加载认证状态，显示加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  // 如果未认证，返回空（将会跳转）
  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
              <RSSiaHeader isLoggedIn={isAuthenticated} onLogin={handleLogin} onLogout={handleLogout} showFilterTags={false} />
      <main className="flex-grow container mx-auto px-4 py-8">{children}</main>
    </div>
  )
}
