"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import Image from "next/image"
import Link from "next/link"
import { format } from "date-fns"
import { X, ExternalLink, Play, Pause, Volume2, VolumeX, Maximize, ChevronLeft, ChevronRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
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
import type { ContentDetailData, MediaItem } from "@/types/content"
import {
  getContentCoverImage,
  getPlatformLogo,
  formatRelativeTime,
  formatDuration,
  getAuthorName,
} from "@/lib/content-utils"
import TextPlaceholder from "./content/text-placeholder"

interface ContentDetailModalProps {
  isOpen: boolean
  onClose: () => void
  contentId: number | null
}

// 模拟获取内容详情的函数
const fetchContentDetail = async (contentId: number): Promise<ContentDetailData> => {
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 300))

  // 视频内容示例
  const videoContent = {
    content: {
      content_id: 1,
      subscription_id: 1,
      title: "【幻兽帕鲁】佐伊塔主暴揍佐伊塔主",
      link: "https://www.bilibili.com/video/BV1eu4m1N7cL",
      summary:
        "这是一个关于幻兽帕鲁游戏的视频，展示了佐伊塔主的游戏过程和技巧分享。视频内容包括游戏机制介绍、战斗技巧演示和娱乐解说。",
      description: "<div><p>详细的HTML内容...</p><p>这里是更多的内容描述</p></div>",
      published_at: "2024-02-08T14:16:54Z",
      fetched_at: "2025-06-11T21:41:30.123456",
      is_favorited: false,
      tags: ["游戏", "幻兽帕鲁", "攻略"],
      platform: "bilibili",
      source_name: "DIYgod的B站视频",
      author: "DIYgod",
      feed_title: "DIYgod的B站视频",
      cover_image: "/placeholder.svg?width=800&height=450",
      media_items: [
        {
          url: "https://www.bilibili.com/video/BV1eu4m1N7cL",
          type: "video",
          description: "幻兽帕鲁游戏视频 - 佐伊塔主攻略",
          duration: 628, // 10:28
        },
      ],
      content_type: "video",
      duration: 628,
    },
    related_contents: [
      {
        content_id: 3,
        title: "【技术分享】如何构建现代化的RSS订阅器",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "video",
        published_at: "2024-02-06T10:30:00Z",
        duration: 1280,
        author: "技术博主",
        feed_title: "技术分享频道",
        platform: "bilibili",
      },
      {
        content_id: 4,
        title: "开源项目RSSHub使用指南",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "image_text",
        published_at: "2024-02-04T15:20:00Z",
        duration: null,
        author: null,
        feed_title: "开源项目分享",
        platform: "github",
      },
      {
        content_id: 5,
        title: "前端开发最佳实践分享",
        cover_image: null,
        content_type: "text",
        published_at: "2024-02-02T09:15:00Z",
        duration: null,
        author: "前端开发者",
        feed_title: "前端技术博客",
        platform: "weibo",
      },
      {
        content_id: 6,
        title: "JavaScript异步编程深度解析",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "video",
        published_at: "2024-01-30T16:45:00Z",
        duration: 2145,
        author: "JS专家",
        feed_title: "JavaScript学习",
        platform: "bilibili",
      },
      {
        content_id: 7,
        title: "React 18新特性详解与实战应用",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "video",
        published_at: "2024-01-28T11:20:00Z",
        duration: 1890,
        author: "React专家",
        feed_title: "React技术分享",
        platform: "bilibili",
      },
      {
        content_id: 8,
        title: "TypeScript高级类型系统深入解析",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "text",
        published_at: "2024-01-25T09:30:00Z",
        duration: null,
        author: "TS专家",
        feed_title: "TypeScript学习",
        platform: "github",
      },
    ],
    subscription_info: {
      subscription_id: 1,
      name: "DIYgod的B站视频",
      platform: "bilibili",
      description: "关注DIYgod的技术分享和开源项目",
      total_contents: 15,
    },
  }

  // 图文内容示例
  const imageTextContent = {
    content: {
      content_id: 15,
      subscription_id: 2,
      title: "春日樱花盛开🌸 | 东京上野公园赏樱攻略分享",
      link: "https://weibo.com/1234567890/SpringSakura2025",
      summary: "分享东京上野公园的樱花盛开美景，包含最佳赏樱时间、拍照机位推荐和周边美食介绍。多图预警！",
      description:
        "<div><p>🌸 春日限定 | 东京上野公园樱花季终于来啦！</p><p>📍 地点：上野恩赐公园<br/>🕐 最佳时间：早上8-10点，人少光线好<br/>📷 推荐机位：不忍池畔、樱花大道</p><p>这次用了新买的相机，效果真的很棒！分享几张满意的照片～</p><p>樱花真的太美了，虽然花期很短，但每一刻都值得珍藏 💕</p><p>#樱花季 #东京旅行 #摄影分享</p></div>",
      published_at: "2025-03-28T09:15:22Z",
      fetched_at: "2025-06-11T22:10:15.123456",
      is_favorited: true,
      tags: ["旅行", "摄影", "樱花", "东京", "生活方式"],
      platform: "weibo",
      source_name: "旅行摄影师小梅",
      author: "旅行摄影师小梅",
      feed_title: "旅行摄影师小梅",
      cover_image: "/placeholder.svg?width=800&height=450",
      media_items: [
        {
          url: "/placeholder.svg?width=800&height=450",
          type: "image",
          description: "上野公园樱花大道全景 - 主图",
        },
        {
          url: "/placeholder.svg?width=800&height=450",
          type: "image",
          description: "樱花特写 - 粉色花瓣细节",
        },
        {
          url: "/placeholder.svg?width=800&height=450",
          type: "image",
          description: "不忍池樱花倒影",
        },
        {
          url: "/placeholder.svg?width=800&height=450",
          type: "image",
          description: "游客赏樱野餐场景",
        },
        {
          url: "/placeholder.svg?width=800&height=450",
          type: "image",
          description: "夜间樱花灯光秀",
        },
        {
          url: "/placeholder.svg?width=800&height=450",
          type: "image",
          description: "樱花主题便当和茶点",
        },
      ],
      content_type: "image_text",
      duration: null,
    },
    related_contents: [
      {
        content_id: 16,
        title: "【VLOG】京都赏樱三日游完整记录",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "video",
        published_at: "2025-03-25T14:30:00Z",
        duration: 1820,
        author: "旅行博主",
        feed_title: "京都旅行记录",
        platform: "bilibili",
      },
      {
        content_id: 17,
        title: "日本春季旅行穿搭指南 | 樱花季怎么拍更美",
        cover_image: "/placeholder.svg?width=400&height=225",
        content_type: "image_text",
        published_at: "2025-03-22T11:20:00Z",
        duration: null,
        author: null,
        feed_title: "时尚穿搭分享",
        platform: "weibo",
      },
    ],
    subscription_info: {
      subscription_id: 2,
      name: "旅行摄影师小梅",
      platform: "weibo",
      description: "专注旅行摄影和生活美学分享，记录世界各地的美好瞬间",
      total_contents: 128,
    },
  }

  // 纯文本内容示例
  const textContent = {
    content: {
      content_id: 1001,
      subscription_id: 25,
      title: "关于AI视频生成技术Veo 3的深度分析和行业思考",
      link: "https://weibo.com/1560906700/PvLKXnIbl",
      summary:
        "分析了AI视频生成技术Veo 3对社交媒体平台的冲击，以及业界对AI技术发展速度的不同观点。作者从技术发展、市场反应和行业趋势多个角度进行了深度思考。",
      description:
        '上个月月底，Veo 3的发布再次让海外社交媒体炸了锅，大量AI视频如病毒般迅速铺满了各大平台，这次受伤的不只有老面孔Ins，连TikTok也未能幸免。这中间还不乏有反AI派和技术保守派的声音，认为这种技术的发展速度已经超出了人类的控制范围...<br><br><a href="https://mp.weixin.qq.com/s/-XOJEo0yizKAhvDNIzGz4A" target="_blank">阅读全文：温和、务实的「炸裂派AI」</a>',
      published_at: "2025-06-12T08:30:15Z",
      fetched_at: "2025-06-12T08:35:22Z",
      is_favorited: false,
      tags: ["AI", "技术分析", "社交媒体", "Veo3"],
      platform: "weibo",
      source_name: "阑夕的微博",
      author: "阑夕",
      feed_title: "阑夕的微博",
      cover_image: null,
      media_items: [],
      content_type: "text",
      duration: null,
    },
    related_contents: [
      {
        content_id: 1002,
        title: "人工智能发展的三个阶段与未来趋势预测",
        cover_image: null,
        content_type: "text",
        published_at: "2025-06-10T14:20:00Z",
        duration: null,
        author: "AI研究员",
        feed_title: "AI技术前沿",
        platform: "weibo",
      },
    ],
    subscription_info: {
      subscription_id: 25,
      name: "阑夕的微博",
      platform: "weibo",
      description: "互联网视频博主，知名科技自媒体。",
      total_contents: 45,
    },
  }

  // 根据contentId返回不同的内容
  if (contentId === 15) {
    return imageTextContent
  } else if (contentId === 1001) {
    return textContent
  } else {
    return videoContent
  }
}

// 格式化日期函数
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return format(date, "yyyy-MM-dd HH:mm:ss")
  } catch (error) {
    return dateString
  }
}

// 视频播放器组件
const VideoPlayer = ({ mediaItem, coverImage }: { mediaItem: MediaItem; coverImage: string }) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(mediaItem.duration || 0)
  const videoRef = useRef<HTMLVideoElement>(null)

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(Math.floor(videoRef.current.currentTime))
      if (videoRef.current.duration) {
        setDuration(Math.floor(videoRef.current.duration))
      }
    }
  }

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current && duration > 0) {
      const progressBar = e.currentTarget
      const clickPosition = e.clientX - progressBar.getBoundingClientRect().left
      const progressBarWidth = progressBar.clientWidth
      const clickPercentage = (clickPosition / progressBarWidth) * 100
      const newTime = (duration * clickPercentage) / 100
      videoRef.current.currentTime = newTime
      setCurrentTime(Math.floor(newTime))
    }
  }

  const handleFullScreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen()
      }
    }
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
      {!isPlaying && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Image src={coverImage || "/placeholder.svg"} alt="Video thumbnail" fill className="object-cover" />
          <div className="absolute inset-0 bg-black/30" />
        </div>
      )}

      <video
        ref={videoRef}
        src={mediaItem.url}
        className="w-full h-full"
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => setIsPlaying(false)}
        onLoadedMetadata={() => {
          if (videoRef.current?.duration) {
            setDuration(Math.floor(videoRef.current.duration))
          }
        }}
      />

      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
        {/* 时长显示 */}
        <div className="text-white text-sm mb-2">
          {formatDuration(currentTime)} / {formatDuration(duration)}
        </div>

        {/* 进度条 */}
        <div className="w-full h-1 bg-gray-600 rounded-full mb-3 cursor-pointer" onClick={handleProgressClick}>
          <div className="h-full bg-red-500 rounded-full" style={{ width: `${progress}%` }} />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="text-white hover:text-gray-200 transition-colors"
              aria-label={isPlaying ? "暂停" : "播放"}
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>

            <button
              onClick={toggleMute}
              className="text-white hover:text-gray-200 transition-colors"
              aria-label={isMuted ? "取消静音" : "静音"}
            >
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
          </div>

          <button
            onClick={handleFullScreen}
            className="text-white hover:text-gray-200 transition-colors"
            aria-label="全屏"
          >
            <Maximize size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}

// 图片查看器组件
const ImageGallery = ({ mediaItems }: { mediaItems: MediaItem[] }) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const imageItems = mediaItems.filter((item) => item.type === "image")

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? imageItems.length - 1 : prev - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === imageItems.length - 1 ? 0 : prev + 1))
  }

  if (imageItems.length === 0) return null

  return (
    <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
      <div className="relative w-full h-full">
        <Image
          src={imageItems[currentIndex]?.url || "/placeholder.svg"}
          alt={imageItems[currentIndex]?.description || `Image ${currentIndex + 1}`}
          fill
          className="object-contain"
        />
      </div>

      {imageItems.length > 1 && (
        <>
          <button
            onClick={goToPrevious}
            className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
            aria-label="上一张"
          >
            <ChevronLeft size={20} />
          </button>

          <button
            onClick={goToNext}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
            aria-label="下一张"
          >
            <ChevronRight size={20} />
          </button>

          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-black/70 text-white text-xs px-2 py-1 rounded-full">
            {currentIndex + 1} / {imageItems.length}
          </div>
        </>
      )}
    </div>
  )
}

// AI摘要气泡组件
const AISummaryBubble = ({ isOpen, onClose, summary }: { isOpen: boolean; onClose: () => void; summary: string }) => {
  if (!isOpen) return null

  return (
    <div className="absolute right-0 bottom-full mb-2 w-[300px] z-10">
      <Card className="relative bg-card/95 backdrop-blur-sm text-card-foreground shadow-lg border overflow-hidden">
        <div className="flex items-center justify-between p-3 border-b">
          <h2 className="text-sm font-bold">💡 AI摘要</h2>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-6 w-6">
            <X className="h-3 w-3" />
          </Button>
        </div>
        <div className="p-3 overflow-y-auto max-h-[200px]">
          <p className="text-xs text-foreground whitespace-pre-wrap leading-relaxed">{summary}</p>
        </div>
      </Card>
    </div>
  )
}

// 模拟订阅状态管理
const useSubscriptionStatus = (subscriptionId: number) => {
  const [isSubscribed, setIsSubscribed] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  const toggleSubscription = async (): Promise<boolean> => {
    setIsLoading(true)
    try {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setIsSubscribed(!isSubscribed)
      return true
    } catch (error) {
      console.error("Failed to toggle subscription:", error)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  return { isSubscribed, isLoading, toggleSubscription }
}

export default function ContentDetailModal({ isOpen, onClose, contentId }: ContentDetailModalProps) {
  const [data, setData] = useState<ContentDetailData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [unsubscribeDialogOpen, setUnsubscribeDialogOpen] = useState(false)
  const [aiSummaryOpen, setAiSummaryOpen] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [showAllRelated, setShowAllRelated] = useState(false)

  const {
    isSubscribed,
    isLoading: subscriptionLoading,
    toggleSubscription,
  } = useSubscriptionStatus(data?.subscription_info.subscription_id || 0)

  // 获取内容详情
  const loadContent = async (id: number) => {
    setIsTransitioning(true)
    setError(null)

    try {
      const newData = await fetchContentDetail(id)
      setData(newData)
    } catch (err) {
      console.error("Failed to fetch content detail:", err)
      setError("获取内容详情失败")
    } finally {
      setIsTransitioning(false)
    }
  }

  useEffect(() => {
    if (isOpen && contentId) {
      loadContent(contentId)
    } else {
      setData(null)
      setShowAllRelated(false)
    }
  }, [isOpen, contentId])

  // 禁用背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
    }

    return () => {
      document.body.style.overflow = ""
    }
  }, [isOpen])

  // ESC键关闭
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !unsubscribeDialogOpen && !aiSummaryOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscKey)
    }

    return () => {
      document.removeEventListener("keydown", handleEscKey)
    }
  }, [isOpen, onClose, unsubscribeDialogOpen, aiSummaryOpen])

  const handleSubscriptionToggle = async () => {
    const success = await toggleSubscription()
    if (success) {
      setUnsubscribeDialogOpen(false)
      // 可以添加成功提示
    } else {
      // 可以添加错误提示
    }
  }

  const handleRelatedContentClick = (relatedContentId: number) => {
    if (relatedContentId === contentId) return
    loadContent(relatedContentId)
  }

  if (!isOpen) return null

  return (
    <>
      {/* 全屏背景遮罩 */}
      <div className="fixed inset-0 z-50 bg-background" onClick={onClose} />

      {/* 全屏弹窗内容容器 */}
      <div className="fixed inset-0 z-50 bg-background">
        {/* 关闭按钮 */}
        <div className="absolute top-4 right-4 z-10">
          <Button variant="ghost" size="icon" onClick={onClose} className="h-10 w-10 bg-transparent hover:bg-muted">
            <X className="h-6 w-6" />
          </Button>
        </div>

        {loading || isTransitioning ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full text-destructive">
            <p>{error}</p>
            <Button onClick={onClose} className="mt-4">
              关闭
            </Button>
          </div>
        ) : data ? (
          <div className="flex flex-col md:flex-row h-full overflow-hidden">
            {/* 左侧内容区域 */}
            <div className="flex-1 overflow-y-auto p-6 md:max-w-[65%]">
              {/* 标题和元信息 */}
              <div className="mb-6">
                <div className="flex items-start justify-between gap-4">
                  <h1 className="text-2xl font-bold leading-tight flex-1">{data.content.title}</h1>
                  <Link
                    href={data.content.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground flex-shrink-0"
                  >
                    <ExternalLink className="h-5 w-5" />
                  </Link>
                </div>

                <div className="flex items-center text-sm text-muted-foreground mt-2">
                  <span>{formatDate(data.content.published_at)}</span>
                  <span className="mx-2">{getAuthorName(data.content.author, data.content.feed_title)}</span>
                </div>

                <div className="flex flex-wrap gap-2 mt-3">
                  {data.content.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* 媒体内容区域 */}
              <div className="mb-6">
                {data.content.content_type === "video" && data.content.media_items.length > 0 && (
                  <VideoPlayer
                    mediaItem={data.content.media_items.find((item) => item.type === "video")!}
                    coverImage={getContentCoverImage(data.content.cover_image, data.content.media_items)}
                  />
                )}

                {data.content.content_type === "image_text" && data.content.media_items.length > 0 && (
                  <ImageGallery mediaItems={data.content.media_items} />
                )}

                {data.content.content_type === "text" && (
                  <div className="w-full aspect-video bg-muted/30 rounded-lg flex items-center justify-center border-2 border-dashed border-muted-foreground/20">
                    <div className="text-center text-muted-foreground">
                      <div className="text-4xl mb-2">📄</div>
                      <p className="text-sm">纯文本内容</p>
                    </div>
                  </div>
                )}
              </div>

              {/* AI摘要按钮 - 单独一行，右对齐 */}
              <div className="mb-6 relative">
                <div className="flex justify-end">
                  <div className="relative">
                    <Button
                      variant="outline"
                      onClick={() => setAiSummaryOpen(!aiSummaryOpen)}
                      className="bg-foreground text-background hover:bg-foreground/90 border-foreground hover:text-background"
                    >
                      💡 AI摘要
                    </Button>
                    <AISummaryBubble
                      isOpen={aiSummaryOpen}
                      onClose={() => setAiSummaryOpen(false)}
                      summary={data.content.summary}
                    />
                  </div>
                </div>
              </div>

              {/* 富文本内容 */}
              <div className="mb-6">
                <TextPlaceholder content={data.content.description} />
              </div>
            </div>

            {/* 右侧信息区域 */}
            <div className="md:w-[35%] border-t md:border-t-0 md:border-l border-border overflow-y-auto bg-muted/20">
              <div className="p-6">
                {/* 订阅源信息 */}
                <div className="mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center overflow-hidden flex-shrink-0">
                      {getPlatformLogo(data.content.platform) ? (
                        <Image
                          src={getPlatformLogo(data.content.platform)! || "/placeholder.svg"}
                          alt={data.subscription_info.name}
                          width={48}
                          height={48}
                          className="object-cover"
                        />
                      ) : (
                        <span className="text-lg font-bold">{data.subscription_info.name.charAt(0).toUpperCase()}</span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0 flex items-center">
                      <h2 className="font-semibold truncate">{data.subscription_info.name}</h2>
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground mb-4">{data.subscription_info.description}</p>

                  <div className="flex gap-3">
                    <Button variant="outline" className="flex-1 h-10" asChild>
                      <Link href={data.content.link} target="_blank" rel="noopener noreferrer">
                        前往订阅源
                      </Link>
                    </Button>
                    <Button
                      className={`flex-1 h-10 ${
                        isSubscribed
                          ? "bg-white text-black dark:bg-black dark:text-white hover:bg-gray-100 dark:hover:bg-gray-900 border border-input"
                          : "bg-foreground text-background hover:bg-foreground/90"
                      }`}
                      onClick={() => setUnsubscribeDialogOpen(true)}
                      disabled={subscriptionLoading}
                    >
                      {isSubscribed ? "取消订阅" : "订阅"}
                    </Button>
                  </div>
                </div>

                <Separator className="my-6" />

                {/* 相关内容 */}
                <div>
                  <h2 className="font-semibold mb-4">相关内容</h2>
                  <div className="space-y-4">
                    {data.related_contents.slice(0, showAllRelated ? undefined : 4).map((item) => (
                      <Card key={item.content_id} className="overflow-hidden bg-card/50 backdrop-blur-sm">
                        <button
                          onClick={() => handleRelatedContentClick(item.content_id)}
                          className="block w-full text-left group"
                        >
                          <div className="relative aspect-video">
                            {item.cover_image ? (
                              <Image
                                src={item.cover_image || "/placeholder.svg"}
                                alt={item.title}
                                fill
                                className="object-cover transition-transform duration-300 group-hover:scale-105"
                              />
                            ) : (
                              <div className="w-full h-full bg-muted flex items-center justify-center">
                                <span className="text-muted-foreground">无封面</span>
                              </div>
                            )}
                            {item.duration && (
                              <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                                {formatDuration(item.duration)}
                              </div>
                            )}
                          </div>
                          <div className="p-3">
                            <h3 className="font-medium line-clamp-2 group-hover:text-primary transition-colors duration-200">
                              {item.title}
                            </h3>
                            <div className="text-xs text-muted-foreground mt-1">
                              <span>{formatRelativeTime(item.published_at)}</span>
                            </div>
                          </div>
                        </button>
                      </Card>
                    ))}
                  </div>

                  {data.related_contents.length > 4 && (
                    <div className="mt-4 text-center">
                      <Button variant="ghost" onClick={() => setShowAllRelated(!showAllRelated)}>
                        {showAllRelated ? "收起" : `查看更多 (${data.related_contents.length - 4})`}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* 取消订阅确认对话框 */}
      <AlertDialog open={unsubscribeDialogOpen} onOpenChange={() => setUnsubscribeDialogOpen(false)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{isSubscribed ? "⚠️ 确认取消订阅？" : "🚀 确认订阅？"}</AlertDialogTitle>
            <AlertDialogDescription>
              {isSubscribed ? "取消订阅后，你将不再收到该订阅源的更新内容。" : "订阅后，你将收到该订阅源的更新内容。"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setUnsubscribeDialogOpen(false)}>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleSubscriptionToggle} disabled={subscriptionLoading}>
              {subscriptionLoading ? "处理中..." : "确认"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
