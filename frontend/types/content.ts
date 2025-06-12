// 媒体项类型定义
export interface MediaItem {
  url: string
  type: "video" | "image" | "audio"
  description?: string
  duration?: number // 秒数
}

// 内容详情类型定义
export interface ContentDetail {
  content_id: number
  subscription_id: number
  title: string
  link: string
  summary: string
  description: string // HTML内容
  published_at: string
  fetched_at: string
  is_favorited: boolean
  tags: string[]
  platform: string
  source_name: string
  author: string | null // 作者信息，可能为null
  feed_title: string // 订阅源标题，作为author的备选
  cover_image: string | null // 可能为null
  media_items: MediaItem[]
  content_type: "video" | "image_text" | "text"
  duration?: number | null // 内容时长，可能为null
}

// 相关内容类型定义
export interface RelatedContent {
  content_id: number
  title: string
  cover_image: string | null
  content_type: "video" | "image_text" | "text"
  published_at: string
  duration: number | null // 秒数
  author: string | null
  feed_title: string
  platform: string
}

// 订阅信息类型定义
export interface SubscriptionInfo {
  subscription_id: number
  name: string
  platform: string
  description: string
  total_contents: number
}

// 完整数据类型定义
export interface ContentDetailData {
  content: ContentDetail
  related_contents: RelatedContent[]
  subscription_info: SubscriptionInfo
}

// 主页卡片展示用的简化类型
export interface ContentCardItem {
  content_id: number
  title: string
  cover_image: string | null
  media_items: MediaItem[]
  platform: string
  author: string | null
  feed_title: string
  published_at: string
  duration: number | null
  content_type: "video" | "image_text" | "text"
}
