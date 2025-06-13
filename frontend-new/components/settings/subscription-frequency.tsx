"use client"

import { useState, useEffect } from "react"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useToast } from "@/hooks/use-toast"
import { 
  fetchConfigService, 
  formatUtils, 
  type FetchConfig, 
  type UpdateConfigRequest 
} from "@/lib/services/fetchConfigService"

export default function SubscriptionFrequency() {
  // 状态管理
  const [autoSubscribe, setAutoSubscribe] = useState(false)
  const [frequency, setFrequency] = useState<'daily' | 'three_days' | 'weekly'>("daily")
  const [subscribeTime, setSubscribeTime] = useState("09:00")
  const [isAlertOpen, setIsAlertOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isPageLoading, setIsPageLoading] = useState(true)
  const [pendingAction, setPendingAction] = useState<"enable" | "disable" | null>(null)
  
  const { toast } = useToast()

  const timeOptions = Array.from({ length: 24 }, (_, i) => {
    const hour = i.toString().padStart(2, "0")
    return `${hour}:00`
  })

  // 页面初始化：加载用户配置
  useEffect(() => {
    loadUserConfig()
  }, [])

  /**
   * 加载用户配置
   */
  const loadUserConfig = async () => {
    try {
      setIsPageLoading(true)
      const config = await fetchConfigService.getUserConfig()
      
      // 设置表单初始值
      setAutoSubscribe(config.auto_fetch_enabled)
      setFrequency(config.frequency)
      setSubscribeTime(formatUtils.hourToTimeString(config.preferred_hour))
      
    } catch (error) {
      console.error('获取配置失败:', error)
      toast({
        title: "❓获取失败，请刷新页面",
        description: "无法加载当前配置"
      })
    } finally {
      setIsPageLoading(false)
    }
  }

  /**
   * 统一的配置更新函数
   * @param config 要更新的配置
   * @param successMessage 成功时显示的Toast消息
   */
  const updateConfig = async (config: UpdateConfigRequest, successMessage: string) => {
    try {
      setIsLoading(true)
      
      // 调用API更新配置
      const updatedConfig = await fetchConfigService.updateUserConfig(config)
      
      // 更新本地状态
      setAutoSubscribe(updatedConfig.auto_fetch_enabled)
      setFrequency(updatedConfig.frequency)
      setSubscribeTime(formatUtils.hourToTimeString(updatedConfig.preferred_hour))
      
      // 显示成功Toast
      toast({
        title: successMessage,
        description: "配置已更新"
      })
      
    } catch (error) {
      console.error('更新配置失败:', error)
      toast({
        title: "❌设置更新失败",
        description: "请稍后重试"
      })
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * 保存频率和时间配置
   */
  const handleSaveChanges = async () => {
    const config: UpdateConfigRequest = {
      auto_fetch_enabled: autoSubscribe,
      frequency: frequency,
      preferred_hour: formatUtils.timeStringToHour(subscribeTime)
    }
    
    await updateConfig(config, "✅设置更新成功")
  }

  /**
   * 开关状态变更处理
   */
  const handleSwitchChange = (checked: boolean) => {
    if (checked) {
      setPendingAction("enable")
      setIsAlertOpen(true)
    } else {
      setPendingAction("disable")
      setIsAlertOpen(true)
    }
  }

  /**
   * 确认开关操作
   */
  const handleConfirmAction = async () => {
    const isEnabling = pendingAction === "enable"
    
    const config: UpdateConfigRequest = {
      auto_fetch_enabled: isEnabling,
      frequency: frequency,
      preferred_hour: formatUtils.timeStringToHour(subscribeTime)
    }
    
    const successMessage = isEnabling 
      ? "🎉自动订阅已开启" 
      : "🤫自动订阅已关闭"
    
    await updateConfig(config, successMessage)
    
    // 关闭弹窗
    setIsAlertOpen(false)
    setPendingAction(null)
  }

  /**
   * 取消弹窗操作
   */
  const handleCancelAction = () => {
    setIsAlertOpen(false)
    setPendingAction(null)
  }

  // 页面加载状态
  if (isPageLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="text-muted-foreground">加载配置中...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>订阅频率设置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between space-x-2 p-4 border rounded-lg">
            <Label htmlFor="auto-subscribe-switch" className="flex flex-col space-y-1">
              <span>自动订阅</span>
              <span className="font-normal leading-snug text-muted-foreground">
                开启后，系统将按以下设置自动获取更新。
              </span>
            </Label>
            <Switch 
              id="auto-subscribe-switch" 
              checked={autoSubscribe} 
              onCheckedChange={handleSwitchChange}
              disabled={isLoading}
            />
          </div>

          {autoSubscribe && (
            <>
              <div className="space-y-2">
                <Label htmlFor="frequency-select">订阅频率</Label>
                <Select 
                  value={frequency} 
                  onValueChange={(value: 'daily' | 'three_days' | 'weekly') => setFrequency(value)}
                  disabled={isLoading}
                >
                  <SelectTrigger id="frequency-select">
                    <SelectValue placeholder="选择频率" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">每天</SelectItem>
                    <SelectItem value="three_days">每3天</SelectItem>
                    <SelectItem value="weekly">每7天</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="time-select">订阅时间 (UTC+8)</Label>
                <Select 
                  value={subscribeTime} 
                  onValueChange={setSubscribeTime}
                  disabled={isLoading}
                >
                  <SelectTrigger id="time-select">
                    <SelectValue placeholder="选择时间" />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {timeOptions.map((time) => (
                      <SelectItem key={time} value={time}>
                        {time}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">系统将在你选择的北京时间整点进行订阅更新。</p>
              </div>
            </>
          )}
        </CardContent>
        {autoSubscribe && (
          <CardFooter>
            <Button 
              onClick={handleSaveChanges}
              disabled={isLoading}
            >
              {isLoading ? "保存中..." : "保存更改"}
            </Button>
          </CardFooter>
        )}
      </Card>

      <AlertDialog open={isAlertOpen} onOpenChange={() => {}}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingAction === "enable" ? "🚀 确认打开自动订阅？" : "⚠️ 确认关闭自动订阅？"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction === "enable"
                ? "打开后，系统将按照你的配置自动获取更新。"
                : "关闭后，系统将不再自动获取更新。你需要手动刷新才能看到最新内容。"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelAction}>
              取消
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmAction} disabled={isLoading}>
              {isLoading ? "处理中..." : "确认"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
