"use client"

import Image from "next/image"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
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
import { useState } from "react"
import { getPlatformLogo } from "@/lib/content-utils"

export interface SubscriptionItem {
  id: number // 后端: id (INTEGER)
  template_id: string // 后端: template_id (STRING) 
  template_name: string // 后端: template_name (STRING)
  target_user_id: string // 后端: target_user_id (STRING)
  platform: string // 后端: platform (STRING)
  is_active: boolean // 后端: is_active (BOOLEAN)
  created_at: string // 后端: created_at (TIMESTAMP)
  custom_name?: string // 后端: custom_name (可选)
  rss_url: string // 后端: rss_url (STRING)
}

interface SubscriptionListProps {
  subscriptions: SubscriptionItem[]
  onDelete: (id: number) => void
  onStatusChange: (id: number, newStatus: boolean) => void
}

export default function SubscriptionList({ subscriptions, onDelete, onStatusChange }: SubscriptionListProps) {
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<{
    id: number
    action: "subscribe" | "unsubscribe"
  } | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSwitchChange = (id: number, checked: boolean) => {
    setPendingAction({
      id,
      action: checked ? "subscribe" : "unsubscribe",
    })
    setConfirmDialogOpen(true)
  }

  const handleConfirmAction = async () => {
    if (!pendingAction) return

    setIsLoading(true)
    try {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 1000))
      onStatusChange(pendingAction.id, pendingAction.action === "subscribe")
      console.log(`${pendingAction.action} action completed for ${pendingAction.id}`)
    } catch (error) {
      console.error("Failed to update subscription:", error)
    } finally {
      setIsLoading(false)
      setConfirmDialogOpen(false)
      setPendingAction(null)
    }
  }

  if (subscriptions.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8 border-2 border-dashed rounded-lg mt-8">
        <p>暂无已配置的订阅源。</p>
        <p className="text-sm">请通过上方的搜索框添加新的订阅。</p>
      </div>
    )
  }

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">已配置的订阅</h3>
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>名称</TableHead>
              <TableHead>标识</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>添加时间</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {subscriptions.map((sub) => (
              <TableRow key={sub.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Image
                      src={getPlatformLogo(sub.platform) || "/placeholder.svg"}
                      alt={sub.platform}
                      width={24}
                      height={24}
                      className="h-6 w-6"
                    />
                    <span className="font-medium">{sub.custom_name || sub.template_name}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="font-mono">
                    {sub.target_user_id}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Switch
                    checked={sub.is_active}
                    onCheckedChange={(checked) => handleSwitchChange(sub.id, checked)}
                    aria-label="订阅状态开关"
                  />
                </TableCell>
                <TableCell>{new Date(sub.created_at).toLocaleString()}</TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(sub.id)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <AlertDialog open={confirmDialogOpen} onOpenChange={() => {}}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingAction?.action === "subscribe" ? "🚀 确认订阅？" : "⚠️ 确认取消订阅？"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction?.action === "subscribe"
                ? "订阅后，你将收到该订阅源的更新内容。"
                : "取消订阅后，你将不再收到该订阅源的更新内容。"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setConfirmDialogOpen(false)
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
    </div>
  )
}
