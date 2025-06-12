"use client"

import { useState } from "react"
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

export default function SubscriptionFrequency() {
  const [autoSubscribe, setAutoSubscribe] = useState(true)
  const [frequency, setFrequency] = useState("daily") // daily, three_days, weekly
  const [subscribeTime, setSubscribeTime] = useState("09:00") // HH:MM format
  const [isAlertOpen, setIsAlertOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [pendingAction, setPendingAction] = useState<"enable" | "disable" | null>(null)

  const timeOptions = Array.from({ length: 24 }, (_, i) => {
    const hour = i.toString().padStart(2, "0")
    return `${hour}:00`
  })

  const handleSaveChanges = () => {
    // Simulate saving changes
    console.log("Saving frequency settings:", { autoSubscribe, frequency, subscribeTime })
    alert("订阅频率设置已保存！") // Replace with toast
  }

  const handleSwitchChange = (checked: boolean) => {
    if (checked) {
      // 如果用户是打开自动订阅
      setPendingAction("enable")
      setIsAlertOpen(true)
    } else {
      // 如果用户是关闭自动订阅
      setPendingAction("disable")
      setIsAlertOpen(true)
    }
  }

  const handleConfirmAction = async () => {
    setIsLoading(true)
    try {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 1000))

      if (pendingAction === "enable") {
        setAutoSubscribe(true)
        console.log("Enabling auto-subscribe")
      } else if (pendingAction === "disable") {
        setAutoSubscribe(false)
        console.log("Disabling auto-subscribe")
      }
    } catch (error) {
      console.error("Failed to update auto-subscribe setting:", error)
    } finally {
      setIsLoading(false)
      setIsAlertOpen(false)
      setPendingAction(null)
    }
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
            <Switch id="auto-subscribe-switch" checked={autoSubscribe} onCheckedChange={handleSwitchChange} />
          </div>

          {autoSubscribe && (
            <>
              <div className="space-y-2">
                <Label htmlFor="frequency-select">订阅频率</Label>
                <Select value={frequency} onValueChange={setFrequency}>
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
                <Select value={subscribeTime} onValueChange={setSubscribeTime}>
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
            <Button onClick={handleSaveChanges}>保存更改</Button>
          </CardFooter>
        )}
      </Card>

      <AlertDialog open={isAlertOpen} onOpenChange={() => {}}>
        <AlertDialogContent onPointerDownOutside={(e) => e.preventDefault()}>
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
            <AlertDialogCancel
              onClick={() => {
                setIsAlertOpen(false)
                setPendingAction(null)
              }}
            >
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
