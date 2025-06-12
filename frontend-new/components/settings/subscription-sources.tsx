"use client"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
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
import {
  getUserSubscriptions,
  createSubscription,
  deleteSubscription,
  updateSubscriptionStatus,
  searchSubscriptionSources,
  type SubscriptionTemplate,
  type SubscriptionCreateRequest
} from "@/lib/api"

export default function SubscriptionSources() {
  const { toast } = useToast()
  const [selectedSource, setSelectedSource] = useState<SubscriptionTemplate | null>(null)
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([])
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [subscriptionToDelete, setSubscriptionToDelete] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchResults, setSearchResults] = useState<SubscriptionTemplate[]>([])

  // 加载用户订阅列表
  const loadSubscriptions = async () => {
    try {
      setLoading(true)
      const response = await getUserSubscriptions()
      setSubscriptions(response.subscriptions)
    } catch (error) {
      console.error('加载订阅列表失败:', error)
      toast({
        title: "加载失败",
        description: error instanceof Error ? error.message : "无法加载订阅列表",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // 组件挂载时加载数据
  useEffect(() => {
    loadSubscriptions()
  }, [])

  // 处理搜索
  const handleSearch = async (query: string): Promise<SearchResult[]> => {
    try {
      const templates = await searchSubscriptionSources(query)
      setSearchResults(templates)
      
      // 转换为SearchResult格式
      return templates.map(template => ({
        id: template.template_id,
        display_name: template.template_name,
        description: template.description,
        icon: `/icons/${template.platform}.svg`, // 前端根据平台生成图标路径
        platform: template.platform,
      }))
    } catch (error) {
      console.error('搜索失败:', error)
      toast({
        title: "搜索失败",
        description: error instanceof Error ? error.message : "搜索订阅源时出错",
        variant: "destructive",
      })
      return []
    }
  }

  const handleSearchSelect = (source: SearchResult) => {
    // 从搜索结果中找到对应的模板
    const template = searchResults.find(t => t.template_id === source.id)
    if (template) {
      setSelectedSource(template)
    }
  }

  const handleFormSubmit = async (formData: Record<string, string>) => {
    if (!selectedSource) return

    try {
      const request: SubscriptionCreateRequest = {
        template_id: selectedSource.template_id,
        parameters: formData,
        custom_name: formData.custom_name, // 如果表单包含自定义名称
      }

      const newSubscription = await createSubscription(request)
      
      // 更新本地状态
      setSubscriptions(prev => [...prev, newSubscription])
      
      // 关闭表单
      setSelectedSource(null)
      
      toast({
        title: "订阅成功",
        description: `已成功添加订阅：${newSubscription.custom_name || newSubscription.template_name}`,
      })
    } catch (error) {
      console.error('创建订阅失败:', error)
      toast({
        title: "订阅失败",
        description: error instanceof Error ? error.message : "创建订阅时出错",
        variant: "destructive",
      })
    }
  }

  const handleFormCancel = () => {
    setSelectedSource(null)
  }

  const handleDeleteSubscription = (id: number) => {
    setSubscriptionToDelete(id)
    setDeleteDialogOpen(true)
  }

  const confirmDeleteSubscription = async () => {
    if (subscriptionToDelete === null) return

    try {
      await deleteSubscription(subscriptionToDelete)
      
      // 更新本地状态
      setSubscriptions(prev => prev.filter(sub => sub.id !== subscriptionToDelete))
      
      toast({
        title: "删除成功",
        description: "订阅已成功删除",
      })
    } catch (error) {
      console.error('删除订阅失败:', error)
      toast({
        title: "删除失败",
        description: error instanceof Error ? error.message : "删除订阅时出错",
        variant: "destructive",
      })
    } finally {
      setDeleteDialogOpen(false)
      setSubscriptionToDelete(null)
    }
  }

  const handleStatusChange = async (id: number, newStatus: boolean) => {
    try {
      await updateSubscriptionStatus(id, newStatus)
      
      // 更新本地状态
      setSubscriptions(prev =>
        prev.map(sub => sub.id === id ? { ...sub, is_active: newStatus } : sub)
      )
      
      toast({
        title: newStatus ? "订阅已开启" : "订阅已关闭",
        description: newStatus ? "将接收该订阅源的更新" : "不再接收该订阅源的更新",
      })
    } catch (error) {
      console.error('更新订阅状态失败:', error)
      toast({
        title: "更新失败",
        description: error instanceof Error ? error.message : "更新订阅状态时出错",
        variant: "destructive",
      })
    }
  }

  // 将SubscriptionTemplate转换为FormFieldSchema
  const getFormSchema = (template: SubscriptionTemplate): FormFieldSchema[] => {
    return template.parameters.map(param => ({
      name: param.name,
      display_name: param.display_name,
      description: param.description,
      type: param.type as "string" | "number" | "boolean", // 类型断言
      required: param.required,
      placeholder: param.placeholder,
      validation_regex: param.validation_regex,
      validation_message: param.validation_message,
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载订阅列表中...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-8">
        <div className="text-center pt-8 pb-4">
          <h2 className="text-3xl font-bold tracking-tight">👀 搜索订阅源</h2>
        </div>
        <SourceSearchInput onSelect={handleSearchSelect} onSearch={handleSearch} />
        {selectedSource && (
          <SourceConfigForm
            key={selectedSource.template_id}
            sourceName={selectedSource.template_name}
            schema={getFormSchema(selectedSource)}
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
