"use client"

import { useState, useRef, useEffect } from "react"
import { useTheme } from "next-themes"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAuth } from "@/contexts/auth-context"

interface TestDropdownProps {
  onLogout: () => void
}

export default function TestDropdown({ onLogout }: TestDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme, resolvedTheme } = useTheme()
  const router = useRouter()
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  // 获取认证信息
  const { user } = useAuth()

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  const handleThemeToggle = () => {
    if (!mounted) return
    const newTheme = resolvedTheme === "dark" ? "light" : "dark"
    setTheme(newTheme)
    setIsOpen(false)
  }

  const handleSettingsClick = () => {
    router.push('/settings/subscriptions')
    setIsOpen(false)
  }

  const handleLogout = () => {
    onLogout()
    setIsOpen(false)
  }

  // 获取用户名显示文本
  const getUserDisplayName = () => {
    if (user?.username) {
      return user.username
    }
    return "用户"
  }

  // 获取用户头像缩写
  const getUserAvatarFallback = () => {
    if (user?.username) {
      return user.username.charAt(0).toUpperCase()
    }
    return "用"
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <Button variant="ghost" className="relative h-9 w-9 rounded-full p-0" onClick={handleToggle}>
        <Avatar className="h-9 w-9">
          <AvatarImage src={user?.avatar || "/placeholder.svg?height=36&width=36"} alt="User Avatar" />
          <AvatarFallback>{getUserAvatarFallback()}</AvatarFallback>
        </Avatar>
      </Button>

      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          {/* 弹窗内容 */}
          <div className="absolute right-0 top-full mt-2 w-56 rounded-md border bg-popover p-1 text-popover-foreground shadow-md z-50">
            <div className="px-2 py-1.5 text-sm font-semibold">{getUserDisplayName()}</div>
            <div className="-mx-1 my-1 h-px bg-muted"></div>
            <button
              className="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
              onClick={handleSettingsClick}
            >
              订阅配置
            </button>
            <button
              className="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
              onClick={handleThemeToggle}
            >
              {mounted ? `切换到 ${resolvedTheme === "dark" ? "浅色" : "深色"} 主题` : "切换主题"}
            </button>
            <div className="-mx-1 my-1 h-px bg-muted"></div>
            <button
              className="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
              onClick={handleLogout}
            >
              登出
            </button>
          </div>
        </>
      )}
    </div>
  )
}
