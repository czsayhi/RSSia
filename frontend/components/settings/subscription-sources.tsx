"use client"

import { useState, useEffect } from "react"
import SourceSearchInput from "./source-search-input"
import SourceConfigForm, { type FormFieldSchema } from "./source-config-form"
import SubscriptionList from "./subscription-list"
import { 
  type SearchResult, 
  type SubscriptionItem, 
  type CreateSubscriptionRequest,
  getUserSubscriptions,
  createSubscription,
  deleteSubscription,
  updateSubscriptionStatus
} from "@/lib/api-client"
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

// 注意：搜索结果现在由 source-search-input 组件从后端API获取

// 表单Schema现在由搜索结果直接提供，无需mock数据

// 订阅列表数据现在由后端API提供

export default function SubscriptionSources() {
  const [selectedSource, setSelectedSource] = useState<SearchResult | null>(null)
  const [formSchema, setFormSchema] = useState<FormFieldSchema[] | null>(null)
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([])
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [subscriptionToDelete, setSubscriptionToDelete] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // 组件加载时获取订阅列表
  useEffect(() => {
    loadSubscriptions()
  }, [])

  const loadSubscriptions = async () => {
    try {
      setIsLoading(true)
      const userSubscriptions = await getUserSubscriptions()
      setSubscriptions(userSubscriptions)
    } catch (error) {
      console.error('获取订阅列表失败:', error)
      // 保持空数组，显示"暂无订阅"状态
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearchSelect = (source: SearchResult) => {
    setSelectedSource(source)
    
    // 直接使用搜索结果中的表单配置 (符合业务预期：统一从后端获取)
    setFormSchema(source.formSchema)
  }

  const handleFormSubmit = async (formData: Record<string, string>) => {
    if (!selectedSource) return

    try {
      setIsLoading(true)
      
      // 调用后端API创建订阅
      const createRequest: CreateSubscriptionRequest = {
        template_id: selectedSource.id,
        user_params: formData
      }
      
      const newSubscription = await createSubscription(createRequest)
      
      // 更新本地状态
      setSubscriptions((prev) => [...prev, newSubscription])
      
      // 关闭表单
      setSelectedSource(null)
      setFormSchema(null)
      
      alert("订阅添加成功！") // TODO: 替换为toast
    } catch (error) {
      console.error('创建订阅失败:', error)
      alert("订阅添加失败，请重试") // TODO: 替换为toast
    } finally {
      setIsLoading(false)
    }
  }

  const handleFormCancel = () => {
    setSelectedSource(null)
    setFormSchema(null)
  }

  const handleDeleteSubscription = (id: string) => {
    setSubscriptionToDelete(id)
    setDeleteDialogOpen(true)
  }

  const confirmDeleteSubscription = async () => {
    if (!subscriptionToDelete) return

    try {
      setIsLoading(true)
      
      // 调用后端API删除订阅
      await deleteSubscription(subscriptionToDelete)
      
      // 更新本地状态
      setSubscriptions((prev) => prev.filter((sub) => sub.id !== subscriptionToDelete))
    } catch (error) {
      console.error('删除订阅失败:', error)
      alert("删除失败，请重试") // TODO: 替换为toast
    } finally {
      setIsLoading(false)
      setDeleteDialogOpen(false)
      setSubscriptionToDelete(null)
    }
  }

  const handleStatusChange = async (id: string, newStatus: boolean) => {
    try {
      setIsLoading(true)
      
      // 调用后端API更新状态
      const updatedSubscription = await updateSubscriptionStatus(id, {
        status: newStatus ? "active" : "inactive"
      })
      
      // 更新本地状态
      setSubscriptions((prev) =>
        prev.map((sub) => (sub.id === id ? updatedSubscription : sub))
      )
    } catch (error) {
      console.error('更新订阅状态失败:', error)
      alert("状态更新失败，请重试") // TODO: 替换为toast
      
      // 恢复原状态（因为开关已经变化了）
      // 这里可以选择重新加载列表或手动恢复
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <div className="space-y-8">
        <div className="text-center pt-8 pb-4">
          <h2 className="text-3xl font-bold tracking-tight">👀 搜索订阅源</h2>
        </div>
        <SourceSearchInput onSelect={handleSearchSelect} />
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
            <AlertDialogAction onClick={confirmDeleteSubscription}>确定删除</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
