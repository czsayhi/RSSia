"use client"

import Image from "next/image"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { type SubscriptionItem } from "@/lib/api-client"

interface SubscriptionListProps {
  subscriptions: SubscriptionItem[]
  onDelete: (id: string) => void
  onStatusChange: (id: string, newStatus: boolean) => void
}

export default function SubscriptionList({ subscriptions, onDelete, onStatusChange }: SubscriptionListProps) {
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
                      src={sub.icon || "/placeholder.svg"}
                      alt={sub.platform}
                      width={24}
                      height={24}
                      className="h-6 w-6"
                    />
                    <span className="font-medium">{sub.display_name}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="font-mono">
                    {sub.identifier}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Switch
                    checked={sub.status === "open"}
                    onCheckedChange={(checked) => onStatusChange(sub.id, checked)}
                    aria-label="订阅状态开关"
                  />
                </TableCell>
                <TableCell>{sub.create_time}</TableCell>
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
    </div>
  )
}
