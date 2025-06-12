"use client"

import { useState } from "react"
import VideoCard from "./video-card"
import ContentDetailModal from "./content-detail-modal"
import type { ContentCardItem } from "@/types/content"

const placeholderItems: ContentCardItem[] = Array(12)
  .fill(null)
  .map((_, i) => ({
    content_id: i + 1,
    title:
      i % 3 === 0
        ? "这是一个非常非常长的文章标题，用来测试多行显示效果和省略号是否正常工作"
        : i === 1
          ? "关于AI视频生成技术Veo 3的深度分析和行业思考"
          : `RSS 文章标题 ${i + 1}`,
    cover_image: i % 4 === 0 ? null : `/placeholder.svg?width=400&height=225&query=abstract+${i}`,
    media_items:
      i % 4 === 0
        ? [
            {
              url: `/placeholder.svg?width=400&height=225&query=media+${i}`,
              type: "image" as const,
              description: `Media item ${i}`,
            },
          ]
        : [],
    platform: ["bilibili", "weibo", "github", "rss"][i % 4],
    author: i % 3 === 0 ? null : `作者${String.fromCharCode(65 + (i % 5))}`,
    feed_title: `订阅源 ${String.fromCharCode(65 + (i % 5))}`,
    published_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    duration: i % 4 === 0 ? Math.floor(Math.random() * 3600) + 60 : null,
    content_type: (["video", "image_text", "text"] as const)[i % 3],
  }))

export default function VideoGrid() {
  const [selectedContentId, setSelectedContentId] = useState<number | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [hasContent] = useState(true) // 模拟是否有内容，可以改为false测试兜底样式

  const handleCardClick = (contentId: number) => {
    setSelectedContentId(contentId)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
  }

  // 如果没有内容，显示兜底样式
  if (!hasContent || placeholderItems.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">当前没有获取到任何订阅内容🤡</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-8">
        {placeholderItems.map((item) => (
          <VideoCard key={item.content_id} item={item} onClick={handleCardClick} />
        ))}
      </div>

      <ContentDetailModal isOpen={isModalOpen} onClose={handleCloseModal} contentId={selectedContentId} />
    </>
  )
}
