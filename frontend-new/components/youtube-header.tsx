"use client"

import Link from "next/link"
import Image from "next/image"
import { Search, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { cn } from "@/lib/utils"
import SubscriptionAssistantCard from "./subscription-assistant-card"
import TestDropdown from "./test-dropdown"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

const filterButtonTags = [
  "全部",
  "音乐",
  "Podcast",
  "游戏",
  "直播中",
  "观光",
  "自然",
  "动作冒险游戏",
  "最新上传",
  "让你耳目一新",
  "烹饪",
  "科技",
  "新闻",
]

interface YoutubeHeaderProps {
  isLoggedIn: boolean
  onLogin: () => void
  onLogout: () => void
  showFilterTags?: boolean
}

function ThemeAwareLogo() {
  const logoHeight = 36
  const logoWidth = 140

  return (
    <>
      <Image
        src="/images/logo-light.png"
        alt="Logo"
        width={logoWidth}
        height={logoHeight}
        className="inline dark:hidden w-auto"
        style={{ height: `${logoHeight}px` }}
        priority
      />
      <Image
        src="/images/logo-dark.png"
        alt="Logo"
        width={logoWidth}
        height={logoHeight}
        className="hidden dark:inline w-auto"
        style={{ height: `${logoHeight}px` }}
        priority
      />
    </>
  )
}

// 模拟手动更新订阅的API调用
const updateSubscriptions = async (): Promise<{ success: boolean; message?: string }> => {
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 2000))

  // 模拟50%的概率达到更新上限
  const reachedLimit = Math.random() > 0.5

  if (reachedLimit) {
    return { success: false, message: "已达到今日更新上限" }
  } else {
    return { success: true }
  }
}

export default function YoutubeHeader({ isLoggedIn, onLogin, onLogout, showFilterTags = true }: YoutubeHeaderProps) {
  const [activeTag, setActiveTag] = useState("全部")
  const [isAssistantOpen, setIsAssistantOpen] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [updateLimitDialogOpen, setUpdateLimitDialogOpen] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)

  const openAssistant = () => setIsAssistantOpen(true)

  const handleUpdateContent = async () => {
    setIsUpdating(true)
    try {
      const result = await updateSubscriptions()
      if (!result.success) {
        setUpdateLimitDialogOpen(true)
      } else {
        // 成功更新，可以添加成功提示
        console.log("订阅内容更新成功")
      }
    } catch (error) {
      console.error("更新订阅内容失败:", error)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleGitHubClick = () => {
    window.open("https://github.com/czsayhi", "_blank", "noopener,noreferrer")
  }

  return (
    <>
      <header className="sticky top-0 z-40 flex flex-col bg-background/80 dark:bg-background/80 backdrop-blur-md">
        <div className="flex items-center justify-between h-14 px-4">
          <div className="flex items-center gap-1 sm:gap-4">
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-6 w-6" />
            </Button>
            <Link href="/" className="flex items-center" aria-label="Go to homepage">
              <ThemeAwareLogo />
            </Link>
          </div>
          {isLoggedIn && (
            <div className="flex-1 flex justify-center px-2 sm:px-4">
              <div className="w-full max-w-md lg:max-w-xl flex items-center">
                <div className="relative flex-grow">
                  <Input
                    type="search"
                    placeholder="搜索"
                    className="w-full rounded-l-full pl-10 pr-4 h-10 border-r-0 focus-visible:ring-offset-0 focus-visible:ring-0 focus-visible:border-input bg-background dark:bg-neutral-950 border-border dark:border-neutral-700"
                    readOnly
                  />
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                </div>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-10 w-16 rounded-r-full border-l-0 bg-muted dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 border-border dark:border-neutral-700"
                  aria-label="Search"
                  disabled
                >
                  <Search className="h-5 w-5" />
                </Button>
              </div>
            </div>
          )}
          <div className="flex items-center gap-3">
            {isLoggedIn && (
              <>
                {/* 更新内容按钮 - 黑色背景矩形按钮 */}
                <div className="relative">
                  <Button
                    onClick={handleUpdateContent}
                    disabled={isUpdating}
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                    className="bg-foreground text-background hover:bg-foreground/90 px-4 py-2 h-9 rounded-md text-sm font-medium"
                  >
                    {isUpdating ? "更新中..." : "更新内容"}
                  </Button>
                  {showTooltip && (
                    <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 bg-foreground text-background text-xs rounded-md whitespace-nowrap z-50">
                      重新获取订阅内容，并非刷新页面
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-foreground"></div>
                    </div>
                  )}
                </div>

                {/* 💡按钮 - 正方形边框按钮 */}
                <Button
                  variant="outline"
                  size="icon"
                  onClick={openAssistant}
                  aria-label="打开个人订阅助手"
                  className="h-9 w-9 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                >
                  <span className="text-lg" role="img" aria-label="灯泡">
                    💡
                  </span>
                </Button>

                {/* GitHub按钮 - 正方形边框按钮 */}
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleGitHubClick}
                  aria-label="查看 GitHub 仓库"
                  className="h-9 w-9 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                >
                  <Image src="/icons/github.png" alt="GitHub Icon" width={20} height={20} className="dark:invert" />
                </Button>
              </>
            )}
            {/* 用户头像/登录按钮 */}
            {isLoggedIn ? (
              <TestDropdown onLogout={onLogout} />
            ) : (
              <Button
                variant="ghost"
                onClick={onLogin}
                className="hover:bg-accent hover:text-accent-foreground px-3 py-2"
              >
                登录
              </Button>
            )}
          </div>
        </div>
        {isLoggedIn && showFilterTags && (
          <div className="flex items-center gap-2 px-4 py-3 overflow-x-auto whitespace-nowrap no-scrollbar">
            {filterButtonTags.map((tag) => (
              <Button
                key={tag}
                variant="outline"
                size="sm"
                onClick={() => setActiveTag(tag)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-150",
                  "border-transparent hover:bg-neutral-200 dark:hover:bg-neutral-700",
                  activeTag === tag
                    ? "bg-foreground text-background dark:bg-neutral-50 dark:text-neutral-900 hover:bg-foreground/90 dark:hover:bg-neutral-200"
                    : "bg-muted text-foreground dark:bg-neutral-800 dark:text-neutral-200",
                )}
              >
                {tag}
              </Button>
            ))}
          </div>
        )}
      </header>
      {isLoggedIn && <SubscriptionAssistantCard isOpen={isAssistantOpen} onClose={() => setIsAssistantOpen(false)} />}

      {/* 更新上限对话框 */}
      <AlertDialog open={updateLimitDialogOpen} onOpenChange={() => {}}>
        <AlertDialogContent onPointerDownOutside={(e) => e.preventDefault()}>
          <AlertDialogHeader>
            <AlertDialogTitle>🥲 已达到今日更新上限</AlertDialogTitle>
            <AlertDialogDescription>当前无法手动更新订阅内容，明天再来看看吧...</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setUpdateLimitDialogOpen(false)}>确认</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
