"use client"

import { useState, useEffect, useRef } from "react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface TestDropdownProps {
  onLogout: () => void
}

export default function TestDropdown({ onLogout }: TestDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { setTheme, resolvedTheme } = useTheme()

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleToggle = () => {
    console.log("Toggle clicked, current state:", isOpen)
    setIsOpen(!isOpen)
  }

  const handleThemeToggle = () => {
    console.log("Theme toggle clicked")
    if (!mounted) return

    // 使用 next-themes 的 setTheme 方法
    setTheme(resolvedTheme === "dark" ? "light" : "dark")
    setIsOpen(false) // 关闭弹窗
  }

  const handleLogout = () => {
    console.log("Logout clicked")
    setIsOpen(false) // 关闭弹窗
    onLogout()
  }

  const handleSettingsClick = () => {
    console.log("Settings clicked")
    setIsOpen(false) // 关闭弹窗
    window.location.href = "/settings/subscriptions"
  }

  // 点击外部区域关闭弹窗
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen])

  // ESC键关闭弹窗
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscapeKey)
    }

    return () => {
      document.removeEventListener("keydown", handleEscapeKey)
    }
  }, [isOpen])

  return (
    <div className="relative" ref={dropdownRef}>
      <Button variant="ghost" className="relative h-9 w-9 rounded-full p-0" onClick={handleToggle}>
        <Avatar className="h-9 w-9">
          <AvatarImage src="/placeholder.svg?height=36&width=36" alt="User Avatar" />
          <AvatarFallback>用户</AvatarFallback>
        </Avatar>
      </Button>

      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          {/* 弹窗内容 */}
          <div className="absolute right-0 top-full mt-2 w-56 rounded-md border bg-popover p-1 text-popover-foreground shadow-md z-50">
            <div className="px-2 py-1.5 text-sm font-semibold">Username (占位符)</div>
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
