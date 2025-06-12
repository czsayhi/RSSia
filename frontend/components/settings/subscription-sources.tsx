"use client"

import { useState } from "react"
import SourceSearchInput, { type SearchResult } from "./source-search-input"
import SourceConfigForm, { type FormFieldSchema } from "./source-config-form"
import SubscriptionList, { type SubscriptionItem } from "./subscription-list"
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

// 注意：这里的搜索结果是mock数据，实际应该由后端提供
const mockSearchResults: SearchResult[] = [
  {
    id: "bilibili_user_videos",
    display_name: "哔哩哔哩 - UP主视频订阅",
    description: "订阅B站UP主的最新视频投稿，及时获取更新通知",
    icon: "/icons/bilibili.svg",
    platform: "bilibili",
  },
  {
    id: "weibo_keyword_search",
    display_name: "微博 - 关键词搜索",
    description: "搜索包含特定关键词的微博内容，追踪热门话题",
    icon: "/icons/weibo.svg",
    platform: "weibo",
  },
]

// Mock data for form schema (as provided by user for Bilibili UID)
const mockBilibiliFormSchema: FormFieldSchema[] = [
  {
    name: "uid",
    display_name: "UP主UID",
    description: "B站UP主的用户ID，可在个人主页URL中找到",
    type: "string",
    required: true,
    placeholder: "297572288",
    validation_regex: "^[0-9]+$",
    validation_message: "请输入纯数字的用户ID",
  },
]

// Mock data for existing subscriptions
const mockInitialSubscriptions: SubscriptionItem[] = [
  {
    id: "sub1",
    source_id: "bilibili_user_videos",
    display_name: "哔哩哔哩 - UP主视频订阅",
    identifier: "297572288",
    icon: "/icons/bilibili.svg",
    platform: "bilibili",
    status: "open",
    create_time: "2025-01-15 15:30",
  },
]

export default function SubscriptionSources() {
  const [selectedSource, setSelectedSource] = useState<SearchResult | null>(null)
  const [formSchema, setFormSchema] = useState<FormFieldSchema[] | null>(null)
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>(mockInitialSubscriptions)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [subscriptionToDelete, setSubscriptionToDelete] = useState<string | null>(null)

  const handleSearchSelect = (source: SearchResult) => {
    setSelectedSource(source)
    // 注意：实际应该调用后端API获取对应的表单schema
    if (source.id === "bilibili_user_videos") {
      setFormSchema(mockBilibiliFormSchema)
    } else {
      // Placeholder for other schemas
      setFormSchema([
        {
          name: "query",
          display_name: "关键词",
          description: "请输入要搜索的关键词",
          type: "string",
          required: true,
          placeholder: "例如：人工智能",
        },
      ])
    }
  }

  const handleFormSubmit = (formData: Record<string, string>) => {
    console.log("Form submitted:", formData, "for source:", selectedSource)
    if (!selectedSource) return

    // 模拟添加到列表
    const newSubscription: SubscriptionItem = {
      id: `sub${Date.now()}`,
      source_id: selectedSource.id,
      display_name: selectedSource.display_name,
      identifier: formData.uid || formData.query || "N/A",
      icon: selectedSource.icon,
      platform: selectedSource.platform,
      status: "open",
      create_time: new Date().toLocaleString(),
    }
    setSubscriptions((prev) => [...prev, newSubscription])

    // 模拟成功：关闭表单
    setSelectedSource(null)
    setFormSchema(null)
    alert("订阅添加成功！") // Replace with toast later
  }

  const handleFormCancel = () => {
    setSelectedSource(null)
    setFormSchema(null)
  }

  const handleDeleteSubscription = (id: string) => {
    setSubscriptionToDelete(id)
    setDeleteDialogOpen(true)
  }

  const confirmDeleteSubscription = () => {
    if (subscriptionToDelete) {
      // 模拟后端删除
      setSubscriptions((prev) => prev.filter((sub) => sub.id !== subscriptionToDelete))
      console.log(`Subscription ${subscriptionToDelete} deleted`)
    }
    setDeleteDialogOpen(false)
    setSubscriptionToDelete(null)
  }

  const handleStatusChange = (id: string, newStatus: boolean) => {
    setSubscriptions((prev) =>
      prev.map((sub) => (sub.id === id ? { ...sub, status: newStatus ? "open" : "closed" } : sub)),
    )
    // 模拟后端更新
    console.log(`Subscription ${id} status changed to ${newStatus ? "open" : "closed"}`)
  }

  return (
    <>
      <div className="space-y-8">
        <div className="text-center pt-8 pb-4">
          <h2 className="text-3xl font-bold tracking-tight">👀 搜索订阅源</h2>
        </div>
        <SourceSearchInput onSelect={handleSearchSelect} mockResults={mockSearchResults} />
        {selectedSource && formSchema && (
          <SourceConfigForm
            key={selectedSource.id}
            sourceName={selectedSource.display_name}
            schema={formSchema}
            onSubmit={handleFormSubmit}
            onCancel={handleFormCancel}
          />
        )}
        <SubscriptionList
          subscriptions={subscriptions}
          onDelete={handleDeleteSubscription}
          onStatusChange={handleStatusChange}
        />
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>⚠️ 确认删除该订阅源？</AlertDialogTitle>
            <AlertDialogDescription>删除后，系统将不再获取该订阅源内容。</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteSubscription}>确认</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
