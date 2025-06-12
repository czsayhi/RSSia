"use client"

import Image from "next/image"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import type { ContentCardItem } from "@/types/content"
import {
  getContentCoverImage,
  getPlatformLogo,
  formatRelativeTime,
  formatDuration,
  getAuthorName,
} from "@/lib/content-utils"

interface VideoCardProps {
  item: ContentCardItem
  onClick: (id: number) => void
}

export default function VideoCard({ item, onClick }: VideoCardProps) {
  const coverImage = getContentCoverImage(item.cover_image, item.media_items)
  const platformLogo = getPlatformLogo(item.platform)
  const authorName = getAuthorName(item.author, item.feed_title)
  const relativeTime = formatRelativeTime(item.published_at)

  return (
    <div className="group cursor-pointer" onClick={() => onClick(item.content_id)}>
      <div className="flex flex-col gap-2">
        <div className="relative aspect-video rounded-xl overflow-hidden">
          <Image
            src={coverImage || "/placeholder.svg"}
            alt={item.title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          {item.duration && (
            <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
              {formatDuration(item.duration)}
            </span>
          )}
        </div>
        <div className="flex gap-3 items-start">
          <Avatar className="h-9 w-9 mt-0.5">
            {platformLogo ? (
              <AvatarImage src={platformLogo || "/placeholder.svg"} alt={item.platform} />
            ) : (
              <AvatarFallback>{item.platform.charAt(0).toUpperCase()}</AvatarFallback>
            )}
          </Avatar>
          <div className="flex-1">
            <h3 className="text-base font-medium leading-snug line-clamp-2 group-hover:text-primary transition-colors duration-200">
              {item.title}
            </h3>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1 group-hover:text-foreground/80 transition-colors duration-200">
              <span>{authorName}</span>
              <span className="text-xs">{relativeTime}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
